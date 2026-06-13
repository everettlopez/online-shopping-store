from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.session import get_session
from app.models.user import User
from app.auth.core import (
    UserCreate,
    UserLogin,
    hash_password,
    verify_password,
    create_access_token
)
from datetime import datetime

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
def login(data: UserLogin, session: Session = Depends(get_session)):
    statement = select(User).where(User.email == data.email)
    user = session.exec(statement).first()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    token = create_access_token({"sub": str(user.user_id)})

    return {"access_token": token, "token_type": "bearer"}