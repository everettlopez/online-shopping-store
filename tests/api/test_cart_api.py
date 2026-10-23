import pytest

from app.schemas.cart_item import MAX_CART_QUANTITY


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
    assert [i["quantity"] for i in user_client.get("/api/cart/items").json()] == [2]


def test_adding_same_product_raises_quantity(user_client, make_product):
    product = make_product()

    for _ in range(3):
        response = user_client.post("/api/cart/items", params={"product_id": product.product_id})

    assert response.json()["quantity"] == 3
    items = user_client.get("/api/cart/items").json()
    assert [(i["product_id"], i["quantity"]) for i in items] == [(product.product_id, 3)]


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


def test_quantity_has_an_upper_limit(user_client, user, make_product, add_to_cart):
    # Huge values used to overflow MySQL's INT column and return 500
    item = add_to_cart(user, make_product(stock_quantity=10**6))

    assert user_client.put(f"/api/cart/items/{item.cart_item_id}", json={"quantity": 3_000_000_000}).status_code == 422
    assert user_client.put(f"/api/cart/items/{item.cart_item_id}", json={"quantity": 100}).status_code == 422
    assert user_client.put(f"/api/cart/items/{item.cart_item_id}", json={"quantity": 99}).status_code == 200


def test_quantity_cannot_exceed_stock(user_client, user, make_product, add_to_cart):
    item = add_to_cart(user, make_product(stock_quantity=3))

    assert user_client.put(f"/api/cart/items/{item.cart_item_id}", json={"quantity": 4}).status_code == 400
    assert user_client.get("/api/cart/items").json()[0]["quantity"] == 1


def test_quantity_above_stock_can_be_lowered(user_client, user, make_product, add_to_cart):
    # Stock fell after the shopper added 3 (another order, or an admin edit)
    item = add_to_cart(user, make_product(stock_quantity=1), quantity=3)

    assert user_client.put(f"/api/cart/items/{item.cart_item_id}", json={"quantity": 2}).status_code == 200
    assert user_client.put(f"/api/cart/items/{item.cart_item_id}", json={"quantity": 3}).status_code == 400
    assert user_client.get("/api/cart/items").json()[0]["quantity"] == 2


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
    # Guests keep their cart in the browser and send it with checkout
    assert client.get("/api/cart/").status_code == 401
    assert client.post("/api/cart/merge", json={"items": []}).status_code == 401


def test_merge_guest_cart_on_login(user_client, user, make_product, add_to_cart):
    shirt = make_product(stock_quantity=10)
    socks = make_product(stock_quantity=10)
    add_to_cart(user, shirt, quantity=2)

    response = user_client.post("/api/cart/merge", json={"items": [
        {"product_id": shirt.product_id, "quantity": 3},
        {"product_id": socks.product_id, "quantity": 1},
    ]})

    assert response.status_code == 200
    quantities = {i["product_id"]: i["quantity"] for i in response.json()["items"]}
    # Adds to the row already in the cart instead of adding another
    assert quantities == {shirt.product_id: 5, socks.product_id: 1}
    assert len(response.json()["items"]) == 2


def test_merge_caps_quantities_and_skips_unavailable_products(user_client, user, make_product, add_to_cart):
    low_stock = make_product(stock_quantity=4)
    plenty = make_product(stock_quantity=500)
    sold_out = make_product(stock_quantity=0)
    inactive = make_product(is_active=False)
    add_to_cart(user, plenty, quantity=90)

    response = user_client.post("/api/cart/merge", json={"items": [
        {"product_id": low_stock.product_id, "quantity": 9},
        {"product_id": plenty.product_id, "quantity": 20},
        {"product_id": sold_out.product_id, "quantity": 1},
        {"product_id": inactive.product_id, "quantity": 1},
        {"product_id": 9999, "quantity": 1},
    ]})

    assert response.status_code == 200
    quantities = {i["product_id"]: i["quantity"] for i in response.json()["items"]}
    assert quantities == {low_stock.product_id: 4, plenty.product_id: MAX_CART_QUANTITY}


def test_merge_rejects_bad_quantities(user_client, make_product):
    product = make_product()

    assert user_client.post("/api/cart/merge", json={"items": [{"product_id": product.product_id, "quantity": 0}]}).status_code == 422
    assert user_client.get("/api/cart/items").json() == []
