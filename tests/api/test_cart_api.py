from sqlmodel import select

from app.models.cart import CartItem
from app.models.order import Order, OrderItem
from app.models.product import Product


def test_get_cart_creates_empty_cart(user_client, user):
    response = user_client.get("/api/cart/")

    assert response.status_code == 200
    assert response.json()["user_id"] == user.user_id
    assert response.json()["items"] == []


def test_get_cart_includes_products(user_client, user, make_product, add_to_cart):
    product = make_product(title="Watch")
    add_to_cart(user, product, quantity=2)

    items = user_client.get("/api/cart/").json()["items"]

    assert len(items) == 1
    assert items[0]["quantity"] == 2
    assert items[0]["product"]["title"] == "Watch"
    assert items[0]["product"]["category"]["category_id"] == product.category_id


def test_add_item_for_first_time_shopper(user_client, make_product):
    # No GET /cart beforehand: the cart must be created on demand
    product = make_product()

    response = user_client.post("/api/cart/items", params={"product_id": product.product_id})

    assert response.status_code == 200
    assert response.json()["quantity"] == 1
    assert response.json()["product"]["product_id"] == product.product_id
    assert len(user_client.get("/api/cart/items").json()) == 1


def test_add_unknown_product(user_client):
    assert user_client.post("/api/cart/items", params={"product_id": 999}).status_code == 404


def test_update_item_quantity(user_client, user, make_product, add_to_cart):
    item = add_to_cart(user, make_product())

    response = user_client.put(f"/api/cart/items/{item.cart_item_id}", json={"quantity": 4})

    assert response.status_code == 200
    assert response.json()["quantity"] == 4


def test_remove_item(user_client, user, make_product, add_to_cart):
    item = add_to_cart(user, make_product())

    assert user_client.delete(f"/api/cart/items/{item.cart_item_id}").status_code == 200
    assert user_client.get("/api/cart/items").json() == []


def test_cannot_touch_someone_elses_cart_item(user_client, make_user, make_product, add_to_cart):
    item = add_to_cart(make_user(), make_product())

    assert user_client.put(f"/api/cart/items/{item.cart_item_id}", json={"quantity": 9}).status_code == 404
    assert user_client.delete(f"/api/cart/items/{item.cart_item_id}").status_code == 404
    assert user_client.delete("/api/cart/items/999").status_code == 404


def test_clear_cart(user_client, user, make_product, add_to_cart):
    add_to_cart(user, make_product())
    add_to_cart(user, make_product())

    assert user_client.delete("/api/cart/clear").status_code == 200
    assert user_client.get("/api/cart/items").json() == []


def test_cart_requires_login(client):
    assert client.get("/api/cart/").status_code == 401


# -----------------------------------------
# POST /cart/checkout
# -----------------------------------------

def checkout_body(shipping, billing):
    return {"total_amount": 0, "shipping_address_id": shipping.address_id, "billing_address_id": billing.address_id}


def test_checkout(user_client, session, user, make_address, make_product, add_to_cart):
    shipping, billing = make_address(user, "shipping"), make_address(user, "billing")
    shirt = make_product(price=20.0, stock_quantity=5)
    socks = make_product(price=2.5, stock_quantity=10)
    add_to_cart(user, shirt, quantity=2)
    add_to_cart(user, socks, quantity=4)

    response = user_client.post("/api/cart/checkout", json=checkout_body(shipping, billing))

    assert response.status_code == 200
    body = response.json()
    assert body["total_amount"] == 50.0
    assert body["status"] == "pending"
    assert body["first_name"] == user.first_name
    assert body["shipping_address"]["address_id"] == shipping.address_id
    assert sorted((i["product"]["product_id"], i["quantity"]) for i in body["items"]) == [(shirt.product_id, 2), (socks.product_id, 4)]

    session.expire_all()
    assert session.get(Product, shirt.product_id).stock_quantity == 3
    assert session.get(Product, socks.product_id).stock_quantity == 6
    assert session.exec(select(CartItem)).all() == []
    assert user_client.get(f"/api/orders/{body['order_number']}").status_code == 200


def test_checkout_without_cart_or_items(user_client, user, make_address):
    shipping = make_address(user)

    assert user_client.post("/api/cart/checkout", json=checkout_body(shipping, shipping)).json()["detail"] == "Cart not found"

    user_client.get("/api/cart/")  # creates an empty cart
    assert user_client.post("/api/cart/checkout", json=checkout_body(shipping, shipping)).json()["detail"] == "Cart is empty"


def test_checkout_with_someone_elses_address(user_client, user, make_user, make_address, make_product, add_to_cart):
    mine = make_address(user)
    theirs = make_address(make_user())
    add_to_cart(user, make_product())

    assert user_client.post("/api/cart/checkout", json=checkout_body(theirs, mine)).status_code == 400
    assert user_client.post("/api/cart/checkout", json=checkout_body(mine, theirs)).status_code == 400


def test_checkout_with_insufficient_stock(user_client, session, user, make_address, make_product, add_to_cart):
    address = make_address(user)
    add_to_cart(user, make_product(title="Rare Coin", stock_quantity=1), quantity=2)

    response = user_client.post("/api/cart/checkout", json=checkout_body(address, address))

    assert response.status_code == 400
    assert response.json()["detail"] == "Not enough stock for Rare Coin"
    assert session.exec(select(Order)).all() == []
    assert session.exec(select(OrderItem)).all() == []
