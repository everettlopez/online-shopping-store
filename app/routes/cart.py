from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.session import get_session
from app.auth.core import CurrentUser

from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.schemas.cart import CartRead, CartItemRead
from app.schemas.cart_item import CartItemCreate, CartItemUpdate

router = APIRouter(prefix="/cart", tags=["Cart"])

# Helper: Get or create cart for user
def get_or_create_cart(user_id: int, session: Session) -> Cart:

    cart = session.exec(select(Cart).where(Cart.user_id == user_id)).first()

    if not cart:
        cart = Cart(user_id=user_id)
        session.add(cart)
        session.commit()
        session.refresh(cart)

    return cart

@router.get("/", response_model=CartRead)
def get_cart(user: CurrentUser, session: Session = Depends(get_session)):
    cart = get_or_create_cart(user.user_id, session)

    items = session.exec(select(CartItem).where(CartItem.cart_id == cart.cart_id)).all()

    enriched_items = []

    for item in items:
        product = session.exec(select(Product).where(Product.product_id == item.product_id)).first()

        enriched_items.append(CartItemRead(
            cart_item_id=item.cart_item_id,
            product_id=item.product_id,
            quantity=item.quantity,
            product=product
        ))

    return CartRead(
        cart_id=cart.cart_id,
        user_id=cart.user_id,
        created_at=cart.created_at,
        updated_at=cart.updated_at,
        items=enriched_items
    )

@router.get("/items", response_model=list[CartItemRead])
def get_cart_items(user: CurrentUser, session: Session = Depends(get_session)):
    cart = get_or_create_cart(user.user_id, session)

    items = session.exec(select(CartItem).where(CartItem.cart_id == cart.cart_id)).all()

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

        product = session.exec(select(Product).where(Product.product_id == existing_item.product_id)).first()

        return CartItemRead(
            cart_item_id=existing_item.cart_item_id,
            product_id=existing_item.product_id,
            quantity=existing_item.quantity,
            product=product
        )

    # Create new cart item
    item = CartItem(
        cart_id=cart.cart_id,
        product_id=data.product_id,
        quantity=data.quantity
    )

    session.add(item)
    session.commit()
    session.refresh(item)

    product = session.exec(select(Product).where(Product.product_id == item.product_id)).first()
    

    return CartItemRead(
        cart_item_id=item.cart_item_id,
        product_id=item.product_id,
        quantity=item.quantity,
        product=product
    )

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