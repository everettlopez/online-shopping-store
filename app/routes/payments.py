from fastapi import APIRouter, Depends
from sqlmodel import Session
import stripe
import os

from app.db.session import get_session
from app.schemas.checkout import CheckoutRequest
from app.auth.core import CurrentUser

router = APIRouter(prefix="/payments", tags=["Payments"])

stripe.api_key = ""


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
def create_checkout_session(data: CheckoutRequest, user: CurrentUser):
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": "Order Payment"
                },
                "unit_amount": int(data.total_amount * 100),
            },
            "quantity": 1,
        }],
        success_url="http://localhost:5173/order-success",
        cancel_url="http://localhost:5173/payment-cancel",
        metadata={
            "user_id": user.user_id,
            "shipping_address_id": data.shipping_address_id,
            "billing_address_id": data.billing_address_id
        }
    )

    return {"checkoutUrl": session.url}
