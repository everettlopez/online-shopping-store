from pydantic import BaseModel
from datetime import datetime


class ProductCreate(BaseModel):
    category_id: int
    name: str
    description: str | None = None
    price: float
    sku: str
    stock_quantity: int = 0
    is_active: bool = True

class ProductRead(BaseModel):
    product_id: int
    category_id: int
    name: str
    description: str | None
    price: float
    sku: str
    stock_quantity: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ProductUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = None
    description: str | None = None
    price: float | None = None
    sku: str | None = None
    stock_quantity: int | None = None
    is_active: bool | None = None
