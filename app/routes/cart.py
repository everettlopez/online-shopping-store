from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.session import get_session
from app.auth.core import CurrentUser

from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.schemas.product import ProductRead
from app.schemas.cart import CartRead, CartItemRead
from app.schemas.cart_item import CartItemCreate, CartItemUpdate, MAX_CART_QUANTITY
from app.models.category import Category

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

def ensure_quantity_allowed(product: Product, quantity: int):
    if quantity > MAX_CART_QUANTITY:
        raise HTTPException(status_code=400, detail=f"You can buy at most {MAX_CART_QUANTITY} of one product")

    if quantity > product.stock_quantity:
        raise HTTPException(status_code=400, detail=f"Not enough stock for {product.title}")

@router.get("/", response_model=CartRead)
def get_cart(user: CurrentUser, session: Session = Depends(get_session)):
    cart = get_or_create_cart(user.user_id, session)

    items = session.exec(
        select(CartItem).where(CartItem.cart_id == cart.cart_id)
    ).all()

    enriched_items = []

    for item in items:
        product = session.exec(
            select(Product).where(Product.product_id == item.product_id)
        ).first()

        # Load category (same pattern as product routes)
        category = session.exec(
            select(Category).where(Category.category_id == product.category_id)
        ).first()

        enriched_product = ProductRead(
            product_id=product.product_id,
            category=category,
            title=product.title,
            description=product.description,
            price=product.price,
            size=product.size,
            color=product.color,
            thumbnail=product.thumbnail,
            stock_quantity=product.stock_quantity,
            is_active=product.is_active,
            created_at=product.created_at,
            updated_at=product.updated_at,
            images=product.images
        )

        enriched_items.append(
            CartItemRead(
                cart_item_id=item.cart_item_id,
                product_id=item.product_id,
                quantity=item.quantity,
                product=enriched_product
            )
        )

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
    user: CurrentUser,
    product_id: int,
    session: Session = Depends(get_session)
):

    # Get user's cart (a first-time shopper doesn't have one yet)
    cart = get_or_create_cart(user.user_id, session)

    # Get product
    product = session.exec(
        select(Product).where(Product.product_id == product_id)
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if not product.is_active:
        raise HTTPException(status_code=400, detail="Product is not available")

    # Adding a product that's already in the cart raises its quantity instead of adding a row
    cart_item = session.exec(
        select(CartItem).where(CartItem.cart_id == cart.cart_id, CartItem.product_id == product.product_id)
    ).first() or CartItem(cart_id=cart.cart_id, product_id=product.product_id, quantity=0)

    ensure_quantity_allowed(product, cart_item.quantity + 1)
    cart_item.quantity += 1

    # Get category (same pattern as product routes)
    category = session.exec(
        select(Category).where(Category.category_id == product.category_id)
    ).first()

    session.add(cart_item)
    session.commit()
    session.refresh(cart_item)

    # Build ProductRead exactly like product routes
    enriched_product = ProductRead(
        product_id=product.product_id,
        category=category,
        title=product.title,
        description=product.description,
        price=product.price,
        size=product.size,
        color=product.color,
        thumbnail=product.thumbnail,
        stock_quantity=product.stock_quantity,
        is_active=product.is_active,
        created_at=product.created_at,
        updated_at=product.updated_at,
        images=product.images
    )

    # Return CartItemRead
    return CartItemRead(
        cart_item_id=cart_item.cart_item_id,
        product_id=cart_item.product_id,
        quantity=cart_item.quantity,
        product=enriched_product
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

    ensure_quantity_allowed(session.get(Product, item.product_id), data.quantity)

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
