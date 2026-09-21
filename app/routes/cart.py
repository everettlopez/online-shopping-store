from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.session import get_session
from app.auth.core import CurrentUser
import uuid

from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.schemas.product import ProductRead
from app.schemas.cart import CartRead, CartItemRead
from app.schemas.cart_item import CartItemCreate, CartItemUpdate

from app.schemas.checkout import CheckoutRequest
from app.schemas.order import OrderRead, OrderItemRead
from app.models.order import Order, OrderItem
from app.models.address import Address
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

    # Get user's cart
    cart = session.exec(
        select(Cart).where(Cart.user_id == user.user_id)
    ).first()

    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    # Get product
    product = session.exec(
        select(Product).where(Product.product_id == product_id)
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Get category (same pattern as product routes)
    category = session.exec(
        select(Category).where(Category.category_id == product.category_id)
    ).first()

    # Create cart item
    cart_item = CartItem(
        cart_id=cart.cart_id,
        product_id=product.product_id,
        quantity=1
    )

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

@router.post("/checkout", response_model=OrderRead)
def checkout(
    data: CheckoutRequest,
    user: CurrentUser,
    session: Session = Depends(get_session)
):
    cart = session.exec(
        select(Cart).where(Cart.user_id == user.user_id)
    ).first()

    if not cart:
        raise HTTPException(status_code=400, detail="Cart not found")

    cart_items = session.exec(
        select(CartItem).where(CartItem.cart_id == cart.cart_id)
    ).all()

    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    shipping = session.get(Address, data.shipping_address_id)
    billing = session.get(Address, data.billing_address_id)

    if not shipping or shipping.user_id != user.user_id:
        raise HTTPException(status_code=400, detail="Invalid shipping address")

    if not billing or billing.user_id != user.user_id:
        raise HTTPException(status_code=400, detail="Invalid billing address")

    total_amount = 0

    for item in cart_items:
        product = session.get(Product, item.product_id)

        if not product:
            raise HTTPException(status_code=400, detail="Product not found")

        if product.stock_quantity < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough stock for {product.name}"
            )

        total_amount += product.price * item.quantity

    order = Order(
        user_id=user.user_id,
        shipping_address_id=shipping.address_id,
        billing_address_id=billing.address_id,
        total_amount=total_amount,
        order_number=str(uuid.uuid4())[:8],
        status="pending"
    )

    session.add(order)
    session.commit()
    session.refresh(order)

    for item in cart_items:
        product = session.get(Product, item.product_id)

        order_item = OrderItem(
            order_id=order.order_id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=product.price,
            subtotal=product.price * item.quantity
        )

        session.add(order_item)

        product.stock_quantity -= item.quantity
        session.add(product)

    session.commit()

    for item in cart_items:
        session.delete(item)
    session.commit()

    order_items = session.exec(
        select(OrderItem).where(OrderItem.order_id == order.order_id)
    ).all()

    enriched_items = []
    for oi in order_items:
        product = session.get(Product, oi.product_id)

        enriched_items.append(OrderItemRead(
            order_item_id=oi.order_item_id,
            order_id=oi.order_id,
            product=product,
            quantity=oi.quantity
        ))

    shipping_address = session.get(Address, order.shipping_address_id)
    billing_address = session.get(Address, order.billing_address_id)


    return OrderRead(
        order_id=order.order_id,
        order_number=order.order_number,
        status=order.status,
        created_at=order.created_at,
        updated_at=order.updated_at,
        order_date=order.order_date,
        total_amount=order.total_amount,
        shipping_address=shipping_address,   
        billing_address=billing_address,
        items=enriched_items
    )
