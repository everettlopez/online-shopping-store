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
        metadata={
            "user_id": user.user_id,
            "shipping_address_id": data.shipping_address_id,
            "billing_address_id": data.billing_address_id
        }
    )

    return {"clientSecret": intent.client_secret}
