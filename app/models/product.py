from __future__ import annotations
from sqlmodel import SQLModel, Field
from datetime import datetime

class Product(SQLModel, table=True):
    __tablename__ = "products"


    product_id: int | None = Field(default=None, primary_key=True)
    category_id: int = Field(foreign_key="categories.category_id")

    name: str
    description: str | None = None
    price: float
    sku: str
    stock_quantity: int = 0
    is_active: bool = True

    created_at: datetime = Field(default_factory=datetime.utcnow)
