from datetime import datetime
from pydantic import BaseModel
from typing import List
from app.schemas.product import ProductRead

class CartItemRead(BaseModel):
    cart_item_id: int
    product_id: int
    quantity: int
    product: ProductRead | None = None

    class Config:
        from_attributes = True

class CartRead(BaseModel):
    cart_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    items: List[CartItemRead] = []

    class Config:
        from_attributes = True
