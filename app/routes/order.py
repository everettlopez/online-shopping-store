from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Security, Response
from sqlmodel import Session, select
from app.db.session import get_session
from datetime import datetime
from app.auth.core import CurrentUser
from app.schemas.order import OrderLookup, OrderRead, OrderItemRead, OrderTrackingLink, RefundRequest
from app.models.order import Order, OrderItem
from decimal import Decimal
import logging
import secrets
import stripe

from app.models.product import Product
from app.database.products import database_get_product_reads
from app.auth.dependencies import admin_required
from app.models.user import User
from app.mail import build_refund_email, build_shipping_notice_email, send_email
from app.money import to_cents, to_decimal
from app.rate_limit import rate_limit
from app.alerts import alert_admin


router = APIRouter(prefix="/orders", tags=["Orders"])

logger = logging.getLogger(__name__)

ORDER_STATUSES = {"pending", "placed", "processing", "shipped", "delivered", "completed", "cancelled", "refunded"}
# Set only by a refund (the Refund button or Stripe's Dashboard), never by hand
REFUND_ONLY_STATUSES = {"refunded"}


def restock_order_items(session: Session, order: Order):
    """Put the order's items back in stock, once per order."""
    if order.restocked_at:
        return
    for item in session.exec(select(OrderItem).where(OrderItem.order_id == order.order_id)).all():
        product = session.exec(select(Product).where(Product.product_id == item.product_id).with_for_update()).first()
        if product:
            product.stock_quantity += item.quantity
            session.add(product)
    order.restocked_at = datetime.utcnow()
    session.add(order)


def record_refund(session: Session, order: Order, refunded_total: Decimal, restock: bool):
    """Record what Stripe has refunded on the order in total. The first time that
    reaches the order's total, the order becomes refunded (and restocked if asked)."""
    order.refunded_amount = refunded_total
    order.updated_at = datetime.utcnow()
    if refunded_total >= order.total_amount and order.status != "refunded":
        order.status = "refunded"
        order.refunded_at = datetime.utcnow()
        if restock:
            restock_order_items(session, order)
    session.add(order)


def was_paid(order: Order) -> bool:
    """Whether money may have changed hands. Orders whose payment never went through
    (pending, or cancelled after a failed payment) are the only ones safe to delete."""
    return order.payment_status == "succeeded" or order.refunded_amount > 0 or order.status not in {"pending", "cancelled"}


def build_order_reads(session: Session, orders) -> list[OrderRead]:
    # Load every order's items and their products up front instead of per item
    all_items = session.exec(
        select(OrderItem).where(OrderItem.order_id.in_([o.order_id for o in orders]))
    ).all() if orders else []
    products = database_get_product_reads(session, {i.product_id for i in all_items})

    enriched_orders = []

    for order in orders:
        enriched_items = [
            OrderItemRead(
                order_item_id=item.order_item_id,
                order_id=item.order_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                subtotal=item.subtotal,
                product=products.get(item.product_id)
            )
            for item in all_items if item.order_id == order.order_id
        ]

        # model_dump() includes the addresses as they were when the order was placed
        enriched_orders.append(OrderRead(**order.model_dump(), items=enriched_items))

    return enriched_orders

@router.get("/", response_model=list[OrderRead], dependencies=[Depends(admin_required)])
def list_orders(session: Session = Depends(get_session)):
    orders = session.exec(select(Order)).all()
    return build_order_reads(session, orders)

@router.get("/me", response_model=list[OrderRead])
def list_my_orders(user: CurrentUser, order_status: str | None = None, session: Session = Depends(get_session)):

    query = select(Order).where(Order.user_id == user.user_id)

    if order_status:
        query = query.where(Order.status == order_status)

    orders = session.exec(query).all()
    return build_order_reads(session, orders)

def same_secret(expected: str, given: str) -> bool:
    """Constant-time comparison. On bytes, because compare_digest raises on non-ASCII strings"""
    return secrets.compare_digest(expected.encode(), given.encode())

@router.get("/track/{order_number}", response_model=OrderRead, dependencies=[rate_limit("lookup")])
def track_order(order_number: str, token: str = "", session: Session = Depends(get_session)):
    """The order behind an emailed tracking link, with no login needed (guests have no
    account). The token is a long random secret kept on the order"""
    order = session.exec(select(Order).where(Order.order_number == order_number.lower())).first()

    if not order or not order.access_token or not same_secret(order.access_token, token):
        raise HTTPException(status_code=404, detail="Order not found")

    return build_order_reads(session, [order])[0]

@router.post("/lookup", response_model=OrderTrackingLink, dependencies=[rate_limit("lookup")])
def look_up_order(data: OrderLookup, session: Session = Depends(get_session)):
    """Find the tracking link for an order from its number and the email it was placed
    with. Either one being wrong gives the same 404, so neither can be probed alone"""
    order = session.exec(select(Order).where(Order.order_number == data.order_number.strip().lower())).first()

    email = data.email.strip().lower()
    if not order or not order.email or not order.access_token or not same_secret(order.email.lower(), email):
        raise HTTPException(status_code=404, detail="We couldn't find an order with that number and email")

    return OrderTrackingLink(order_number=order.order_number, access_token=order.access_token)

@router.get("/{order_number}", response_model=OrderRead)
def get_order(order_number: str, user: CurrentUser, session: Session = Depends(get_session)):
    order = session.exec(select(Order).where(Order.order_number == order_number.lower())).first()

    # Only the buyer (or an admin) can see the order; 404 so order numbers can't be probed
    if not order or (order.user_id != user.user_id and not user.is_admin):
        raise HTTPException(status_code=404, detail="Order not found")

    return build_order_reads(session, [order])[0]

@router.put("/{order_id}/status", dependencies=[Depends(admin_required)])
def update_order_status(order_id: int, status: str, session: Session = Depends(get_session)):
    if status not in ORDER_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid order status '{status}'")
    if status in REFUND_ONLY_STATUSES:
        raise HTTPException(status_code=400, detail="Use Refund to refund an order; it returns the money through Stripe")

    order = session.get(Order, order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = status
    order.updated_at = datetime.now()
    session.add(order)
    session.commit()
    session.refresh(order)

    return {"message": "Order status updated"}

@router.put("/{order_id}/tracking", dependencies=[Depends(admin_required)])
def update_tracking_information(order_id: int, tracking_number: str, tracking_carrier: str, tracking_url: str, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):

    # The link goes into emails and the order pages, so only a web address will do
    # (one typed without https:// gets it, as the order pages always assumed)
    tracking_url = tracking_url.strip()
    if tracking_url and "://" not in tracking_url:
        tracking_url = f"https://{tracking_url}"
    if tracking_url and not tracking_url.lower().startswith(("https://", "http://")):
        raise HTTPException(status_code=400, detail="The tracking link must be a web address starting with https://")

    order = session.get(Order, order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.tracking_number=tracking_number
    order.tracking_carrier=tracking_carrier
    order.tracking_url=tracking_url

    order.status = "shipped"
    order.updated_at = datetime.now()

    session.add(order)
    session.commit()
    session.refresh(order)

    # Tell the buyer, including when an admin corrects the tracking details
    if order.email:
        background_tasks.add_task(send_email, build_shipping_notice_email(order.email, order))

    return {"message": "Order tracking updated"}

@router.post("/{order_id}/refund", response_model=OrderRead, dependencies=[Depends(admin_required)])
def refund_order(order_id: int, data: RefundRequest, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    """Refund some or all of an order through Stripe. Stripe's charge.refunded webhook
    for it then finds the amount already recorded, so nothing is counted twice."""
    # Locked until the refund is recorded, so the webhook can't record it at the same time
    order = session.exec(select(Order).where(Order.order_id == order_id).with_for_update()).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not order.payment_intent_id or order.status == "pending" or not was_paid(order):
        raise HTTPException(status_code=400, detail="This order hasn't been paid, so there's nothing to refund")

    remaining = order.total_amount - order.refunded_amount
    if remaining <= 0:
        raise HTTPException(status_code=400, detail="This order has already been refunded in full")

    amount = remaining if data.amount is None else to_decimal(data.amount)
    if amount > remaining:
        raise HTTPException(status_code=400, detail=f"At most ${remaining:,.2f} is left to refund on this order")

    try:
        stripe.Refund.create(
            payment_intent=order.payment_intent_id,
            amount=to_cents(amount),
            metadata={"order_id": order.order_id},
            # A retried click refunds once; a later refund of the same amount is a new one
            idempotency_key=f"refund-{order.order_id}-{to_cents(order.refunded_amount)}-{to_cents(amount)}",
        )
    except stripe.StripeError as e:
        logger.error("refund failed order_id=%s error=%s", order.order_id, e)
        alert_admin("refund-stripe-error", "A refund failed", [
            f"Stripe refused a refund for order {order.order_number} (id {order.order_id}).",
            f"Stripe said: {e}",
            "Check the payment in the Stripe Dashboard, then try again.",
        ])   # sent now: background tasks don't run after an error response
        message = getattr(e, "user_message", None) or "Stripe couldn't make the refund. Please try again in a moment."
        raise HTTPException(status_code=502, detail=message)

    record_refund(session, order, order.refunded_amount + amount, data.restock)
    session.commit()
    session.refresh(order)

    if order.email:
        background_tasks.add_task(send_email, build_refund_email(order.email, order, amount))

    return build_order_reads(session, [order])[0]

@router.delete("/{order_id}", dependencies=[Depends(admin_required)])
def delete_order(order_id: int, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Paid orders are financial records; cancel or refund them instead
    if was_paid(order):
        raise HTTPException(status_code=409, detail="Paid orders can't be deleted. Cancel or refund the order instead.")

    # Unpaid orders still hold their stock (unless a failed payment already returned it)
    restock_order_items(session, order)

    for item in session.exec(select(OrderItem).where(OrderItem.order_id == order.order_id)).all():
        session.delete(item)
    session.flush()

    session.delete(order)
    session.commit()

    return {"message": "Order deleted and stock restored"}



# ---------------------------------------------------------
# GET /orders/{order_id}/items → list all items in an order
# ---------------------------------------------------------
@router.get("/{order_id}/items", response_model=list[OrderItemRead])
def list_order_items(order_id: int, user: CurrentUser, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)

    if not order or order.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="Order not found")

    statement = select(OrderItem).where(OrderItem.order_id == order_id)
    return session.exec(statement).all()


# -------------------------------------------------------------------
# GET /orders/{order_id}/items/{item_id} → get a single order item
# -------------------------------------------------------------------
@router.get("/{order_id}/items/{item_id}", response_model=OrderItemRead)
def get_order_item(order_id: int, item_id: int, user: CurrentUser, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)

    if not order or order.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="Order not found")

    item = session.get(OrderItem, item_id)

    if not item or item.order_id != order_id:
        raise HTTPException(status_code=404, detail="Order item not found")

    return item
