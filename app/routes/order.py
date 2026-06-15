from fastapi import APIRouter, Depends, HTTPException, Security, Response
from sqlmodel import Session, select
from app.db.session import get_session
from app.models.user import User
from app.models.address import Address
from datetime import datetime
from app.auth.core import CurrentUser
from app.schemas.order import OrderCreate, OrderRead
from app.models.order import Order

from app.models.order_item import OrderItem
from app.schemas.order_item import OrderItemRead, OrderItemUpdate

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("/", response_model=OrderRead)
def create_order(data: OrderCreate, user: CurrentUser, session: Session = Depends(get_session)):

    # Validate shipping address
    shipping = session.get(Address, data.shipping_address_id)
    if not shipping or shipping.user_id != user.user_id:
        raise HTTPException(status_code=400, detail="Invalid shipping address")
    
    # Validate billing address
    billing = session.get(Address, data.billing_address_id)
    if not billing or billing.user_id != user.user_id:
        raise HTTPException(status_code=400, detail="Invalid billing address")
    
    # Generate order number
    order_number = f"ORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    order = Order(
        user_id=user.user_id,
        shipping_address_id=data.shipping_address_id,
        billing_address_id=data.billing_address_id,
        total_amount=data.total_amount,
        order_number=order_number,
        status="pending"
    )

    session.add(order)
    session.commit()
    session.refresh(order)

    return order

@router.get("/", response_model = list[OrderRead])
def list_orders(user: CurrentUser, session: Session = Depends(get_session)):
    statement = select(Order).where(Order.user_id == user.user_id)
    return session.exec(statement).all()

@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: int, user: CurrentUser, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)

    if not order or order.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="Order not found")

    return order

@router.put("/{order_id}/status")
def update_order_status(order_id: int, status: str, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = status
    session.add(order)
    session.commit()
    session.refresh(order)

    return {"message": "Order status updated"}

@router.delete("/{order_id}")
def delete_order(order_id: int, user: CurrentUser, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)

    if not order or order.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="Order not found")

    session.delete(order)
    session.commit()

    return {"message": "Order deleted"}

# ---------------------------------------------------------
# GET /orders/{order_id}/items → list all items in an order
# ---------------------------------------------------------
@router.get("/{order_id}/items", response_model=list[OrderItemRead])
def list_order_items(order_id: int, user: CurrentUser, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)

    if not order or order.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="Order not found")

    statement = select(OrderItem).where(OrderItem.order_id == order_id)
    return session.exec(statement).all()


# -------------------------------------------------------------------
# GET /orders/{order_id}/items/{item_id} → get a single order item
# -------------------------------------------------------------------
@router.get("/{order_id}/items/{item_id}", response_model=OrderItemRead)
def get_order_item(order_id: int, item_id: int, user: CurrentUser, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)

    if not order or order.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="Order not found")

    item = session.get(OrderItem, item_id)

    if not item or item.order_id != order_id:
        raise HTTPException(status_code=404, detail="Order item not found")

    return item


# -------------------------------------------------------------------
# PUT /orders/{order_id}/items/{item_id} → update quantity
# -------------------------------------------------------------------
@router.put("/{order_id}/items/{item_id}", response_model=OrderItemRead)
def update_order_item(order_id: int, item_id: int, data: OrderItemUpdate, user: CurrentUser, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)

    if not order or order.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="Order not found")

    item = session.get(OrderItem, item_id)

    if not item or item.order_id != order_id:
        raise HTTPException(status_code=404, detail="Order item not found")

    update_data = data.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(item, key, value)

    # Recalculate subtotal
    item.subtotal = item.unit_price * item.quantity

    session.add(item)
    session.commit()
    session.refresh(item)

    return item


# -------------------------------------------------------------------
# DELETE /orders/{order_id}/items/{item_id} → delete order item
# -------------------------------------------------------------------
@router.delete("/{order_id}/items/{item_id}")
def delete_order_item(order_id: int, item_id: int, user: CurrentUser, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)

    if not order or order.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="Order not found")

    item = session.get(OrderItem, item_id)

    if not item or item.order_id != order_id:
        raise HTTPException(status_code=404, detail="Order item not found")

    session.delete(item)
    session.commit()

    return {"message": "Order item deleted"}
