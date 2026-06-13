from fastapi import APIRouter, Depends, HTTPException, Security, Response
from sqlmodel import Session, select
from app.db.session import get_session
from app.models.user import User
from app.auth.core import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)
from app.schemas.user import UserCreate, UserLogin, UserRead
from datetime import datetime
from app.auth.core import CurrentUser

router = APIRouter()

@router.post("/register")
def register(user: UserCreate, session: Session = Depends(get_session)):
    statement = select(User).where(User.email == user.email)       # SQL Query Statement
    existing = session.exec(statement).first()                     # Database Lookup

    if existing:
        raise HTTPException(status_code=400, detail="Email already taken")
    
    db_user = User(
        email = user.email,
        hashed_password = hash_password(user.password),
        first_name = user.first_name,
        last_name = user.last_name,
        created_at = datetime.utcnow()
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return {"message": "User registered successfully"}

@router.post("/login")
def login(data: UserLogin, response: Response, session: Session = Depends(get_session)):
    statement = select(User).where(User.email == data.email)
    user = session.exec(statement).first()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    token = create_access_token({"sub": str(user.user_id)})

    response.set_cookie(
        key="shop_token",
        value=token,
        httponly=True,
        samesite="lax",
    )

    return {"access_token": token, "token_type": "bearer"}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("shop_token")
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserRead)
def read_current_user(user: CurrentUser):
    return user

@router.delete("/me")
def delete_account(user: CurrentUser, response: Response, session: Session = Depends(get_session)):
    session.delete(user)
    session.commit()

    response.delete_cookie("shop_token")

    return {"message": "Account deleted successfully"}

@router.put("/me/email", response_model = UserRead)
def update_email(user: CurrentUser, new_email: str, session: Session = Depends(get_session)):

    # Check if the email already exists
    exists_query = session.exec(select(User).where(User.email == new_email)).first()

    if exists_query:
        raise HTTPException(status_code=400, detail="Email already taken")
    
    user.email = new_email
    session.add(user)
    session.commit()
    session.refresh(user)

    return user

@router.put("/me/password")
def update_password(
    old_password: str,
    new_password: str,
    user: CurrentUser,
    session: Session = Depends(get_session)
):
    
    if old_password == new_password:
        raise HTTPException(status_code=400, detail="New password must be different")

    # Verify the old password
    if not verify_password(old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid Credentials")
    
    user.hashed_password = hash_password(new_password)
    session.add(user)
    session.commit()

    return {"message": "Password updated successfully"}