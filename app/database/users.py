from sqlmodel import Session, select
from app.models.user import User

def database_get_users(session: Session, sort: str | None = None):

    users = session.exec(select(User)).all()

    if sort == None:
        return users
    
    if sort == "id":
        users = sorted(users, key=lambda u: u.user_id)
    elif sort == "name":
        users = sorted(users, key=lambda u: u.first_name)
    elif sort == "created_at":
        users = sorted(users, key=lambda u: u.created_at)
    else:
        # Unsupported sort ket -> ifnore or raise
        return users

    return users

def database_get_user_by_id(session: Session, user_id: int):
    return session.get(User, user_id)