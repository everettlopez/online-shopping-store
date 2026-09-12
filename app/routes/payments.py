from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
import stripe
import uuid
from sqlmodel import Session, select

from fastapi import APIRouter, Depends, Request
from sqlmodel import Session
import stripe
import json
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

stripe.api_key = ""
WEBHOOK_SECRET = ""

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
                detail=f"Not enough stock for {product.name}"
            )

        total_amount += product.price * item.quantity

    # 4. Create Stripe Checkout Session
    stripe_session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        expand=["payment_intent.charges"],
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
        cancel_url="http://localhost:5173/payment-cancel",
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

# Temporary in-memory store for payment details
PAYMENT_CACHE = {}

@router.post("/webhook")
async def stripe_webhook(request: Request, session: Session = Depends(get_session)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except Exception as e:
        print("Webhook signature failed:", e)
        return {"received": True}

    event_type = event["type"]

    # ---------------------------------------------------------
    # 1️⃣ charge.succeeded → store payment details temporarily
    # ---------------------------------------------------------
    if event_type == "charge.succeeded":
        charge = event["data"]["object"]
        pi_id = charge["payment_intent"]

        pm = charge["payment_method_details"]

        PAYMENT_CACHE[pi_id] = {
            "payment_method_type": pm["type"],
            "card_brand": pm["card"]["brand"],
            "card_last4": pm["card"]["last4"],
            "payment_status": charge["status"],
            "receipt_url": charge["receipt_url"]
        }

        print("Cached payment details for:", pi_id)
        return {"received": True}

    # ---------------------------------------------------------
    # 2️⃣ checkout.session.completed → create order + apply cached payment
    # ---------------------------------------------------------
    if event_type == "checkout.session.completed":
        stripe_session = event["data"]["object"]
        metadata = stripe_session.metadata.to_dict()

        user_id = int(metadata["user_id"])
        shipping_id = int(metadata["shipping_address_id"])
        billing_id = int(metadata["billing_address_id"])

        user_obj = session.exec(select(User).where(User.user_id == user_id)).first()

        if not user_obj:
            print("ERROR: User not found: ", user_id)
            return {"received": True}

        cart = session.exec(select(Cart).where(Cart.user_id == user_id)).first()
        if not cart:
            return {"received": True}

        cart_items = session.exec(select(CartItem).where(CartItem.cart_id == cart.cart_id)).all()
        if not cart_items:
            return {"received": True}

        total_amount = sum(
            session.get(Product, item.product_id).price * item.quantity
            for item in cart_items
        )

        order = Order(
            user_id=user_id,
            first_name=user_obj.first_name,
            last_name=user_obj.last_name,
            shipping_address_id=shipping_id,
            billing_address_id=billing_id,
            total_amount=total_amount,
            order_number=str(uuid.uuid4())[:8],
            status="pending",
            payment_intent_id=stripe_session.payment_intent,
            stripe_session_id=stripe_session.id
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

        session.commit()

        for item in cart_items:
            session.delete(item)
        session.commit()

        # ⭐ Apply cached payment details if available
        pi_id = stripe_session.payment_intent
        if pi_id in PAYMENT_CACHE:
            pd = PAYMENT_CACHE.pop(pi_id)

            order.payment_method_type = pd["payment_method_type"]
            order.card_brand = pd["card_brand"]
            order.card_last4 = pd["card_last4"]
            order.payment_status = pd["payment_status"]
            order.receipt_url = pd["receipt_url"]
            order.status = "paid"

            session.add(order)
            session.commit()

            print("Applied cached payment details to order:", order.order_id)

        return {"received": True}

    # ---------------------------------------------------------
    # 3️⃣ charge.updated → fallback: apply payment details if order exists
    # ---------------------------------------------------------
    if event_type == "charge.updated":
        charge = event["data"]["object"]
        pi_id = charge["payment_intent"]

        order = session.exec(
            select(Order).where(Order.payment_intent_id == pi_id)
        ).first()

        if order:
            pm = charge["payment_method_details"]

            order.payment_method_type = pm["type"]
            order.card_brand = pm["card"]["brand"]
            order.card_last4 = pm["card"]["last4"]
            order.payment_status = charge["status"]
            order.receipt_url = charge["receipt_url"]
            order.status = "paid"

            session.add(order)
            session.commit()

            print("Payment saved from charge.updated:", order.order_id)

        return {"received": True}

    return {"received": True}

