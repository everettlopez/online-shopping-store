from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db.session import get_session
from app.auth.dependencies import admin_required
from app.auth.core import hash_password

from app.models.user import User
from app.schemas.user import UserRead, UserResponse, AdminUserCreate, AdminUserUpdate, Metadata as UserMetadata

from app.database.users import (
    database_get_users,
    database_get_user_by_id,
    database_get_user_by_email,
    database_user_has_orders,
    database_delete_user
)



router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(admin_required)]
)

@router.get("/")
def admin_home():
    return {"message": "Welcome to the admin dashboard"}

@router.get("/users", response_model=UserResponse)
def get_all_users(session: Session = Depends(get_session), sort: str | None = None):
    users = database_get_users(session, sort)

    user_reads = [UserRead.model_validate(u.__dict__) for u in users]


    return UserResponse(
        metadata = UserMetadata(count=len(users), sort=sort),
        users = user_reads
    )

@router.post("/users", response_model=UserRead)
def create_user(data: AdminUserCreate, session: Session = Depends(get_session)):
    if database_get_user_by_email(session, data.email):
        raise HTTPException(status_code=409, detail="Email already taken")

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        is_admin=data.is_admin
    )

    session.add(user)
    session.commit()
    session.refresh(user)
    return UserRead.model_validate(user.__dict__)

@router.put("/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    data: AdminUserUpdate,
    session: Session = Depends(get_session),
    admin: User = Depends(admin_required)
):
    user = database_get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = data.model_dump(exclude_unset=True)

    if update_data.get("is_admin") is False and user.user_id == admin.user_id:
        raise HTTPException(status_code=400, detail="You cannot remove your own admin rights")

    if "email" in update_data:
        existing = database_get_user_by_email(session, update_data["email"])
        if existing and existing.user_id != user.user_id:
            raise HTTPException(status_code=409, detail="Email already taken")

    # Blank password means "leave it unchanged"
    password = update_data.pop("password", None)
    if password:
        user.hashed_password = hash_password(password)

    for key, value in update_data.items():
        if value is not None:
            setattr(user, key, value)

    session.add(user)
    session.commit()
    session.refresh(user)
    return UserRead.model_validate(user.__dict__)

@router.delete("/users/{user_id}")
def delete_user(user_id: int, session: Session = Depends(get_session), admin: User = Depends(admin_required)):
    user = database_get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.user_id == admin.user_id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")

    if database_user_has_orders(session, user_id):
        raise HTTPException(status_code=409, detail="User has orders and cannot be deleted")

    database_delete_user(session, user)
    return {"message": "User deleted"}
