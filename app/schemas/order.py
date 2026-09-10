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
    order_number: str
    status: str
    created_at: datetime
    updated_at: datetime
    order_date: datetime
    total_amount: float
    shipping_address: AddressRead      
    billing_address: AddressRead
    items: List[OrderItemRead] = []

    class Config:
        from_attributes = True
