from sqlmodel import SQLModel
from pydantic import EmailStr, BaseModel, Field, field_validator
from datetime import datetime
from typing import Annotated

MIN_PASSWORD_LENGTH = 8

# A new password; checked on register, password change and admin create
NewPassword = Annotated[str, Field(min_length=MIN_PASSWORD_LENGTH, max_length=72)]   # bcrypt only uses the first 72 bytes

class Metadata(BaseModel):
    count: int
    sort: str | None = None


class UserCreate(BaseModel):
    email: EmailStr
    password: NewPassword
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
    password: NewPassword
    first_name: str
    last_name: str
    is_admin: bool = False

class AdminUserUpdate(BaseModel):
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_admin: bool | None = None
    password: str | None = None

    @field_validator("password")
    @classmethod
    def password_length(cls, password: str | None):
        # Blank means "leave the password unchanged"; anything else must be a valid new password
        if password and not MIN_PASSWORD_LENGTH <= len(password) <= 72:
            raise ValueError(f"Password must be between {MIN_PASSWORD_LENGTH} and 72 characters")
        return password

class EmailUpdate(BaseModel):
    new_email: EmailStr
    current_password: str

class PasswordUpdate(BaseModel):
    old_password: str
    new_password: NewPassword
