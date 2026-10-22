from sqlmodel import Field, SQLModel
from datetime import datetime


class PasswordResetToken(SQLModel, table=True):
    __tablename__ = "password_reset_tokens"

    token_id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.user_id", index=True)

    # SHA-256 of the token in the emailed link; the token itself is never stored
    token_hash: str = Field(max_length=64, unique=True, index=True)

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    expires_at: datetime = Field(nullable=False)
    used_at: datetime | None = Field(default=None)
