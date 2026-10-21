from fastapi import APIRouter, Depends, HTTPException, Security, Response
from sqlmodel import Session, select
from app.db.session import get_session
from app.models.user import User
from app.models.address import Address
from datetime import datetime
from app.auth.core import CurrentUser
from app.schemas.order import OrderRead, OrderItemRead
from app.schemas.order_item import OrderItemUpdate
from app.schemas.checkout import CheckoutRequest
from app.models.order import Order, OrderItem
from sqlalchemy.orm import selectinload
import uuid

from app.models.product import Product
from app.database.products import database_get_product_read, database_get_product_reads
from app.auth.dependencies import admin_required


router = APIRouter(prefix="/orders", tags=["Orders"])

ORDER_STATUSES = {"pending", "placed", "processing", "shipped", "delivered", "completed", "cancelled", "refunded"}


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
                product=products.get(item.product_id)
            )
            for item in all_items if item.order_id == order.order_id
        ]

        enriched_orders.append(OrderRead(
            **order.model_dump(),
            shipping_address=session.get(Address, order.shipping_address_id),
            billing_address=session.get(Address, order.billing_address_id),
            items=enriched_items
        ))

    return enriched_orders

@router.post("/", response_model=OrderRead)
def create_order(data: CheckoutRequest, user: CurrentUser, session: Session = Depends(get_session)):

    # Validate shipping address
    shipping = session.get(Address, data.shipping_address_id)
    if not shipping or shipping.user_id != user.user_id:
        raise HTTPException(status_code=400, detail="Invalid shipping address")
    
    # Validate billing address
    billing = session.get(Address, data.billing_address_id)
    if not billing or billing.user_id != user.user_id:
        raise HTTPException(status_code=400, detail="Invalid billing address")
    
    # Same lowercase format as checkout, so GET /orders/{order_number} can find it
    order_number = str(uuid.uuid4())[:8]

    order = Order(
        user_id=user.user_id,
        first_name=user.first_name,
        last_name=user.last_name,
        shipping_address_id=data.shipping_address_id,
        billing_address_id=data.billing_address_id,
        total_amount=data.total_amount,
        order_number=order_number,
        status="pending"
    )

    session.add(order)
    session.commit()
    session.refresh(order)

    return build_order_reads(session, [order])[0]

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

@router.get("/{order_number}", response_model=OrderRead)
def get_order(order_number: str, user: CurrentUser, session: Session = Depends(get_session)):
    order = session.exec(select(Order).where(Order.order_number == order_number.lower())).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    user_obj = session.get(User, order.user_id)
    shipping = session.get(Address, order.shipping_address_id)
    billing = session.get(Address, order.billing_address_id)

    order_items = session.exec(select(OrderItem).where(OrderItem.order_id == order.order_id)).all()

    enriched_items = []

    for oi in order_items:
        product = database_get_product_read(session, oi.product_id)

        enriched_items.append(OrderItemRead(
            order_item_id=oi.order_item_id,
            order_id=oi.order_id,
            product=product,
            quantity=oi.quantity
        ))

    return OrderRead(
        order_id=order.order_id,
        user_id=order.user_id,
        first_name=user_obj.first_name,
        last_name=user_obj.last_name,
        order_number=order.order_number,
        status=order.status,
        created_at=order.created_at,
        updated_at=order.updated_at,
        order_date=order.order_date,
        total_amount=order.total_amount,

        payment_intent_id=order.payment_intent_id,
        stripe_session_id=order.stripe_session_id,
        payment_method_type=order.payment_method_type,
        card_brand=order.card_brand,
        card_last4=order.card_last4,
        payment_status=order.payment_status,
        receipt_url=order.receipt_url,
        shipping_address=shipping,
        billing_address=billing,
        tracking_number=order.tracking_number,
        tracking_carrier=order.tracking_carrier,
        tracking_url=order.tracking_url,
        items=enriched_items
    )

@router.put("/{order_id}/status", dependencies=[Depends(admin_required)])
def update_order_status(order_id: int, status: str, session: Session = Depends(get_session)):
    if status not in ORDER_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid order status '{status}'")

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
def update_tracking_information(order_id: int, tracking_number: str, tracking_carrier: str, tracking_url: str, session: Session = Depends(get_session)):

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


    return {"message": "Order tracking updated"}

@router.delete("/{order_id}", dependencies=[Depends(admin_required)])
def delete_order(order_id: int, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # 1. Load order items
    order_items = session.exec(
        select(OrderItem).where(OrderItem.order_id == order.order_id)
    ).all()

    # 2. Restore product stock
    for item in order_items:
        product = session.get(Product, item.product_id)
        if product:
            product.stock_quantity += item.quantity
            session.add(product)

    # 3. Delete order items
    for item in order_items:
        session.delete(item)

    session.flush()

    # 4. Delete order
    session.delete(order)

    # 5. Commit
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


# -------------------------------------------------------------------
# PUT /orders/{order_id}/items/{item_id} → update quantity
# -------------------------------------------------------------------
@router.put("/{order_id}/items/{item_id}", response_model=OrderItemRead)
def update_order_item(order_id: int, item_id: int, data: OrderItemUpdate, user: CurrentUser, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)

    if not order or order.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="Order not found")

    item = session.get(OrderItem, item_id)

    if not item or item.order_id != order_id:
        raise HTTPException(status_code=404, detail="Order item not found")

    update_data = data.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(item, key, value)

    # Recalculate subtotal
    item.subtotal = item.unit_price * item.quantity

    session.add(item)
    session.commit()
    session.refresh(item)

    return item


# -------------------------------------------------------------------
# DELETE /orders/{order_id}/items/{item_id} → delete order item
# -------------------------------------------------------------------
@router.delete("/{order_id}/items/{item_id}")
def delete_order_item(order_id: int, item_id: int, user: CurrentUser, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)

    if not order or order.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="Order not found")

    item = session.get(OrderItem, item_id)

    if not item or item.order_id != order_id:
        raise HTTPException(status_code=404, detail="Order item not found")

    session.delete(item)
    session.commit()

    return {"message": "Order item deleted"}
