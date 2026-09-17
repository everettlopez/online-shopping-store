from pydantic import BaseModel
from datetime import datetime
from typing import List
from app.schemas.product import ProductRead
from app.schemas.address import AddressRead

class OrderItemRead(BaseModel):
    order_item_id: int
    order_id: int
    product: ProductRead | None = None
    quantity: int

    class Config:
        from_attributes = True


class OrderRead(BaseModel):
    order_id: int
    user_id: int

    first_name: str
    last_name: str
    order_number: str
    status: str
    created_at: datetime
    updated_at: datetime
    order_date: datetime
    total_amount: float

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

    shipping_address: AddressRead
    billing_address: AddressRead
    items: List[OrderItemRead] = []

    class Config:
        from_attributes = True
