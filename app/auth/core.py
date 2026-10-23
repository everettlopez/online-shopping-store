from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import jwt, JWTError

from fastapi import Depends, HTTPException, Response
from fastapi.security import APIKeyCookie, HTTPBearer
from sqlmodel import Session, select
from app.db.session import get_session
from app.models.user import User
from app.settings import MIN_JWT_SECRET_LENGTH, cookie_samesite, cookie_secure
from typing import Annotated
import os


JWT_COOKIE_KEY = "shop_token"
cookie_scheme = APIKeyCookie(name=JWT_COOKIE_KEY, auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)

# A missing key is reported by check_required_settings() at startup
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")

def signing_key() -> str:
    # Never sign or accept tokens with an empty or weak key, even if startup was skipped
    if len(SECRET_KEY) < MIN_JWT_SECRET_LENGTH:
        raise RuntimeError("JWT_SECRET_KEY is missing or too short")
    return SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


# Password Hashing

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)



def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, signing_key(), algorithm=ALGORITHM)

def set_auth_cookie(response: Response, token: str):
    response.set_cookie(
        key=JWT_COOKIE_KEY,
        value=token,
        httponly=True,
        samesite=cookie_samesite(),
        secure=cookie_secure(),
        path="/",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,   # the cookie lives as long as the token
    )

def clear_auth_cookie(response: Response):
    # Browsers only drop the cookie when these attributes match the ones it was set with
    response.delete_cookie(
        key=JWT_COOKIE_KEY,
        path="/",
        httponly=True,
        samesite=cookie_samesite(),
        secure=cookie_secure(),
    )

def get_access_token(cookie_token = Depends(cookie_scheme), bearer_token = Depends(bearer_scheme)):
    if cookie_token:
        return cookie_token
    
    if bearer_token:
        return bearer_token.credentials
    
    raise HTTPException(status_code=401, detail="Not authenticated")

def user_from_token(token: str, session: Session) -> User:
    try:
        payload = jwt.decode(token, signing_key(), algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = session.exec(select(User).where(User.user_id == int(user_id))).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

def get_current_user(token: str = Depends(get_access_token), session: Session = Depends(get_session)):
    return user_from_token(token, session)

def get_optional_user(cookie_token = Depends(cookie_scheme), bearer_token = Depends(bearer_scheme), session: Session = Depends(get_session)):
    """The logged-in user, or None for a guest. An expired or invalid token also counts
    as a guest, so a stale cookie never blocks shopping without an account."""
    token = cookie_token or (bearer_token.credentials if bearer_token else None)
    if not token:
        return None
    try:
        return user_from_token(token, session)
    except HTTPException:
        return None

CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]