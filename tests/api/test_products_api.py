import json

import pytest

from sqlmodel import select

from app.models.cart import CartItem


def ids(response):
    return [p["product_id"] for p in response.json()]


def test_list_products_includes_inactive(client, make_product):
    active = make_product()
    inactive = make_product(is_active=False)

    response = client.get("/api/products/")

    assert response.status_code == 200
    assert ids(response) == [active.product_id, inactive.product_id]
    assert response.json()[0]["category"]["category_id"] == active.category_id


def test_active_products(client, make_category, make_product):
    shoes, hats = make_category(), make_category()
    old_shoe = make_product(category=shoes)
    make_product(category=shoes, is_active=False)
    hat = make_product(category=hats)
    new_shoe = make_product(category=shoes)

    assert ids(client.get("/api/products/active")) == [old_shoe.product_id, hat.product_id, new_shoe.product_id]
    assert ids(client.get("/api/products/active", params={"category_id": shoes.category_id})) == [old_shoe.product_id, new_shoe.product_id]
    assert ids(client.get("/api/products/active", params={"sort": "newest", "limit": 2})) == [new_shoe.product_id, hat.product_id]


def test_active_products_rejects_bad_params(client):
    assert client.get("/api/products/active", params={"limit": 0}).status_code == 422
    assert client.get("/api/products/active", params={"limit": 101}).status_code == 422
    assert client.get("/api/products/active", params={"sort": "price"}).status_code == 422


def test_get_product(client, make_product):
    product = make_product(title="Boots")

    assert client.get(f"/api/products/{product.product_id}").json()["title"] == "Boots"
    assert client.get("/api/products/999").status_code == 404


def test_create_product(admin_client, make_category, upload_dir):
    category = make_category()

    response = admin_client.post(
        "/api/products/",
        data={"category_id": category.category_id, "title": "Scarf", "price": "19.99", "stock_quantity": "5", "color": "red"},
        files={"thumbnail": ("scarf.png", b"fake-image", "image/png")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Scarf"
    assert body["price"] == 19.99
    assert body["stock_quantity"] == 5
    assert body["category"]["category_id"] == category.category_id
    # Saved under a random name, never the one the client sent
    assert body["thumbnail"].startswith("http://testserver/uploads/")
    saved_name = body["thumbnail"].rsplit("/uploads/", 1)[1]
    assert saved_name.endswith(".png") and saved_name != "scarf.png"
    assert (upload_dir / saved_name).read_bytes() == b"fake-image"


def test_create_product_without_thumbnail(admin_client, make_category, upload_dir):
    category = make_category()

    response = admin_client.post("/api/products/", data={"category_id": category.category_id, "title": "Belt", "price": "5"})

    assert response.status_code == 200
    assert response.json()["thumbnail"] is None


def test_create_product_unknown_category(admin_client, upload_dir):
    response = admin_client.post("/api/products/", data={"category_id": 999, "title": "X", "price": "1"})

    assert response.status_code == 400


def test_update_product_fields(admin_client, make_category, make_product):
    product = make_product()
    new_category = make_category()

    response = admin_client.put(f"/api/products/{product.product_id}", data={
        "title": "Renamed",
        "price": "42.5",
        "stock_quantity": "3",
        "is_active": "false",
        "category_id": new_category.category_id,
    })

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Renamed"
    assert body["price"] == 42.5
    assert body["stock_quantity"] == 3
    assert body["is_active"] is False
    assert body["category"]["category_id"] == new_category.category_id


def test_price_keeps_exact_cents(admin_client, make_category, upload_dir):
    category = make_category()

    response = admin_client.post("/api/products/", data={"category_id": category.category_id, "title": "X", "price": "19.99"})

    assert response.json()["price"] == 19.99


@pytest.mark.parametrize("price", ["19.999", "-1", "abc"])
def test_price_must_be_dollars_and_cents(admin_client, make_category, make_product, upload_dir, price):
    category = make_category()
    product = make_product()

    assert admin_client.post("/api/products/", data={"category_id": category.category_id, "title": "X", "price": price}).status_code == 422
    assert admin_client.put(f"/api/products/{product.product_id}", data={"price": price}).status_code == 422


def test_create_product_is_active_by_default(admin_client, make_category, upload_dir):
    category = make_category()

    response = admin_client.post("/api/products/", data={"category_id": category.category_id, "title": "X", "price": "1"})

    assert response.status_code == 200
    assert response.json()["is_active"] is True


@pytest.mark.parametrize("value, expected", [("true", True), ("false", False), ("0", False), ("on", True)])
def test_create_product_sets_is_active(admin_client, make_category, upload_dir, value, expected):
    category = make_category()

    response = admin_client.post("/api/products/", data={
        "category_id": category.category_id, "title": "X", "price": "1", "is_active": value,
    })

    assert response.json()["is_active"] is expected


def test_update_without_is_active_keeps_it(admin_client, make_product):
    # A missing bool form field reads as False in FastAPI, which used to deactivate the product
    active = make_product(is_active=True)
    inactive = make_product(is_active=False)

    for product, expected in [(active, True), (inactive, False)]:
        response = admin_client.put(f"/api/products/{product.product_id}", data={"title": "Renamed"})

        assert response.status_code == 200
        assert response.json()["is_active"] is expected


def test_invalid_is_active_is_rejected(admin_client, make_product):
    product = make_product()

    response = admin_client.put(f"/api/products/{product.product_id}", data={"is_active": "maybe"})

    assert response.status_code == 422


def test_update_product_merges_images(admin_client, make_product, upload_dir):
    product = make_product(images=["uploads/existing.png"])

    response = admin_client.put(
        f"/api/products/{product.product_id}",
        data={"images_urls": json.dumps(["https://cdn.example.com/a.png"])},
        files=[("images_files", ("new.png", b"img", "image/png"))],
    )

    assert response.status_code == 200
    existing, uploaded, url = response.json()["images"]
    assert (existing, url) == ("uploads/existing.png", "https://cdn.example.com/a.png")
    # Same absolute form as thumbnails, so the frontend can use either as an <img> src
    assert uploaded.startswith("http://testserver/uploads/") and uploaded.endswith(".png")
    assert (upload_dir / uploaded.rsplit("/", 1)[1]).exists()


def test_image_links_use_public_api_url(admin_client, make_category, make_product, upload_dir, monkeypatch):
    # Behind a proxy the request URL is the internal one, so links come from PUBLIC_API_URL
    monkeypatch.setenv("PUBLIC_API_URL", "https://api.shop.example.com/")
    category = make_category()
    product = make_product()

    created = admin_client.post(
        "/api/products/",
        data={"category_id": category.category_id, "title": "Hat", "price": "5"},
        files={"thumbnail": ("hat.png", b"img", "image/png")},
    ).json()
    updated = admin_client.put(
        f"/api/products/{product.product_id}",
        files=[("images_files", ("side.png", b"img", "image/png"))],
    ).json()

    assert created["thumbnail"].startswith("https://api.shop.example.com/uploads/")
    assert updated["images"][-1].startswith("https://api.shop.example.com/uploads/")


def test_rejected_batch_leaves_no_files(admin_client, make_product, upload_dir):
    product = make_product()

    response = admin_client.put(
        f"/api/products/{product.product_id}",
        files=[
            ("images_files", ("good.png", b"img", "image/png")),
            ("images_files", ("bad.html", b"<script></script>", "text/html")),
        ],
    )

    assert response.status_code == 400
    assert list(upload_dir.iterdir()) == []
    assert admin_client.get(f"/api/products/{product.product_id}").json()["images"] == []


def test_upload_routes_do_not_block_the_event_loop():
    # Plain def routes run in FastAPI's threadpool; async ones would block on file and DB I/O
    import inspect
    from app.routes.product import create_product, update_product

    assert not inspect.iscoroutinefunction(create_product)
    assert not inspect.iscoroutinefunction(update_product)


@pytest.mark.parametrize("filename", ["../../main.py", "page.html", "script.svg", "no-extension"])
def test_upload_rejects_non_images(admin_client, make_category, upload_dir, filename):
    category = make_category()

    response = admin_client.post(
        "/api/products/",
        data={"category_id": category.category_id, "title": "X", "price": "1"},
        files={"thumbnail": (filename, b"<script>alert(1)</script>", "image/png")},
    )

    assert response.status_code == 400
    assert list(upload_dir.iterdir()) == []


def test_upload_cannot_escape_uploads_folder(admin_client, make_product, upload_dir):
    product = make_product()

    response = admin_client.put(
        f"/api/products/{product.product_id}",
        files=[("images_files", ("../../evil.png", b"img", "image/png"))],
    )

    assert response.status_code == 200
    [saved] = list(upload_dir.iterdir())
    assert saved.parent == upload_dir
    assert not (upload_dir.parent / "evil.png").exists()


def test_upload_size_limit(admin_client, make_product, upload_dir, monkeypatch):
    monkeypatch.setattr("app.routes.product.MAX_UPLOAD_BYTES", 10)
    product = make_product()

    response = admin_client.put(
        f"/api/products/{product.product_id}",
        files=[("images_files", ("big.png", b"x" * 11, "image/png"))],
    )

    assert response.status_code == 400
    assert list(upload_dir.iterdir()) == []


def test_images_urls_must_be_a_list_of_strings(admin_client, make_product):
    product = make_product()

    for bad in ["not json", '{"a": 1}', "[1, 2]"]:
        assert admin_client.put(f"/api/products/{product.product_id}", data={"images_urls": bad}).status_code == 400


def test_price_and_stock_cannot_be_negative(admin_client, make_category, make_product, upload_dir):
    category = make_category()
    product = make_product()

    assert admin_client.post("/api/products/", data={"category_id": category.category_id, "title": "X", "price": "-1"}).status_code == 422
    assert admin_client.post("/api/products/", data={"category_id": category.category_id, "title": "X", "price": "1", "stock_quantity": "-3"}).status_code == 422
    assert admin_client.put(f"/api/products/{product.product_id}", data={"price": "-5"}).status_code == 422
    assert admin_client.put(f"/api/products/{product.product_id}", data={"stock_quantity": "-1"}).status_code == 422


def test_update_product_unknown_category(admin_client, make_product):
    product = make_product()

    assert admin_client.put(f"/api/products/{product.product_id}", data={"category_id": 999}).status_code == 400


def test_update_missing_product(admin_client):
    assert admin_client.put("/api/products/999", data={"title": "X"}).status_code == 404


def test_delete_product_removes_it_from_carts(admin_client, session, user, make_product, add_to_cart):
    product = make_product()
    add_to_cart(user, product)

    assert admin_client.delete(f"/api/products/{product.product_id}").status_code == 200
    assert admin_client.get(f"/api/products/{product.product_id}").status_code == 404
    assert session.exec(select(CartItem)).all() == []


def test_delete_product_in_an_order_is_refused(admin_client, user, make_product, make_order):
    product = make_product()
    make_order(user, items=[(product, 1)])

    assert admin_client.delete(f"/api/products/{product.product_id}").status_code == 409


def test_delete_missing_product(admin_client):
    assert admin_client.delete("/api/products/999").status_code == 404


def test_product_writes_require_admin(user_client, make_product):
    product = make_product()

    assert user_client.post("/api/products/", data={"category_id": product.category_id, "title": "X", "price": "1"}).status_code == 403
    assert user_client.put(f"/api/products/{product.product_id}", data={"title": "X"}).status_code == 403
    assert user_client.delete(f"/api/products/{product.product_id}").status_code == 403
