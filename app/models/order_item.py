from __future__ import annotations
from sqlmodel import SQLModel, Field
from datetime import datetime

class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"

    order_item_id: int | None = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.order_id")
    product_id: int = Field(foreign_key="products.product_id")

    quantity: int
    unit_price: float
    subtotal: float
