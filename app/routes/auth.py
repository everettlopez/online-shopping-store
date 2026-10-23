from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Security, Response
from sqlmodel import Session, select, delete
from app.db.session import get_session
from app.models.user import User
from app.auth.core import (
    hash_password,
    verify_password,
    create_user_token,
    revoke_sessions,
    set_auth_cookie,
    clear_auth_cookie
)
from app.schemas.user import UserCreate, UserLogin, UserRead, EmailUpdate, PasswordUpdate, ForgotPasswordRequest, PasswordReset
from app.database.users import database_user_has_orders, database_delete_user
from datetime import datetime, timedelta
from app.auth.core import CurrentUser, OptionalUser
from app.models.password_reset import PasswordResetToken
from app.mail import build_password_reset_email, send_email
from app.settings import password_reset_minutes
from app.rate_limit import rate_limit
import hashlib
import secrets

router = APIRouter(prefix="/auth", tags=["Auth"])

# A user gets at most one reset email per minute, which keeps a script from
# flooding their inbox (or using up the email provider's daily quota)
RESET_EMAIL_COOLDOWN = timedelta(minutes=1)
FORGOT_PASSWORD_MESSAGE = "If an account uses that email, we've sent it a link to reset the password"


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

@router.post("/register", dependencies=[rate_limit("auth")])
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

@router.post("/login", dependencies=[rate_limit("auth")])
def login(data: UserLogin, response: Response, session: Session = Depends(get_session)):
    statement = select(User).where(User.email == data.email)
    user = session.exec(statement).first()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    token = create_user_token(user)
    set_auth_cookie(response, token)

    return {"access_token": token, "token_type": "bearer"}

@router.post("/logout")
def logout(response: Response):
    clear_auth_cookie(response)
    return {"message": "Logged out"}

@router.post("/logout-all")
def logout_everywhere(user: CurrentUser, response: Response, session: Session = Depends(get_session)):
    """Log out on every device, this one included (for a lost phone or a shared computer)."""
    revoke_sessions(user)
    session.add(user)
    session.commit()

    clear_auth_cookie(response)
    return {"message": "Logged out on every device"}



@router.get("/me", response_model=UserRead)
def read_current_user(user: CurrentUser):
    return user

# The storefront asks this on every page load to learn who's logged in. A guest gets
# null with a 200, rather than /me's 401, so browsers don't log an error for every visitor
@router.get("/session", response_model=UserRead | None)
def read_session(user: OptionalUser):
    return user

@router.delete("/me")
def delete_account(user: CurrentUser, response: Response, session: Session = Depends(get_session)):
    if database_user_has_orders(session, user.user_id):
        raise HTTPException(status_code=409, detail="Accounts with orders cannot be deleted")

    database_delete_user(session, user)

    clear_auth_cookie(response)

    return {"message": "Account deleted successfully"}

@router.put("/me/email", response_model = UserRead)
def update_email(data: EmailUpdate, user: CurrentUser, session: Session = Depends(get_session)):

    # Changing the login email takes the current password, so a stolen session can't take over the account
    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid Credentials")

    # Check if the email already exists
    exists_query = session.exec(select(User).where(User.email == data.new_email)).first()

    if exists_query:
        raise HTTPException(status_code=400, detail="Email already taken")
    
    user.email = data.new_email
    session.add(user)
    session.commit()
    session.refresh(user)

    return user

@router.put("/me/password")
def update_password(
    data: PasswordUpdate,
    user: CurrentUser,
    response: Response,
    session: Session = Depends(get_session)
):
    
    if data.old_password == data.new_password:
        raise HTTPException(status_code=400, detail="New password must be different")

    # Verify the old password
    if not verify_password(data.old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid Credentials")
    
    user.hashed_password = hash_password(data.new_password)
    # Whoever else is logged in (say, with a stolen session) is logged out; this
    # browser gets a new token and stays logged in
    revoke_sessions(user)
    session.add(user)
    session.commit()

    token = create_user_token(user)
    set_auth_cookie(response, token)

    return {"message": "Password updated successfully", "access_token": token, "token_type": "bearer"}


@router.post("/forgot-password", dependencies=[rate_limit("auth")])
def forgot_password(data: ForgotPasswordRequest, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    # Same answer whether or not the account exists, so this can't be used to find accounts
    user = session.exec(select(User).where(User.email == data.email)).first()
    if not user:
        return {"message": FORGOT_PASSWORD_MESSAGE}

    now = datetime.utcnow()
    recent = session.exec(
        select(PasswordResetToken)
        .where(PasswordResetToken.user_id == user.user_id)
        .where(PasswordResetToken.created_at > now - RESET_EMAIL_COOLDOWN)
    ).first()
    if recent:
        return {"message": FORGOT_PASSWORD_MESSAGE}

    token = secrets.token_urlsafe(32)
    minutes = password_reset_minutes()
    session.add(PasswordResetToken(
        user_id=user.user_id,
        token_hash=hash_reset_token(token),
        created_at=now,
        expires_at=now + timedelta(minutes=minutes),
    ))
    session.commit()

    background_tasks.add_task(send_email, build_password_reset_email(user.email, user.first_name, token, minutes))

    return {"message": FORGOT_PASSWORD_MESSAGE}

@router.post("/reset-password", dependencies=[rate_limit("auth")])
def reset_password(data: PasswordReset, session: Session = Depends(get_session)):
    # Locked so two requests with the same link can't both use it
    reset = session.exec(
        select(PasswordResetToken)
        .where(PasswordResetToken.token_hash == hash_reset_token(data.token))
        .with_for_update()
    ).first()

    if not reset or reset.used_at or reset.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="This reset link is invalid or has expired. Please request a new one")

    user = session.get(User, reset.user_id)
    user.hashed_password = hash_password(data.new_password)
    # Whoever had the old password may still be logged in
    revoke_sessions(user)
    session.add(user)

    # The link works once, and any other links sent to this user stop working too
    reset.used_at = datetime.utcnow()
    session.add(reset)
    session.exec(
        delete(PasswordResetToken)
        .where(PasswordResetToken.user_id == user.user_id)
        .where(PasswordResetToken.token_id != reset.token_id)
    )
    session.commit()

    return {"message": "Password reset. You can now sign in with your new password"}
