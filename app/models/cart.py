from __future__ import annotations

from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class Cart(SQLModel, table=True):
    __tablename__ = "carts"
    cart_id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.user_id")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CartItem(SQLModel, table=True):
    __tablename__ = "cart_Items"

    cart_item_id: int | None = Field(default=None, primary_key=True)
    cart_id: int = Field(foreign_key="carts.cart_id")
    product_id: int = Field(foreign_key="products.product_id")
    quantity: int = Field(default=1)
