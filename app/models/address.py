from __future__ import annotations

from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional


class Address(SQLModel, table=True):
    __tablename__ = "addresses"

    address_id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.user_id")

    full_name: str                       # Recipient, printed on the shipping label
    phone: Optional[str] = None          # Carriers use it for delivery problems
    line1: str
    line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    county: Optional[str] = None
    country: str = Field(default="US", sa_column_kwargs={"server_default": "US"})   # ISO 3166-1 alpha-2

    address_type: str  # "shipping" or "billing"

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Deleting hides the address; the row stays because orders and checkouts in
    # progress may point at it
    deleted_at: datetime | None = Field(default=None)
