import json

import pytest
import stripe
from sqlmodel import select

from app.models.cart import CartItem
from app.models.order import Order, OrderItem
from app.models.product import Product


def checkout_session(user=None, shipping=None, billing=None, items=None, session_id="cs_test_1", payment_status="paid", amount_total=None):
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
    return {"total_amount": 0, "shipping_address_id": shipping.address_id, "billing_address_id": billing.address_id}


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
    assert call["line_items"][0]["price_data"]["unit_amount"] == 2 * 1999 + 450
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


def test_checkout_session_with_insufficient_stock(user_client, shopper, make_product, add_to_cart, stripe_create):
    user, shipping, billing = shopper
    add_to_cart(user, make_product(title="Rare Coin", stock_quantity=1), quantity=3)

    response = user_client.post("/api/payments/create-checkout-session", json=checkout_body(shipping, billing))

    assert response.status_code == 400
    assert response.json()["detail"] == "Not enough stock for Rare Coin"
    assert stripe_create == []


def test_checkout_session_requires_login(client):
    assert client.post("/api/payments/create-checkout-session", json={"total_amount": 0, "shipping_address_id": 1, "billing_address_id": 1}).status_code == 401


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
    assert body["shipping_address"]["address_id"] == shipping.address_id
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
