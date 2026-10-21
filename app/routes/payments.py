from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select
import stripe
import uuid
import json
import os
from datetime import datetime

from app.db.session import get_session
from app.schemas.checkout import CheckoutRequest
from app.auth.core import CurrentUser
from app.models.order import Order, OrderItem
from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.models.address import Address
from app.models.user import User

router = APIRouter(prefix="/payments", tags=["Payments"])

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

@router.post("/create-payment-intent")
def create_payment_intent(
    data: CheckoutRequest,
    user: CurrentUser,
    session: Session = Depends(get_session)
):
    intent = stripe.PaymentIntent.create(
        amount=int(data.total_amount * 100),
        currency="usd",
        payment_method_types=["card"],
        metadata={
            "user_id": user.user_id,
            "shipping_address_id": data.shipping_address_id,
            "billing_address_id": data.billing_address_id
        }
    )

    return {"clientSecret": intent.client_secret}

@router.post("/create-checkout-session")
def create_checkout_session(data: CheckoutRequest, user: CurrentUser, session: Session = Depends(get_session)):
    # 1. Load cart
    cart = session.exec(select(Cart).where(Cart.user_id == user.user_id)).first()
    if not cart:
        raise HTTPException(status_code=400, detail="Cart not found")

    cart_items = session.exec(select(CartItem).where(CartItem.cart_id == cart.cart_id)).all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # 2. Validate addresses
    shipping = session.get(Address, data.shipping_address_id)
    billing = session.get(Address, data.billing_address_id)

    if not shipping or shipping.user_id != user.user_id:
        raise HTTPException(status_code=400, detail="Invalid shipping address")

    if not billing or billing.user_id != user.user_id:
        raise HTTPException(status_code=400, detail="Invalid billing address")

    # 3. Validate stock BEFORE Stripe Checkout
    total_amount = 0

    for item in cart_items:
        product = session.get(Product, item.product_id)

        if not product:
            raise HTTPException(status_code=400, detail="Product not found")

        if product.stock_quantity < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough stock for {product.title}"
            )

        total_amount += product.price * item.quantity

    # 4. Create Stripe Checkout Session
    # Payment methods (card, etc.) are configured in the Stripe Dashboard
    stripe_session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": "Order Payment"
                },
                "unit_amount": int(total_amount * 100),
            },
            "quantity": 1,
        }],
        success_url="http://localhost:5173/order-success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="http://localhost:5173/cart",
        metadata={
            "user_id": user.user_id,
            "shipping_address_id": data.shipping_address_id,
            "billing_address_id": data.billing_address_id
        }
    )

    return {"checkoutUrl": stripe_session.url}


@router.get("/session/{session_id}")
def get_order_from_session(session_id: str, session: Session = Depends(get_session)):
    order = session.exec(
        select(Order).where(Order.stripe_session_id == session_id)
    ).first()

    # Webhook hasn't created the order yet (or never arrived): ask Stripe directly
    if not order:
        try:
            stripe_session = stripe.checkout.Session.retrieve(session_id)
        except Exception as e:
            print("Failed to load checkout session:", session_id, e)
            stripe_session = None

        if stripe_session and stripe_session.payment_status == "paid":
            order = fulfill_checkout(session, stripe_session)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Load addresses
    shipping = session.get(Address, order.shipping_address_id)
    billing = session.get(Address, order.billing_address_id)

    # Load items
    items = session.exec(
        select(OrderItem).where(OrderItem.order_id == order.order_id)
    ).all()

    # Load product for each item
    enriched_items = []
    for item in items:
        product = session.get(Product, item.product_id)
        enriched_items.append({
            **item.dict(),
            "product": product.dict() if product else None
        })

    return {
        **order.dict(),
        "shipping_address": shipping.dict() if shipping else None,
        "billing_address": billing.dict() if billing else None,
        "items": enriched_items
    }

def summarize_payment_method(pmd: dict) -> dict:
    """Turn a charge's payment_method_details into how the customer paid.
    Checkout offers several methods (card, Link, Klarna, Cash App, ...), and only
    card-backed ones have a brand/last4."""
    method = pmd.get("type")
    details = pmd.get(method) or {}

    # Card, or a card funding another method (e.g. Amazon Pay)
    card = details if "last4" in details else (details.get("funding") or {}).get("card") or {}

    # Wallets (Apple Pay, Google Pay, Link) charge a card; show the wallet the customer picked
    wallet = (details.get("wallet") or {}).get("type") if method == "card" else None

    return {
        "payment_method_type": wallet or method,
        "card_brand": card.get("brand"),
        "card_last4": card.get("last4")
    }


def get_payment_details(payment_intent_id: str) -> dict:
    """Read payment + receipt details straight from Stripe, so the order doesn't
    depend on separate charge.* webhook events arriving in the right order."""
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id, expand=["latest_charge"])
        charge = intent.latest_charge
        if not charge:
            return {}

        pmd = charge.payment_method_details.to_dict() if charge.payment_method_details else {}

        return {
            **summarize_payment_method(pmd),
            "payment_status": charge.status,
            "receipt_url": charge.receipt_url
        }
    except Exception as e:
        print("Failed to load payment details for:", payment_intent_id, e)
        return {}


@router.post("/webhook")
async def stripe_webhook(request: Request, session: Session = Depends(get_session)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except Exception as e:
        print("Webhook signature failed:", e)
        return {"received": True}

    if event["type"] == "checkout.session.completed":
        fulfill_checkout(session, event["data"]["object"])

    return {"received": True}


def fulfill_checkout(session: Session, stripe_session) -> Order | None:
    """Create the order for a completed Checkout Session. Called by the webhook and,
    as a fallback, by the success page, so it must be safe to run more than once."""

    # Stripe can deliver the same event more than once
    existing = session.exec(select(Order).where(Order.stripe_session_id == stripe_session.id)).first()
    if existing:
        return existing

    metadata = stripe_session.metadata.to_dict()

    user_id = int(metadata["user_id"])
    shipping_id = int(metadata["shipping_address_id"])
    billing_id = int(metadata["billing_address_id"])

    user_obj = session.exec(select(User).where(User.user_id == user_id)).first()

    if not user_obj:
        print("ERROR: User not found: ", user_id)
        return None

    cart = session.exec(select(Cart).where(Cart.user_id == user_id)).first()
    if not cart:
        return None

    cart_items = session.exec(select(CartItem).where(CartItem.cart_id == cart.cart_id)).all()
    if not cart_items:
        return None

    total_amount = sum(
        session.get(Product, item.product_id).price * item.quantity
        for item in cart_items
    )

    pi_id = stripe_session.payment_intent

    order = Order(
        user_id=user_id,
        first_name=user_obj.first_name,
        last_name=user_obj.last_name,
        shipping_address_id=shipping_id,
        billing_address_id=billing_id,
        total_amount=total_amount,
        order_number=str(uuid.uuid4())[:8],
        status="placed" if stripe_session.payment_status == "paid" else "pending",
        payment_intent_id=pi_id,
        stripe_session_id=stripe_session.id,
        **get_payment_details(pi_id)
    )

    session.add(order)
    session.commit()
    session.refresh(order)

    for item in cart_items:
        product = session.get(Product, item.product_id)
        session.add(OrderItem(
            order_id=order.order_id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=product.price,
            subtotal=product.price * item.quantity
        ))
        product.stock_quantity -= item.quantity
        session.add(product)

    for item in cart_items:
        session.delete(item)

    session.commit()

    session.refresh(order)

    print("Created order:", order.order_id, "status:", order.status)

    return order
