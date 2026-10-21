from sqlmodel import Session, select, delete
from app.models.user import User
from app.models.address import Address
from app.models.cart import Cart, CartItem
from app.models.order import Order

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
def database_get_user_by_email(session: Session, email: str):
    return session.exec(select(User).where(User.email == email)).first()

def database_user_has_orders(session: Session, user_id: int) -> bool:
    # Orders are financial records, so users who have them are kept
    return session.exec(select(Order).where(Order.user_id == user_id)).first() is not None

def database_delete_user(session: Session, user: User):
    """Delete a user along with their cart and addresses. Callers must check
    database_user_has_orders first, since orders reference the user."""
    cart_ids = session.exec(select(Cart.cart_id).where(Cart.user_id == user.user_id)).all()
    if cart_ids:
        session.exec(delete(CartItem).where(CartItem.cart_id.in_(cart_ids)))
    session.exec(delete(Cart).where(Cart.user_id == user.user_id))
    session.exec(delete(Address).where(Address.user_id == user.user_id))

    session.delete(user)
    session.commit()
