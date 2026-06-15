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