from __future__ import annotations
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class Order(SQLModel, table=True):
    __tablename__ = "orders"
    order_id: int | None = Field(default = None, primary_key = True)
    user_id: int = Field(foreign_key = "users.user_id")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    shipping_address_id: int = Field(foreign_key="addresses.address_id")
    billing_address_id: int = Field(foreign_key="addresses.address_id")

    order_number: str = Field(index=True, unique=True)
    status: str = Field(default="pending")  # pending, paid, shipped, cancelled
    order_date: datetime = Field(default_factory=datetime.utcnow)
    total_amount: float



class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"

    order_item_id: int | None = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.order_id")
    product_id: int = Field(foreign_key="products.product_id")
    quantity: int
    unit_price: float
    subtotal: float


    