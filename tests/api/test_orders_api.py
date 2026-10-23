from sqlmodel import select

from app.models.order import Order, OrderItem
from app.models.product import Product


def test_admin_lists_all_orders(admin_client, make_user, make_product, make_order):
    product = make_product()
    make_order(make_user(), items=[(product, 1)])
    make_order(make_user(), items=[(product, 2)])

    response = admin_client.get("/api/orders/")

    assert response.status_code == 200
    assert [len(o["items"]) for o in response.json()] == [1, 1]
    assert response.json()[1]["items"][0]["product"]["product_id"] == product.product_id


def test_my_orders(user_client, user, make_user, make_order):
    pending = make_order(user)
    make_order(user, status="shipped")
    make_order(make_user())

    assert len(user_client.get("/api/orders/me").json()) == 2
    filtered = user_client.get("/api/orders/me", params={"order_status": "pending"}).json()
    assert [o["order_id"] for o in filtered] == [pending.order_id]


def test_get_order_by_number(user_client, user, make_product, make_order):
    order = make_order(user, items=[(make_product(title="Lamp"), 3)])

    response = user_client.get(f"/api/orders/{order.order_number.upper()}")

    assert response.status_code == 200
    assert response.json()["items"][0]["product"]["title"] == "Lamp"
    assert response.json()["items"][0]["quantity"] == 3
    assert user_client.get("/api/orders/nope").status_code == 404


def test_orders_are_private(client, auth_headers, user, make_user, admin, make_order):
    order = make_order(user)

    assert client.get(f"/api/orders/{order.order_number}", headers=auth_headers(make_user())).status_code == 404
    assert client.get(f"/api/orders/{order.order_number}", headers=auth_headers(admin)).status_code == 200


def test_update_order_status(admin_client, user, make_order):
    order = make_order(user)

    assert admin_client.put(f"/api/orders/{order.order_id}/status", params={"status": "processing"}).status_code == 200
    assert admin_client.get(f"/api/orders/{order.order_number}").json()["status"] == "processing"
    assert admin_client.put(f"/api/orders/{order.order_id}/status", params={"status": "lost"}).status_code == 400
    assert admin_client.put("/api/orders/999/status", params={"status": "processing"}).status_code == 404


def test_update_tracking_marks_order_shipped(admin_client, user, make_order):
    order = make_order(user)
    tracking = {"tracking_number": "1Z999", "tracking_carrier": "UPS", "tracking_url": "https://ups.com/1Z999"}

    assert admin_client.put(f"/api/orders/{order.order_id}/tracking", params=tracking).status_code == 200

    body = admin_client.get(f"/api/orders/{order.order_number}").json()
    assert body["status"] == "shipped"
    assert body["tracking_number"] == "1Z999"
    assert admin_client.put("/api/orders/999/tracking", params=tracking).status_code == 404


def test_update_tracking_emails_the_buyer(admin_client, user, make_order, sent_emails):
    order = make_order(user)
    tracking = {"tracking_number": "1Z999", "tracking_carrier": "UPS", "tracking_url": "https://ups.com/1Z999"}

    admin_client.put(f"/api/orders/{order.order_id}/tracking", params=tracking)

    [message] = sent_emails
    assert message.to == user.email
    assert message.subject == f"Your Online Store order {order.order_number} has shipped"
    assert "1Z999" in message.text


def test_update_tracking_emails_a_guest(admin_client, make_order, sent_emails):
    order = make_order(None)
    tracking = {"tracking_number": "1Z999", "tracking_carrier": "UPS", "tracking_url": "https://ups.com/1Z999"}

    assert admin_client.put(f"/api/orders/{order.order_id}/tracking", params=tracking).status_code == 200

    [message] = sent_emails
    assert message.to == order.email
    # The link opens the order without an account
    assert f"/track/{order.order_number}?token={order.access_token}" in message.text


def test_order_emails_go_to_the_address_on_the_order(admin_client, user, make_order, sent_emails):
    # Recorded at checkout, so a later change of the account's email doesn't matter
    order = make_order(user, email="then@example.com")
    tracking = {"tracking_number": "1Z999", "tracking_carrier": "UPS", "tracking_url": "https://ups.com/1Z999"}

    admin_client.put(f"/api/orders/{order.order_id}/tracking", params=tracking)

    assert [m.to for m in sent_emails] == ["then@example.com"]


# -----------------------------------------
# Tracking without an account
# -----------------------------------------

def test_track_order_with_its_token(client, make_product, make_order):
    order = make_order(None, items=[(make_product(title="Lamp"), 2)], status="shipped", tracking_number="1Z999")

    response = client.get(f"/api/orders/track/{order.order_number.upper()}", params={"token": order.access_token})

    assert response.status_code == 200
    body = response.json()
    assert body["tracking_number"] == "1Z999"
    assert body["items"][0]["product"]["title"] == "Lamp"
    assert body["shipping_address"]["line1"] == "2 Oak Ave"
    assert "access_token" not in body


def test_tracking_works_for_account_orders_too(client, user, make_order):
    order = make_order(user)

    assert client.get(f"/api/orders/track/{order.order_number}", params={"token": order.access_token}).status_code == 200


def test_track_order_needs_the_right_token(client, make_order):
    order = make_order(None)
    tokenless = make_order(None, access_token=None)

    assert client.get(f"/api/orders/track/{order.order_number}").status_code == 404
    assert client.get(f"/api/orders/track/{order.order_number}", params={"token": "wrong"}).status_code == 404
    assert client.get(f"/api/orders/track/{order.order_number}", params={"token": make_order(None).access_token}).status_code == 404
    assert client.get("/api/orders/track/nope", params={"token": order.access_token}).status_code == 404
    assert client.get(f"/api/orders/track/{tokenless.order_number}", params={"token": ""}).status_code == 404


def test_look_up_order_by_number_and_email(client, make_order):
    order = make_order(None)

    response = client.post("/api/orders/lookup", json={"order_number": f" {order.order_number.upper()} ", "email": order.email.upper()})

    assert response.status_code == 200
    assert response.json() == {"order_number": order.order_number, "access_token": order.access_token}


def test_look_up_order_needs_both_to_match(client, make_order):
    order = make_order(None)
    other = make_order(None)
    not_found = "We couldn't find an order with that number and email"

    for body in (
        {"order_number": order.order_number, "email": other.email},
        {"order_number": "nope", "email": order.email},
        {"order_number": other.order_number, "email": order.email},
    ):
        response = client.post("/api/orders/lookup", json=body)
        assert (response.status_code, response.json()["detail"]) == (404, not_found)

    assert client.post("/api/orders/lookup", json={"order_number": "", "email": ""}).status_code == 422


def test_tracking_rejects_non_ascii_input_with_404(client, make_order):
    order = make_order(None)

    assert client.get(f"/api/orders/track/{order.order_number}", params={"token": "tökén"}).status_code == 404
    assert client.post("/api/orders/lookup", json={"order_number": order.order_number, "email": "jösé@example.com"}).status_code == 404


def test_order_listings_leave_out_the_token(admin_client, user, make_order):
    make_order(user)
    make_order(None)

    assert all("access_token" not in o for o in admin_client.get("/api/orders/").json())
    assert all(o["user_id"] is None or o["email"] for o in admin_client.get("/api/orders/").json())


def test_delete_order_restores_stock(admin_client, session, user, make_product, make_order):
    product = make_product(stock_quantity=1)
    order_id = make_order(user, items=[(product, 4)]).order_id

    assert admin_client.delete(f"/api/orders/{order_id}").status_code == 200

    session.expire_all()
    assert session.get(Product, product.product_id).stock_quantity == 5
    assert session.exec(select(Order)).all() == []
    assert session.exec(select(OrderItem)).all() == []
    assert admin_client.delete(f"/api/orders/{order_id}").status_code == 404


def test_admin_order_routes_require_admin(user_client, user, make_order):
    order = make_order(user)

    assert user_client.get("/api/orders/").status_code == 403
    assert user_client.put(f"/api/orders/{order.order_id}/status", params={"status": "shipped"}).status_code == 403
    assert user_client.put(f"/api/orders/{order.order_id}/tracking", params={"tracking_number": "1", "tracking_carrier": "x", "tracking_url": "x"}).status_code == 403
    assert user_client.delete(f"/api/orders/{order.order_id}").status_code == 403


# -----------------------------------------
# Order items
# -----------------------------------------

def test_order_items(user_client, session, user, make_product, make_order):
    order = make_order(user, items=[(make_product(), 2)])
    item = order_item(session, order)
    base = f"/api/orders/{order.order_id}/items"

    assert [i["order_item_id"] for i in user_client.get(base).json()] == [item.order_item_id]
    assert user_client.get(f"{base}/{item.order_item_id}").json()["quantity"] == 2


def test_order_items_are_scoped_to_owner(user_client, session, make_user, make_product, make_order):
    order = make_order(make_user(), items=[(make_product(), 1)])
    item = order_item(session, order)
    base = f"/api/orders/{order.order_id}/items"

    assert user_client.get(base).status_code == 404
    assert user_client.get(f"{base}/{item.order_item_id}").status_code == 404


def test_order_item_must_belong_to_order(user_client, session, user, make_product, make_order):
    product = make_product()
    first = make_order(user, items=[(product, 1)])
    second = make_order(user, items=[(product, 1)])
    other_item = order_item(session, second)

    assert user_client.get(f"/api/orders/{first.order_id}/items/{other_item.order_item_id}").status_code == 404


def order_item(session, order):
    return session.exec(select(OrderItem).where(OrderItem.order_id == order.order_id)).first()
