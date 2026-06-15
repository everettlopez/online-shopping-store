# app/auth/dependencies.py

from fastapi import Depends, HTTPException
from app.auth.core import get_current_user
from app.models.user import User

def admin_required(user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admins only")
    return user
