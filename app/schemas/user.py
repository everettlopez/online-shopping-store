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

class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    is_admin: bool = False

class AdminUserUpdate(BaseModel):
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_admin: bool | None = None
    password: str | None = None
