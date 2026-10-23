import json
from datetime import datetime
from decimal import Decimal

import pytest
import stripe
from sqlmodel import select

from app.models.cart import CartItem
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user import User


def checkout_session(user=None, shipping=None, billing=None, items=None, session_id="cs_test_1", payment_status="paid",
                     amount_total=None, amount_subtotal=None, total_details=None):
    """A Stripe Checkout Session as the webhook and Session.retrieve hand it over.
    items: (product, quantity) pairs, stored the way create-checkout-session does."""
    metadata = {}
    if user:
        metadata = {
            "user_id": str(user.user_id),
            "shipping_address_id": str(shipping.address_id),
            "billing_address_id": str(billing.address_id),
        }
    if items is not None:
        metadata["items"] = json.dumps([[p.product_id, q, round(p.price * 100)] for p, q in items])

    return stripe.checkout.Session.construct_from({
        "id": session_id,
        "object": "checkout.session",
        "payment_status": payment_status,
        "payment_intent": "pi_test_1",
        "amount_total": amount_total,
        "amount_subtotal": amount_subtotal,
        "total_details": total_details,
        "metadata": metadata,
    }, "sk_test")


@pytest.fixture(autouse=True)
def payment_intent(monkeypatch):
    """Every PaymentIntent lookup returns a paid Visa charge."""
    intent = stripe.PaymentIntent.construct_from({
        "id": "pi_test_1",
        "latest_charge": {
            "id": "ch_test_1",
            "object": "charge",
            "status": "succeeded",
            "receipt_url": "https://pay.stripe.com/receipts/test",
            "payment_method_details": {"type": "card", "card": {"brand": "visa", "last4": "4242"}},
        },
    }, "sk_test")
    monkeypatch.setattr(stripe.PaymentIntent, "retrieve", lambda *args, **kwargs: intent)


@pytest.fixture
def send_webhook(client, monkeypatch):
    """Post an event to the webhook as if Stripe had signed it."""
    def send_webhook(stripe_object, event_type="checkout.session.completed"):
        event = {"type": event_type, "data": {"object": stripe_object}}
        monkeypatch.setattr(stripe.Webhook, "construct_event", lambda payload, sig, secret: event)
        return client.post("/api/payments/webhook", content=b"{}", headers={"stripe-signature": "t=1,v1=test"})
    return send_webhook


@pytest.fixture
def shopper(user, make_address):
    """The user plus their shipping and billing addresses."""
    return user, make_address(user, "shipping"), make_address(user, "billing")


# -----------------------------------------
# POST /payments/create-checkout-session
# -----------------------------------------

@pytest.fixture
def stripe_create(monkeypatch):
    calls = []

    def create(**kwargs):
        calls.append(kwargs)
        return stripe.checkout.Session.construct_from({"id": "cs_test_1", "url": "https://checkout.stripe.com/c/cs_test_1"}, "sk_test")

    monkeypatch.setattr(stripe.checkout.Session, "create", create)
    return calls


def checkout_body(shipping, billing):
    return {"shipping_address_id": shipping.address_id, "billing_address_id": billing.address_id}


def test_create_checkout_session(user_client, shopper, make_product, add_to_cart, stripe_create):
    user, shipping, billing = shopper
    shirt = make_product(price=19.99)
    socks = make_product(price=4.5)
    add_to_cart(user, shirt, quantity=2)
    add_to_cart(user, socks, quantity=1)

    response = user_client.post("/api/payments/create-checkout-session", json=checkout_body(shipping, billing))

    assert response.status_code == 200
    assert response.json() == {"checkoutUrl": "https://checkout.stripe.com/c/cs_test_1"}

    [call] = stripe_create
    # One line per product, priced before tax so Stripe Tax adds it
    assert call["line_items"] == [
        {"price_data": {"currency": "usd", "unit_amount": 1999, "tax_behavior": "exclusive",
                        "product_data": {"name": shirt.title, "tax_code": "txcd_30011000"}}, "quantity": 2},
        {"price_data": {"currency": "usd", "unit_amount": 450, "tax_behavior": "exclusive",
                        "product_data": {"name": socks.title, "tax_code": "txcd_30011000"}}, "quantity": 1},
    ]
    assert call["metadata"]["user_id"] == user.user_id
    assert json.loads(call["metadata"]["items"]) == [[shirt.product_id, 2, 1999], [socks.product_id, 1, 450]]


def test_checkout_session_without_cart_or_items(user_client, shopper, stripe_create):
    user, shipping, billing = shopper

    assert user_client.post("/api/payments/create-checkout-session", json=checkout_body(shipping, billing)).json()["detail"] == "Cart not found"

    user_client.get("/api/cart/")
    assert user_client.post("/api/payments/create-checkout-session", json=checkout_body(shipping, billing)).json()["detail"] == "Cart is empty"
    assert stripe_create == []


def test_checkout_session_with_someone_elses_address(user_client, shopper, make_user, make_address, make_product, add_to_cart, stripe_create):
    user, shipping, billing = shopper
    theirs = make_address(make_user())
    add_to_cart(user, make_product())

    assert user_client.post("/api/payments/create-checkout-session", json=checkout_body(theirs, billing)).status_code == 400
    assert user_client.post("/api/payments/create-checkout-session", json=checkout_body(shipping, theirs)).status_code == 400
    assert stripe_create == []


def test_checkout_session_with_deleted_address(user_client, shopper, make_address, make_product, add_to_cart, stripe_create):
    user, shipping, billing = shopper
    deleted = make_address(user, deleted_at=datetime(2026, 1, 1))
    add_to_cart(user, make_product())

    assert user_client.post("/api/payments/create-checkout-session", json=checkout_body(deleted, billing)).status_code == 400
    assert user_client.post("/api/payments/create-checkout-session", json=checkout_body(shipping, deleted)).status_code == 400
    assert stripe_create == []


def test_checkout_session_with_insufficient_stock(user_client, shopper, make_product, add_to_cart, stripe_create):
    user, shipping, billing = shopper
    add_to_cart(user, make_product(title="Rare Coin", stock_quantity=1), quantity=3)

    response = user_client.post("/api/payments/create-checkout-session", json=checkout_body(shipping, billing))

    assert response.status_code == 400
    assert response.json()["detail"] == "Not enough stock for Rare Coin"
    assert stripe_create == []


def test_checkout_session_rejects_negative_quantity(user_client, shopper, make_product, add_to_cart, stripe_create):
    # 3 shirts plus -2 hats would otherwise lower the total the customer pays
    user, shipping, billing = shopper
    add_to_cart(user, make_product(price=20.0), quantity=3)
    add_to_cart(user, make_product(price=15.0), quantity=-2)

    response = user_client.post("/api/payments/create-checkout-session", json=checkout_body(shipping, billing))

    assert response.status_code == 400
    assert stripe_create == []


def test_checkout_session_rejects_inactive_product(user_client, shopper, make_product, add_to_cart, stripe_create):
    user, shipping, billing = shopper
    add_to_cart(user, make_product(is_active=False))

    assert user_client.post("/api/payments/create-checkout-session", json=checkout_body(shipping, billing)).status_code == 400
    assert stripe_create == []


def test_checkout_session_counts_duplicate_cart_rows_against_stock(user_client, shopper, make_product, add_to_cart, stripe_create):
    user, shipping, billing = shopper
    product = make_product(stock_quantity=2)
    for _ in range(3):
        add_to_cart(user, product, quantity=1)

    assert user_client.post("/api/payments/create-checkout-session", json=checkout_body(shipping, billing)).status_code == 400
    assert stripe_create == []


def test_checkout_snapshot_has_one_entry_per_product(user_client, shopper, make_product, add_to_cart, stripe_create):
    # Older carts can hold a product in several rows; the snapshot must not grow per row,
    # or a normal cart hits Stripe's 500-character metadata limit
    user, shipping, billing = shopper
    product = make_product(price=40.0, stock_quantity=100)
    for _ in range(60):
        add_to_cart(user, product, quantity=1)

    response = user_client.post("/api/payments/create-checkout-session", json=checkout_body(shipping, billing))

    assert response.status_code == 200
    [call] = stripe_create
    assert json.loads(call["metadata"]["items"]) == [[product.product_id, 60, 4000]]
    [line] = call["line_items"]
    assert (line["price_data"]["unit_amount"], line["quantity"]) == (4000, 60)


def shipping_charged(call):
    [option] = call["shipping_options"]
    return option["shipping_rate_data"]["fixed_amount"]["amount"]


@pytest.mark.parametrize("price, expected", [(74.99, 695), (75.00, 0), (120.00, 0)])
def test_checkout_charges_flat_shipping_below_threshold(user_client, shopper, make_product, add_to_cart, stripe_create, price, expected):
    user, shipping, billing = shopper
    add_to_cart(user, make_product(price=price))

    user_client.post("/api/payments/create-checkout-session", json=checkout_body(shipping, billing))

    [call] = stripe_create
    assert shipping_charged(call) == expected
    rate = call["shipping_options"][0]["shipping_rate_data"]
    assert (rate["tax_behavior"], rate["tax_code"]) == ("exclusive", "txcd_92010001")
    assert rate["display_name"] == ("Free shipping" if expected == 0 else "Standard shipping")


def test_shipping_amounts_come_from_settings(user_client, client, shopper, make_product, add_to_cart, stripe_create, monkeypatch):
    monkeypatch.setenv("SHIPPING_FLAT_RATE", "9.50")
    monkeypatch.setenv("FREE_SHIPPING_THRESHOLD", "200")
    user, shipping, billing = shopper
    add_to_cart(user, make_product(price=150.0))

    user_client.post("/api/payments/create-checkout-session", json=checkout_body(shipping, billing))

    assert shipping_charged(stripe_create[0]) == 950
    assert client.get("/api/payments/shipping").json() == {"flat_rate": 9.5, "free_shipping_threshold": 200.0}


def test_checkout_uses_stripe_tax_with_the_buyers_customer(user_client, session, shopper, make_product, add_to_cart, stripe_create, stripe_customers):
    user, shipping, billing = shopper
    add_to_cart(user, make_product())

    user_client.post("/api/payments/create-checkout-session", json=checkout_body(shipping, billing))
    user_client.post("/api/payments/create-checkout-session", json=checkout_body(shipping, billing))

    first, second = stripe_create
    assert first["automatic_tax"] == {"enabled": True}
    assert first["customer"] == second["customer"] == "cus_test_1"

    # Created once, then updated with this checkout's addresses (Stripe Tax uses the shipping one)
    [created] = stripe_customers["create"]
    assert created["email"] == user.email
    assert created["shipping"] == {
        "name": "Pat Doe", "phone": None,
        "address": {"line1": "1 Main St", "line2": None, "city": "Springfield", "state": "IL", "postal_code": "62701", "country": "US"},
    }
    [(customer_id, modified)] = stripe_customers["modify"]
    assert customer_id == "cus_test_1" and modified["shipping"] == created["shipping"]

    session.expire_all()
    assert session.get(User, user.user_id).stripe_customer_id == "cus_test_1"


def test_customer_from_other_stripe_keys_is_replaced(user_client, session, shopper, make_product, add_to_cart, stripe_create, stripe_customers, monkeypatch):
    # A customer id saved with sandbox keys doesn't exist once live keys are in use
    user, shipping, billing = shopper
    user.stripe_customer_id = "cus_from_sandbox"
    session.add(user)
    session.commit()
    add_to_cart(user, make_product())

    def missing(customer_id, **kwargs):
        raise stripe.InvalidRequestError("No such customer", "id")
    monkeypatch.setattr(stripe.Customer, "modify", missing)

    user_client.post("/api/payments/create-checkout-session", json=checkout_body(shipping, billing))

    assert stripe_create[0]["customer"] == "cus_test_1"
    assert len(stripe_customers["create"]) == 1


def test_automatic_tax_can_be_turned_off(user_client, shopper, make_product, add_to_cart, stripe_create, stripe_customers, monkeypatch):
    monkeypatch.setenv("STRIPE_AUTOMATIC_TAX", "false")
    user, shipping, billing = shopper
    add_to_cart(user, make_product())

    user_client.post("/api/payments/create-checkout-session", json=checkout_body(shipping, billing))

    [call] = stripe_create
    assert "automatic_tax" not in call and "customer" not in call
    assert stripe_customers["create"] == []


def test_stripe_errors_become_a_clear_message(user_client, shopper, make_product, add_to_cart, monkeypatch):
    user, shipping, billing = shopper
    add_to_cart(user, make_product())

    def refuse(**kwargs):
        raise stripe.InvalidRequestError("You must have a valid head office address to enable automatic tax", None)
    monkeypatch.setattr(stripe.checkout.Session, "create", refuse)

    response = user_client.post("/api/payments/create-checkout-session", json=checkout_body(shipping, billing))

    assert response.status_code == 502
    assert response.json()["detail"] == "We couldn't start checkout. Please try again in a moment."


def test_checkout_ships_only_within_the_us(user_client, user, make_address, make_product, add_to_cart, stripe_create):
    canadian = make_address(user, country="CA")
    add_to_cart(user, make_product())

    response = user_client.post("/api/payments/create-checkout-session", json=checkout_body(canadian, canadian))

    assert response.status_code == 400
    assert response.json()["detail"] == "We currently ship only within the US"
    assert stripe_create == []


def test_checkout_session_returns_to_configured_frontend(user_client, shopper, make_product, add_to_cart, stripe_create, monkeypatch):
    monkeypatch.setenv("FRONTEND_URL", "https://shop.example.com/")
    user, shipping, billing = shopper
    add_to_cart(user, make_product())

    user_client.post("/api/payments/create-checkout-session", json=checkout_body(shipping, billing))

    [call] = stripe_create
    assert call["success_url"] == "https://shop.example.com/order-success?session_id={CHECKOUT_SESSION_ID}"
    assert call["cancel_url"] == "https://shop.example.com/cart"


# -----------------------------------------
# Guest checkout (no account)
# -----------------------------------------

GUEST_ADDRESS = {"line1": "2 Oak Ave", "line2": None, "city": "Austin", "state": "TX", "postal_code": "78701", "country": "US"}


def guest_checkout_session(items, session_id="cs_test_1", payment_status="paid", email="guest@example.com"):
    """A guest's paid Checkout Session: the email and addresses come from Stripe's page.
    items: (product, quantity) pairs."""
    return stripe.checkout.Session.construct_from({
        "id": session_id,
        "object": "checkout.session",
        "payment_status": payment_status,
        "payment_intent": "pi_test_1",
        "metadata": {"guest": "1", "items": json.dumps([[p.product_id, q, round(p.price * 100)] for p, q in items])},
        "customer_details": {"email": email, "name": "Sam Card", "phone": "+15125550100",
                             "address": {**GUEST_ADDRESS, "line1": "9 Billing Rd"}},
        "collected_information": {"shipping_details": {"name": "Sam Guest", "address": GUEST_ADDRESS}},
    }, "sk_test")


def guest_body(*items):
    return {"items": [{"product_id": p.product_id, "quantity": q} for p, q in items]}


def test_guest_checkout_session(client, make_product, stripe_create, stripe_customers):
    shirt = make_product(price=19.99)
    socks = make_product(price=4.5)

    # A stale or bad login token still checks out as a guest
    response = client.post("/api/payments/create-checkout-session", json=guest_body((shirt, 2), (socks, 1), (shirt, 1)),
                           headers={"Authorization": "Bearer not-a-token"})

    assert response.status_code == 200
    [call] = stripe_create
    # Priced on the server, one line per product
    assert [(i["price_data"]["unit_amount"], i["quantity"]) for i in call["line_items"]] == [(1999, 3), (450, 1)]
    assert call["metadata"] == {"guest": "1", "items": json.dumps([[shirt.product_id, 3, 1999], [socks.product_id, 1, 450]], separators=(",", ":"))}
    # Stripe collects the email and addresses, and taxes from the shipping address
    assert call["shipping_address_collection"] == {"allowed_countries": ["US"]}
    assert call["billing_address_collection"] == "required"
    assert call["phone_number_collection"] == {"enabled": True}
    assert call["automatic_tax"] == {"enabled": True}
    assert "customer" not in call
    assert stripe_customers["create"] == []


def test_logged_in_checkout_ignores_sent_items(user_client, shopper, make_product, add_to_cart, stripe_create):
    user, shipping, billing = shopper
    in_cart = make_product()
    add_to_cart(user, in_cart)

    user_client.post("/api/payments/create-checkout-session", json={**checkout_body(shipping, billing), **guest_body((make_product(), 5))})

    [call] = stripe_create
    assert json.loads(call["metadata"]["items"]) == [[in_cart.product_id, 1, round(in_cart.price * 100)]]
    assert "shipping_address_collection" not in call


def test_guest_checkout_validates_items(client, make_product, stripe_create):
    product = make_product(stock_quantity=2)
    inactive = make_product(is_active=False)

    def checkout(body):
        return client.post("/api/payments/create-checkout-session", json=body)

    assert checkout({}).json()["detail"] == "Cart is empty"
    assert checkout({"items": []}).json()["detail"] == "Cart is empty"
    assert checkout({"shipping_address_id": 1, "billing_address_id": 1}).json()["detail"] == "Cart is empty"
    assert checkout(guest_body((product, 0))).status_code == 422
    assert checkout(guest_body((product, 3))).json()["detail"] == f"Not enough stock for {product.title}"
    assert checkout(guest_body((product, 1), (product, 2))).json()["detail"] == f"Not enough stock for {product.title}"
    assert checkout(guest_body((inactive, 1))).json()["detail"] == f"{inactive.title} is no longer available"
    assert checkout({"items": [{"product_id": 9999, "quantity": 1}]}).json()["detail"] == "Product not found"
    assert stripe_create == []


def test_guest_fulfillment_creates_the_order(send_webhook, session, make_product, sent_emails):
    shirt = make_product(title="Shirt", price=20.0, stock_quantity=5)
    shirt_id = shirt.product_id

    send_webhook(guest_checkout_session([(shirt, 2)]))

    session.expire_all()
    order = session.exec(select(Order)).one()
    assert order.user_id is None and order.shipping_address_id is None and order.billing_address_id is None
    assert order.email == "guest@example.com"
    assert (order.first_name, order.last_name) == ("Sam", "Guest")
    assert order.status == "placed"
    assert order.shipping_address == {"full_name": "Sam Guest", "phone": "+15125550100", "county": None, **GUEST_ADDRESS}
    assert order.billing_address["full_name"] == "Sam Card" and order.billing_address["line1"] == "9 Billing Rd"
    assert len(order.access_token) >= 40
    assert session.get(Product, shirt_id).stock_quantity == 3

    [message] = sent_emails
    assert message.to == "guest@example.com"
    assert f"/track/{order.order_number}?token={order.access_token}" in message.text


def test_guest_fulfillment_reads_older_shipping_details(send_webhook, session, make_product):
    data = guest_checkout_session([(make_product(), 1)]).to_dict()
    data["shipping_details"] = data.pop("collected_information")["shipping_details"]

    send_webhook(stripe.checkout.Session.construct_from(data, "sk_test"))

    assert session.exec(select(Order)).one().shipping_address["full_name"] == "Sam Guest"


def test_guest_fulfillment_happens_once(client, send_webhook, session, make_product, monkeypatch, sent_emails):
    product = make_product(stock_quantity=5)
    product_id = product.product_id
    stripe_session = guest_checkout_session([(product, 1)])
    monkeypatch.setattr(stripe.checkout.Session, "retrieve", lambda session_id: stripe_session)

    client.get("/api/payments/session/cs_test_1")
    send_webhook(stripe_session)
    send_webhook(stripe_session)

    session.expire_all()
    assert len(session.exec(select(Order)).all()) == 1
    assert session.get(Product, product_id).stock_quantity == 4
    assert len(sent_emails) == 1


def test_racing_guest_fulfillment_keeps_the_first_order(session, make_product, monkeypatch):
    """If another fulfillment commits between our check and our insert, the unique
    session id stops a second order and ours is rolled back, stock included."""
    from fastapi import BackgroundTasks
    from app.routes import payments

    product = make_product(stock_quantity=5)
    product_id = product.product_id
    stripe_session = guest_checkout_session([(product, 1)])
    first_id = payments.fulfill_checkout(session, stripe_session, BackgroundTasks()).order_id

    # The "already fulfilled" check misses the committed order, as it would in a race
    real_exec = session.exec
    seen = []

    class NoRow:
        def first(self):
            return None

    def exec_missing_first(statement, *args, **kwargs):
        seen.append(statement)
        return NoRow() if len(seen) == 1 else real_exec(statement, *args, **kwargs)

    monkeypatch.setattr(session, "exec", exec_missing_first)
    second = payments.fulfill_checkout(session, stripe_session, BackgroundTasks())
    monkeypatch.setattr(session, "exec", real_exec)

    session.expire_all()
    assert second.order_id == first_id
    assert len(session.exec(select(Order)).all()) == 1
    assert session.get(Product, product_id).stock_quantity == 4


def test_guest_sees_order_for_session_without_login(client, send_webhook, make_product, monkeypatch):
    send_webhook(guest_checkout_session([(make_product(title="Ring"), 1)]))
    monkeypatch.setattr(stripe.checkout.Session, "retrieve", lambda *args, **kwargs: pytest.fail("should not ask Stripe"))

    response = client.get("/api/payments/session/cs_test_1")

    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] is None and body["email"] == "guest@example.com"
    assert body["items"][0]["product"]["title"] == "Ring"
    # For the success page's tracking link
    assert len(body["access_token"]) >= 40


def test_guest_success_page_fulfills_when_webhook_is_late(client, session, make_product, monkeypatch):
    stripe_session = guest_checkout_session([(make_product(), 1)])
    monkeypatch.setattr(stripe.checkout.Session, "retrieve", lambda session_id: stripe_session)

    response = client.get("/api/payments/session/cs_test_1")

    assert response.status_code == 200 and response.json()["status"] == "placed"
    assert len(session.exec(select(Order)).all()) == 1


def test_unpaid_guest_session_is_not_fulfilled(client, session, make_product, monkeypatch):
    stripe_session = guest_checkout_session([(make_product(), 1)], payment_status="unpaid")
    monkeypatch.setattr(stripe.checkout.Session, "retrieve", lambda session_id: stripe_session)

    assert client.get("/api/payments/session/cs_test_1").status_code == 404
    assert session.exec(select(Order)).all() == []


def test_account_order_for_session_is_hidden_from_guests(client, send_webhook, shopper, make_product, monkeypatch):
    user, shipping, billing = shopper
    stripe_session = checkout_session(user, shipping, billing, items=[(make_product(), 1)])
    monkeypatch.setattr(stripe.checkout.Session, "retrieve", lambda session_id: stripe_session)

    # Not fulfilled for a stranger, and not shown once it exists
    assert client.get("/api/payments/session/cs_test_1").status_code == 404
    send_webhook(stripe_session)
    assert client.get("/api/payments/session/cs_test_1").status_code == 404


def test_account_order_records_its_email_and_token(send_webhook, session, shopper, make_product):
    user, shipping, billing = shopper

    send_webhook(checkout_session(user, shipping, billing, items=[(make_product(), 1)]))

    order = session.exec(select(Order)).one()
    assert order.email == user.email and order.access_token


# -----------------------------------------
# POST /payments/webhook
# -----------------------------------------

def test_webhook_rejects_bad_signature(client, session):
    # The real construct_event runs here and fails on the fake signature
    response = client.post("/api/payments/webhook", content=b"{}", headers={"stripe-signature": "t=1,v1=bad"})

    assert response.status_code == 400
    assert session.exec(select(Order)).all() == []


def test_completed_checkout_creates_order(send_webhook, session, shopper, make_product, add_to_cart):
    user, shipping, billing = shopper
    shirt = make_product(price=20.0, stock_quantity=5)
    hat = make_product(price=15.0, stock_quantity=5)
    add_to_cart(user, shirt, quantity=2)
    add_to_cart(user, hat, quantity=1)

    response = send_webhook(checkout_session(user, shipping, billing, items=[(shirt, 2), (hat, 1)], amount_total=5500))

    assert response.status_code == 200
    [order] = session.exec(select(Order)).all()
    assert order.status == "placed"
    assert order.total_amount == 55.0
    assert order.stripe_session_id == "cs_test_1"
    assert order.first_name == user.first_name
    assert (order.payment_method_type, order.card_brand, order.card_last4) == ("card", "visa", "4242")
    assert order.receipt_url == "https://pay.stripe.com/receipts/test"

    items = session.exec(select(OrderItem)).all()
    assert sorted((i.product_id, i.quantity, i.unit_price, i.subtotal) for i in items) == [
        (shirt.product_id, 2, 20.0, 40.0),
        (hat.product_id, 1, 15.0, 15.0),
    ]

    session.expire_all()
    assert session.get(Product, shirt.product_id).stock_quantity == 3
    assert session.get(Product, hat.product_id).stock_quantity == 4
    assert session.exec(select(CartItem)).all() == []


def test_order_keeps_addresses_as_they_were(send_webhook, session, shopper, make_product, user_client):
    user, shipping, billing = shopper
    send_webhook(checkout_session(user, shipping, billing, items=[(make_product(), 1)]))

    # The customer moves and edits the saved address, then deletes the billing one
    changed = {"full_name": "New Name", "line1": "9 Elm St", "city": "Boise", "state": "ID", "postal_code": "83702", "address_type": "shipping"}
    assert user_client.put(f"/api/addresses/{shipping.address_id}", json=changed).status_code == 200
    assert user_client.delete(f"/api/addresses/{billing.address_id}").status_code == 200

    [order] = user_client.get("/api/orders/me").json()
    assert order["shipping_address"] == {
        "full_name": "Pat Doe", "phone": None, "line1": "1 Main St", "line2": None, "city": "Springfield",
        "state": "IL", "postal_code": "62701", "county": None, "country": "US",
    }
    assert order["billing_address"]["line1"] == "1 Main St"


def test_address_deleted_during_checkout_still_reaches_the_order(send_webhook, session, shopper, make_product):
    user, shipping, billing = shopper
    shipping.deleted_at = datetime(2026, 1, 1)
    session.add(shipping)
    session.commit()

    send_webhook(checkout_session(user, shipping, billing, items=[(make_product(), 1)]))

    [order] = session.exec(select(Order)).all()
    assert order.shipping_address["line1"] == "1 Main St"


def test_order_records_shipping_and_tax_from_stripe(send_webhook, session, shopper, make_product, user_client):
    user, shipping, billing = shopper
    tee = make_product(price=19.99)
    send_webhook(checkout_session(
        user, shipping, billing, items=[(tee, 3)],
        amount_subtotal=5997, amount_total=6407,
        total_details={"amount_discount": 0, "amount_shipping": 0, "amount_tax": 410},
    ))

    [order] = session.exec(select(Order)).all()
    assert (order.subtotal_amount, order.shipping_amount, order.tax_amount, order.total_amount) == (
        Decimal("59.97"), Decimal("0.00"), Decimal("4.10"), Decimal("64.07"),
    )
    [item] = session.exec(select(OrderItem)).all()
    assert (item.unit_price, item.subtotal) == (Decimal("19.99"), Decimal("59.97"))

    shown = user_client.get(f"/api/orders/{order.order_number}").json()
    assert (shown["subtotal_amount"], shown["shipping_amount"], shown["tax_amount"], shown["total_amount"]) == (59.97, 0.0, 4.1, 64.07)


def test_order_shows_the_price_paid_after_the_price_changes(send_webhook, session, shopper, make_product, user_client):
    user, shipping, billing = shopper
    tee = make_product(price=12.50)
    send_webhook(checkout_session(user, shipping, billing, items=[(tee, 2)]))
    tee.price = Decimal("30.00")
    session.add(tee)
    session.commit()

    [order] = user_client.get("/api/orders/me").json()
    [item] = order["items"]
    assert (item["unit_price"], item["subtotal"], item["product"]["price"]) == (12.5, 25.0, 30.0)
    # Sessions without Stripe's breakdown had no shipping or tax
    assert (order["subtotal_amount"], order["shipping_amount"], order["tax_amount"], order["total_amount"]) == (25.0, 0.0, 0.0, 25.0)


def test_completed_checkout_emails_a_confirmation(send_webhook, session, shopper, make_product, sent_emails):
    user, shipping, billing = shopper
    shirt = make_product(title="Shirt", price=20.0)

    send_webhook(checkout_session(user, shipping, billing, items=[(shirt, 2)], amount_subtotal=4000, amount_total=4695,
                                  total_details={"amount_shipping": 695, "amount_tax": 0}))

    order_number = session.exec(select(Order)).one().order_number
    [message] = sent_emails
    assert message.to == user.email
    assert message.subject == f"Online Store order confirmation {order_number}"
    assert "2 x Shirt @ $20.00 = $40.00" in message.text
    assert "Shipping: $6.95" in message.text and "Total: $46.95" in message.text


def test_confirmation_is_sent_once_per_order(client, auth_headers, send_webhook, shopper, make_product, monkeypatch, sent_emails):
    user, shipping, billing = shopper
    product = make_product()
    stripe_session = checkout_session(user, shipping, billing, items=[(product, 1)])
    monkeypatch.setattr(stripe.checkout.Session, "retrieve", lambda session_id: stripe_session)

    # Success page first, then the webhook (twice, as Stripe retries)
    client.get("/api/payments/session/cs_test_1", headers=auth_headers(user))
    send_webhook(stripe_session)
    send_webhook(stripe_session)

    assert len(sent_emails) == 1


def test_unpaid_order_gets_no_confirmation(send_webhook, shopper, make_product, sent_emails):
    user, shipping, billing = shopper

    send_webhook(checkout_session(user, shipping, billing, items=[(make_product(), 1)], payment_status="unpaid"))

    assert sent_emails == []


def test_order_is_kept_when_the_email_fails(send_webhook, session, shopper, make_product, monkeypatch):
    user, shipping, billing = shopper
    def fail(message):
        raise RuntimeError("provider down")
    monkeypatch.setattr("app.mail.deliver", fail)

    response = send_webhook(checkout_session(user, shipping, billing, items=[(make_product(), 1)]))

    assert response.status_code == 200
    assert session.exec(select(Order)).one().status == "placed"


def test_webhook_is_idempotent(send_webhook, session, shopper, make_product, add_to_cart):
    user, shipping, billing = shopper
    product = make_product(stock_quantity=5)
    add_to_cart(user, product, quantity=1)
    stripe_session = checkout_session(user, shipping, billing, items=[(product, 1)])

    send_webhook(stripe_session)
    send_webhook(stripe_session)

    assert len(session.exec(select(Order)).all()) == 1
    session.expire_all()
    assert session.get(Product, product.product_id).stock_quantity == 4


def test_items_added_after_checkout_stay_in_cart(send_webhook, session, shopper, make_product, add_to_cart):
    user, shipping, billing = shopper
    bought = make_product()
    later = make_product()
    add_to_cart(user, bought, quantity=3)  # 2 paid for, 1 more added afterwards
    add_to_cart(user, later, quantity=1)

    send_webhook(checkout_session(user, shipping, billing, items=[(bought, 2)]))

    remaining = {i.product_id: i.quantity for i in session.exec(select(CartItem)).all()}
    assert remaining == {bought.product_id: 1, later.product_id: 1}


def test_oversold_product_stock_stops_at_zero(send_webhook, session, shopper, make_product):
    user, shipping, billing = shopper
    product = make_product(stock_quantity=1)

    send_webhook(checkout_session(user, shipping, billing, items=[(product, 3)]))

    session.expire_all()
    assert session.get(Product, product.product_id).stock_quantity == 0
    assert session.exec(select(OrderItem)).first().quantity == 3


def test_session_without_snapshot_uses_cart(send_webhook, session, shopper, make_product, add_to_cart):
    # Sessions created before the items snapshot existed fall back to the cart
    user, shipping, billing = shopper
    product = make_product(price=8.0)
    add_to_cart(user, product, quantity=2)

    send_webhook(checkout_session(user, shipping, billing))

    order = session.exec(select(Order)).one()
    assert order.total_amount == 16.0
    assert session.exec(select(OrderItem)).one().quantity == 2


def test_unpaid_session_creates_pending_order(send_webhook, session, shopper, make_product):
    user, shipping, billing = shopper
    product = make_product()

    send_webhook(checkout_session(user, shipping, billing, items=[(product, 1)], payment_status="unpaid"))

    assert session.exec(select(Order)).one().status == "pending"


def test_session_without_order_metadata_is_ignored(send_webhook, session):
    response = send_webhook(checkout_session())

    assert response.status_code == 200
    assert session.exec(select(Order)).all() == []


def test_other_event_types_are_ignored(send_webhook, session, shopper, make_product):
    user, shipping, billing = shopper

    response = send_webhook(checkout_session(user, shipping, billing, items=[(make_product(), 1)]), event_type="payment_intent.created")

    assert response.status_code == 200
    assert session.exec(select(Order)).all() == []


# -----------------------------------------
# GET /payments/session/{session_id}
# -----------------------------------------

def test_buyer_sees_order_for_session(client, auth_headers, send_webhook, shopper, make_product):
    user, shipping, billing = shopper
    product = make_product(title="Ring")
    send_webhook(checkout_session(user, shipping, billing, items=[(product, 1)]))

    response = client.get("/api/payments/session/cs_test_1", headers=auth_headers(user))

    assert response.status_code == 200
    body = response.json()
    assert body["stripe_session_id"] == "cs_test_1"
    assert body["shipping_address"]["line1"] == shipping.line1
    assert body["shipping_address"]["full_name"] == shipping.full_name
    assert body["items"][0]["product"]["title"] == "Ring"


def test_order_for_session_is_private(client, auth_headers, send_webhook, shopper, make_user, admin, make_product, monkeypatch):
    user, shipping, billing = shopper
    send_webhook(checkout_session(user, shipping, billing, items=[(make_product(), 1)]))
    monkeypatch.setattr(stripe.checkout.Session, "retrieve", lambda *args, **kwargs: pytest.fail("should not ask Stripe"))

    assert client.get("/api/payments/session/cs_test_1", headers=auth_headers(make_user())).status_code == 404
    assert client.get("/api/payments/session/cs_test_1", headers=auth_headers(admin)).status_code == 200


def test_success_page_fulfills_when_webhook_is_late(client, auth_headers, session, shopper, make_product, monkeypatch):
    user, shipping, billing = shopper
    product = make_product()
    stripe_session = checkout_session(user, shipping, billing, items=[(product, 1)])
    monkeypatch.setattr(stripe.checkout.Session, "retrieve", lambda session_id: stripe_session)

    response = client.get("/api/payments/session/cs_test_1", headers=auth_headers(user))

    assert response.status_code == 200
    assert response.json()["status"] == "placed"
    assert len(session.exec(select(Order)).all()) == 1


@pytest.mark.parametrize("payment_status, viewer_is_buyer", [("unpaid", True), ("paid", False)], ids=["unpaid", "not-the-buyer"])
def test_success_page_does_not_fulfill(client, auth_headers, session, shopper, make_user, make_product, monkeypatch, payment_status, viewer_is_buyer):
    user, shipping, billing = shopper
    stripe_session = checkout_session(user, shipping, billing, items=[(make_product(), 1)], payment_status=payment_status)
    monkeypatch.setattr(stripe.checkout.Session, "retrieve", lambda session_id: stripe_session)
    viewer = user if viewer_is_buyer else make_user()

    assert client.get("/api/payments/session/cs_test_1", headers=auth_headers(viewer)).status_code == 404
    assert session.exec(select(Order)).all() == []


def test_unknown_session(user_client, monkeypatch):
    def fail(session_id):
        raise stripe.error.InvalidRequestError("No such checkout.session", "id")

    monkeypatch.setattr(stripe.checkout.Session, "retrieve", fail)

    assert user_client.get("/api/payments/session/cs_missing").status_code == 404


# -----------------------------------------
# Slow-settling payments (bank debits and the like)
# -----------------------------------------

def test_settled_payment_places_the_order_and_confirms_once(send_webhook, session, shopper, make_product, sent_emails):
    user, shipping, billing = shopper
    product = make_product(title="Shirt")

    send_webhook(checkout_session(user, shipping, billing, items=[(product, 1)], payment_status="unpaid"))
    assert session.exec(select(Order)).one().status == "pending"
    assert sent_emails == []

    settled = checkout_session(user, shipping, billing, items=[(product, 1)])
    send_webhook(settled, event_type="checkout.session.async_payment_succeeded")
    send_webhook(settled, event_type="checkout.session.async_payment_succeeded")

    session.expire_all()
    order = session.exec(select(Order)).one()
    assert order.status == "placed"
    assert order.payment_status == "succeeded"
    [message] = sent_emails
    assert "order confirmation" in message.subject and "1 x Shirt" in message.text


def test_settled_payment_arriving_first_creates_the_order(send_webhook, session, shopper, make_product, sent_emails):
    user, shipping, billing = shopper
    product = make_product(stock_quantity=3)

    send_webhook(checkout_session(user, shipping, billing, items=[(product, 1)]), event_type="checkout.session.async_payment_succeeded")
    # The completed event shows up afterwards, from before the payment settled
    send_webhook(checkout_session(user, shipping, billing, items=[(product, 1)], payment_status="unpaid"))

    session.expire_all()
    assert session.exec(select(Order)).one().status == "placed"
    assert session.get(Product, product.product_id).stock_quantity == 2
    assert len(sent_emails) == 1


def test_failed_payment_cancels_the_order_and_restocks(send_webhook, session, shopper, make_product, sent_emails):
    user, shipping, billing = shopper
    product = make_product(stock_quantity=3)
    unpaid = checkout_session(user, shipping, billing, items=[(product, 2)], payment_status="unpaid")

    send_webhook(unpaid)
    session.expire_all()
    assert session.get(Product, product.product_id).stock_quantity == 1

    send_webhook(unpaid, event_type="checkout.session.async_payment_failed")
    send_webhook(unpaid, event_type="checkout.session.async_payment_failed")

    session.expire_all()
    order = session.exec(select(Order)).one()
    assert order.status == "cancelled"
    assert order.restocked_at is not None
    assert session.get(Product, product.product_id).stock_quantity == 3
    assert sent_emails == []


def test_failed_payment_arriving_first_leaves_stock_alone(send_webhook, session, shopper, make_product):
    user, shipping, billing = shopper
    product = make_product(stock_quantity=3)
    unpaid = checkout_session(user, shipping, billing, items=[(product, 2)], payment_status="unpaid")

    send_webhook(unpaid, event_type="checkout.session.async_payment_failed")
    send_webhook(unpaid)

    session.expire_all()
    assert session.exec(select(Order)).one().status == "cancelled"
    assert session.get(Product, product.product_id).stock_quantity == 3


# -----------------------------------------
# Refunds made in Stripe (charge.refunded)
# -----------------------------------------

def refunded_charge(amount_refunded, payment_intent="pi_test_1"):
    return stripe.Charge.construct_from({
        "id": "ch_test_1",
        "object": "charge",
        "payment_intent": payment_intent,
        "amount_refunded": amount_refunded,
    }, "sk_test")


@pytest.fixture
def paid_order(send_webhook, session, shopper, make_product):
    """A paid $40 order for two $20 shirts, leaving 3 in stock."""
    user, shipping, billing = shopper
    product = make_product(title="Shirt", price=20.0, stock_quantity=5)
    send_webhook(checkout_session(user, shipping, billing, items=[(product, 2)]))
    return session.exec(select(Order)).one(), product.product_id


def test_dashboard_refund_in_full_refunds_and_restocks(send_webhook, session, paid_order, sent_emails):
    order, product_id = paid_order
    sent_emails.clear()

    send_webhook(refunded_charge(4000), event_type="charge.refunded")
    send_webhook(refunded_charge(4000), event_type="charge.refunded")

    session.expire_all()
    order = session.get(Order, order.order_id)
    assert (order.status, order.refunded_amount) == ("refunded", Decimal("40.00"))
    assert order.refunded_at is not None
    assert session.get(Product, product_id).stock_quantity == 5
    [message] = sent_emails
    assert "refund" in message.subject and "$40.00" in message.text


def test_dashboard_partial_refunds_add_up(send_webhook, session, paid_order, sent_emails):
    order, product_id = paid_order
    sent_emails.clear()

    send_webhook(refunded_charge(1000), event_type="charge.refunded")
    session.expire_all()
    first = session.get(Order, order.order_id)
    assert (first.status, first.refunded_amount) == ("placed", Decimal("10.00"))
    assert session.get(Product, product_id).stock_quantity == 3

    # Stripe sends the charge's running total
    send_webhook(refunded_charge(4000), event_type="charge.refunded")
    session.expire_all()
    assert session.get(Order, order.order_id).status == "refunded"
    assert session.get(Product, product_id).stock_quantity == 5
    assert ["$10.00" in m.text for m in sent_emails] == [True, False]
    assert "$30.00" in sent_emails[1].text


def test_refund_button_then_webhook_counts_once(admin_client, send_webhook, session, paid_order, sent_emails, monkeypatch):
    order, product_id = paid_order
    sent_emails.clear()
    monkeypatch.setattr(stripe.Refund, "create", lambda **kwargs: stripe.Refund.construct_from({"id": "re_1"}, "sk_test"))

    # The admin keeps the items out of stock (say they came back damaged)
    assert admin_client.post(f"/api/orders/{order.order_id}/refund", json={"restock": False}).status_code == 200
    send_webhook(refunded_charge(4000), event_type="charge.refunded")

    session.expire_all()
    assert session.get(Order, order.order_id).refunded_amount == Decimal("40.00")
    assert session.get(Product, product_id).stock_quantity == 3
    assert len(sent_emails) == 1


def test_refund_for_an_unknown_payment_is_ignored(send_webhook, session):
    response = send_webhook(refunded_charge(500, payment_intent="pi_unknown"), event_type="charge.refunded")

    assert response.status_code == 200
    assert session.exec(select(Order)).all() == []


def test_refund_without_a_payment_intent_matches_no_order(send_webhook, session, user, make_order):
    # Orders from before payments were recorded have no payment intent either
    order_id = make_order(user, status="placed").order_id

    send_webhook(refunded_charge(500, payment_intent=None), event_type="charge.refunded")

    session.expire_all()
    assert session.get(Order, order_id).refunded_amount == 0
