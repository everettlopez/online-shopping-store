from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.session import get_session
from app.auth.core import CurrentUser

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.schemas.cart import CartRead
from app.schemas.cart_item import CartItemCreate, CartItemRead, CartItemUpdate

router = APIRouter(prefix="/cart", tags=["Cart"])

# Helper: Get or create cart for user
def get_or_create_cart(user_id: int, session: Session) -> Cart:
    statement = select(Cart).where(Cart.user_id == user_id)
    cart = session.exec(statement).first()

    if not cart:
        cart = Cart(user_id=user_id)
        session.add(cart)
        session.commit()
        session.refresh(cart)

    return cart

@router.get("/", response_model=CartRead)
def get_cart(user: CurrentUser, session: Session = Depends(get_session)):
    cart = get_or_create_cart(user.user_id, session)
    return cart

@router.get("/items", response_model=list[CartItemRead])
def get_cart_items(user: CurrentUser, session: Session = Depends(get_session)):
    cart = get_or_create_cart(user.user_id, session)

    statement = select(CartItem).where(CartItem.cart_id == cart.cart_id)
    items = session.exec(statement).all()

    return items

@router.post("/items", response_model=CartItemRead)
def add_item_to_cart(
    data: CartItemCreate,
    user: CurrentUser,
    session: Session = Depends(get_session)
):
    cart = get_or_create_cart(user.user_id, session)

    # Check if item already exists → update quantity instead
    statement = select(CartItem).where(
        CartItem.cart_id == cart.cart_id,
        CartItem.product_id == data.product_id
    )
    existing_item = session.exec(statement).first()

    if existing_item:
        existing_item.quantity += data.quantity
        session.add(existing_item)
        session.commit()
        session.refresh(existing_item)
        return existing_item

    # Create new cart item
    item = CartItem(
        cart_id=cart.cart_id,
        product_id=data.product_id,
        quantity=data.quantity
    )

    session.add(item)
    session.commit()
    session.refresh(item)

    return item

@router.put("/items/{item_id}", response_model=CartItemRead)
def update_cart_item(
    item_id: int,
    data: CartItemUpdate,
    user: CurrentUser,
    session: Session = Depends(get_session)
):
    cart = get_or_create_cart(user.user_id, session)

    item = session.get(CartItem, item_id)

    if not item or item.cart_id != cart.cart_id:
        raise HTTPException(status_code=404, detail="Cart item not found")

    item.quantity = data.quantity
    session.add(item)
    session.commit()
    session.refresh(item)

    return item

@router.delete("/items/{item_id}")
def remove_cart_item(
    item_id: int,
    user: CurrentUser,
    session: Session = Depends(get_session)
):
    cart = get_or_create_cart(user.user_id, session)

    item = session.get(CartItem, item_id)

    if not item or item.cart_id != cart.cart_id:
        raise HTTPException(status_code=404, detail="Cart item not found")

    session.delete(item)
    session.commit()

    return {"message": "Item removed from cart"}

@router.delete("/clear")
def clear_cart(user: CurrentUser, session: Session = Depends(get_session)):
    cart = get_or_create_cart(user.user_id, session)

    statement = select(CartItem).where(CartItem.cart_id == cart.cart_id)
    items = session.exec(statement).all()

    for item in items:
        session.delete(item)

    session.commit()

    return {"message": "Cart cleared"}