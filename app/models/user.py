from __future__ import annotations

from sqlmodel import Field, SQLModel
from datetime import datetime
from pydantic import EmailStr


class User(SQLModel, table=True):
    __tablename__ = "users"

    user_id: int | None = Field(default=None, primary_key=True)
    email: EmailStr = Field(unique=True, index=True)
    hashed_password: str = Field(nullable=False)
    first_name: str = Field(nullable=False)
    last_name: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    is_admin: bool = False
    # Login tokens carry this; raising it (app.auth.core.revoke_sessions) ends every
    # session the user has
    token_version: int = Field(default=0, nullable=False)

    # The Stripe Customer used at checkout (Stripe Tax reads its shipping address)
    stripe_customer_id: str | None = Field(default=None)

    