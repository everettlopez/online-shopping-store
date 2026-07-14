from sqlmodel import SQLModel
from pydantic import EmailStr, BaseModel
from datetime import datetime

class Metadata(BaseModel):
    count: int
    sort: str | None = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRead(BaseModel):
    user_id: int
    email: EmailStr
    first_name: str
    last_name: str
    created_at: datetime
    is_admin: bool

class UserResponse(BaseModel):
    metadata: Metadata
    users: list[UserRead]