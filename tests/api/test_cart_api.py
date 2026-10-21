import pytest


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


def test_cannot_add_inactive_product(user_client, make_product):
    product = make_product(is_active=False)

    assert user_client.post("/api/cart/items", params={"product_id": product.product_id}).status_code == 400
    assert user_client.get("/api/cart/items").json() == []


def test_cannot_add_more_than_stock(user_client, make_product):
    product = make_product(stock_quantity=2)

    assert user_client.post("/api/cart/items", params={"product_id": product.product_id}).status_code == 200
    assert user_client.post("/api/cart/items", params={"product_id": product.product_id}).status_code == 200

    response = user_client.post("/api/cart/items", params={"product_id": product.product_id})

    assert response.status_code == 400
    assert len(user_client.get("/api/cart/items").json()) == 2


def test_update_item_quantity(user_client, user, make_product, add_to_cart):
    item = add_to_cart(user, make_product())

    response = user_client.put(f"/api/cart/items/{item.cart_item_id}", json={"quantity": 4})

    assert response.status_code == 200
    assert response.json()["quantity"] == 4


@pytest.mark.parametrize("quantity", [0, -2])
def test_quantity_must_be_positive(user_client, user, make_product, add_to_cart, quantity):
    # A negative quantity would lower the checkout total
    item = add_to_cart(user, make_product())

    assert user_client.put(f"/api/cart/items/{item.cart_item_id}", json={"quantity": quantity}).status_code == 422
    assert user_client.get("/api/cart/items").json()[0]["quantity"] == 1


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
