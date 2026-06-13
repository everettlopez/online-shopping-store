from sqlmodel import SQLModel
from pydantic import EmailStr
from datetime import datetime

class UserCreate(SQLModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str

class UserLogin(SQLModel):
    email: EmailStr
    password: str

class UserRead(SQLModel):
    user_id: int
    email: EmailStr
    first_name: str
    last_name: str
    created_at: datetime