from sqlmodel import Field, SQLModel
from datetime import datetime
from pydantic import EmailStr

class User(SQLModel, table=True):
    user_id: int | None = Field(default=None, primary_key=True)
    email: EmailStr = Field(unique=True, index=True)
    hashed_password: str = Field(nullable=False)
    first_name: str = Field(nullable=False)
    last_name: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)