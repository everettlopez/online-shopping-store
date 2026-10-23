from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
import jwt

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

def create_user_token(user: User) -> str:
    """A login token for the user. It carries their token_version, so it stops working
    when revoke_sessions() is called (a password change, or logging out everywhere)."""
    return create_access_token({"sub": str(user.user_id), "ver": user.token_version})

def revoke_sessions(user: User):
    """End every login the user has, on every device; the caller commits. Tokens are
    only checked, not stored, so this bumps the version they must match."""
    user.token_version += 1

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
        # Rejects a bad signature, a malformed token and an expired one
        payload = jwt.decode(token, signing_key(), algorithms=[ALGORITHM], options={"require": ["exp", "sub"]})
        user_id = int(payload["sub"])
        # Tokens from before versions existed count as version 0
        version = int(payload.get("ver", 0))
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid token")

    user = session.exec(select(User).where(User.user_id == user_id)).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Signed out everywhere (or the password changed) since this token was issued
    if version != user.token_version:
        raise HTTPException(status_code=401, detail="Your session has ended. Please log in again")

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