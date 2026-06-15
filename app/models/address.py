from __future__ import annotations

from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional


class Address(SQLModel, table=True):
    __tablename__ = "addresses"

    address_id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.user_id")

    line1: str
    line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    county: Optional[str] = None

    address_type: str  # "shipping" or "billing"

    created_at: datetime = Field(default_factory=datetime.utcnow)
