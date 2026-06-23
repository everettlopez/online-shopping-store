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

    size: str | None = None
    color: str | None = None
    image_url: str | None = None

    stock_quantity: int = 1
    is_active: bool = True

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)