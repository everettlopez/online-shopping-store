from pydantic import BaseModel, Field
from datetime import datetime
from typing import List
from app.schemas.product import ProductRead
from app.schemas.address import OrderAddress

class OrderItemRead(BaseModel):
    order_item_id: int
    order_id: int
    product: ProductRead | None = None
    quantity: int
    # What was paid, which stays the same when the product's price changes later
    unit_price: float
    subtotal: float

    class Config:
        from_attributes = True


class OrderRead(BaseModel):
    order_id: int
    user_id: int | None = None   # None for guest orders

    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    order_number: str
    status: str
    created_at: datetime
    updated_at: datetime
    order_date: datetime
    total_amount: float
    subtotal_amount: float | None = None
    shipping_amount: float | None = None
    tax_amount: float | None = None
    refunded_amount: float = 0
    refunded_at: datetime | None = None

    payment_intent_id: str | None = None
    stripe_session_id: str | None = None

    payment_method_type: str | None = None
    card_brand: str | None = None
    card_last4: str | None = None
    payment_status: str | None = None
    receipt_url: str | None = None

    tracking_number: str | None = None
    tracking_carrier: str | None = None
    tracking_url: str | None = None

    # As they were when the order was placed
    shipping_address: OrderAddress | None = None
    billing_address: OrderAddress | None = None
    items: List[OrderItemRead] = []

    class Config:
        from_attributes = True


class CheckoutOrderRead(OrderRead):
    """The order on the checkout success page, with the secret for its tracking link.
    Other order responses leave the token out."""
    access_token: str | None = None


class RefundRequest(BaseModel):
    # None refunds whatever hasn't been refunded yet
    amount: float | None = Field(default=None, gt=0)
    # Put the items back in stock; only a full refund restocks
    restock: bool = True


class OrderLookup(BaseModel):
    order_number: str = Field(min_length=1, max_length=50)
    email: str = Field(min_length=1, max_length=255)


class OrderTrackingLink(BaseModel):
    order_number: str
    access_token: str
