"""Checks that guard the deployment: no routes that skip payment, cross-site
writes blocked, webhooks that can't be forged, secrets kept out of logs, and
configuration that is checked at startup."""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import select

import app.routes.payments as payments
from conftest import TEST_PASSWORD
from app.main import create_app
from app.models.order import Order
from app.settings import check_required_settings


# -----------------------------------------
# Routes that bypassed Stripe Checkout
# -----------------------------------------

@pytest.mark.parametrize("method, url", [
    ("post", "/api/orders/"),
    ("post", "/api/cart/checkout"),
    ("post", "/api/payments/create-payment-intent"),
    ("put", "/api/orders/1/items/1"),
    ("delete", "/api/orders/1/items/1"),
])
def test_routes_that_skip_payment_are_gone(user_client, method, url):
    body = {"total_amount": 0.01, "shipping_address_id": 1, "billing_address_id": 1, "quantity": 1}

    response = user_client.request(method, url, json=body)

    assert response.status_code in (404, 405)


def test_orders_only_come_from_paid_checkout(user_client, session, user, make_address):
    # The only way left to create an order is the Stripe webhook / success page
    address = make_address(user)
    user_client.post("/api/orders/", json={"total_amount": 0.01, "shipping_address_id": address.address_id, "billing_address_id": address.address_id})

    assert session.exec(select(Order)).all() == []


# -----------------------------------------
# Cross-site request forgery
# -----------------------------------------

def test_cross_site_write_is_blocked(admin_client, make_category):
    category = make_category()

    response = admin_client.post(
        "/api/products/",
        data={"category_id": category.category_id, "title": "Planted", "price": "1"},
        headers={"Origin": "https://evil.example"},
    )

    assert response.status_code == 403
    assert admin_client.get("/api/products/").json() == []


def test_frontend_origin_can_write(user_client):
    assert user_client.post("/api/auth/logout", headers={"Origin": "http://localhost:5173"}).status_code == 200


def test_requests_without_origin_can_write(user_client):
    # Stripe's webhook and command-line tools don't send Origin
    assert user_client.post("/api/auth/logout").status_code == 200


def test_cross_site_reads_are_allowed(user_client):
    # CORS already stops other sites from reading the response
    assert user_client.get("/api/auth/me", headers={"Origin": "https://evil.example"}).status_code == 200


# -----------------------------------------
# Stripe webhook
# -----------------------------------------

def test_webhook_refuses_everything_without_a_secret(client, session, monkeypatch):
    monkeypatch.setattr(payments, "WEBHOOK_SECRET", "")
    # Even an event that would verify must not be processed
    monkeypatch.setattr(payments.stripe.Webhook, "construct_event", lambda *args: pytest.fail("should not verify"))

    response = client.post("/api/payments/webhook", content=b"{}", headers={"stripe-signature": "t=1,v1=x"})

    assert response.status_code == 503
    assert session.exec(select(Order)).all() == []


# -----------------------------------------
# Logs
# -----------------------------------------

def test_tokens_are_not_logged(client, user, auth_headers, capsys):
    headers = auth_headers(user)
    client.cookies.set("shop_token", headers["Authorization"].removeprefix("Bearer "))

    client.get("/api/auth/me", headers=headers)

    output = capsys.readouterr()
    assert headers["Authorization"].removeprefix("Bearer ") not in output.out + output.err


def test_sql_is_not_logged_by_default():
    from app.db.session import engine

    assert engine.echo is False


# -----------------------------------------
# Startup configuration check
# -----------------------------------------

def test_valid_settings_pass():
    check_required_settings()


@pytest.mark.parametrize("name, value, problem", [
    ("JWT_SECRET_KEY", "too-short", "JWT_SECRET_KEY"),
    ("JWT_SECRET_KEY", "", "JWT_SECRET_KEY"),
    ("STRIPE_SECRET_KEY", "", "STRIPE_SECRET_KEY"),
    ("STRIPE_WEBHOOK_SECRET", " ", "STRIPE_WEBHOOK_SECRET"),
    ("COOKIE_SAMESITE", "sometimes", "COOKIE_SAMESITE"),
    ("SHIPPING_FLAT_RATE", "-1", "SHIPPING_FLAT_RATE"),
    ("FREE_SHIPPING_THRESHOLD", "free", "FREE_SHIPPING_THRESHOLD"),
    ("PASSWORD_RESET_MINUTES", "0", "PASSWORD_RESET_MINUTES"),
    ("PASSWORD_RESET_MINUTES", "half an hour", "PASSWORD_RESET_MINUTES"),
])
def test_bad_settings_stop_startup(monkeypatch, name, value, problem):
    monkeypatch.setenv(name, value)

    with pytest.raises(RuntimeError, match=problem):
        check_required_settings()


# -----------------------------------------
# Deployment settings
# -----------------------------------------

def test_docs_can_be_turned_off(monkeypatch):
    monkeypatch.setenv("ENABLE_DOCS", "false")
    client = TestClient(create_app())

    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404
    assert client.get("/api").status_code == 200


def test_cors_origins_come_from_settings(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://shop.example.com")
    client = TestClient(create_app())

    allowed = client.options("/api/products/", headers={"Origin": "https://shop.example.com", "Access-Control-Request-Method": "GET"})
    blocked = client.options("/api/products/", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"})

    assert allowed.headers.get("access-control-allow-origin") == "https://shop.example.com"
    assert "access-control-allow-origin" not in blocked.headers
    assert client.post("/api/auth/logout", headers={"Origin": "http://localhost:5173"}).status_code == 403


def test_cookie_settings_come_from_settings(client, user, monkeypatch):
    monkeypatch.setenv("COOKIE_SAMESITE", "lax")
    monkeypatch.setenv("COOKIE_SECURE", "false")

    cookie = client.post("/api/auth/login", json={"email": user.email, "password": TEST_PASSWORD}).headers["set-cookie"].lower()

    assert "samesite=lax" in cookie
    assert "; secure" not in cookie


def test_missing_jwt_secret_gets_a_clear_startup_error(tmp_path):
    # The app used to crash with a bare KeyError on import, before the startup check ran.
    # A fresh interpreter is needed because the key is read when app modules load.
    import os
    import subprocess
    import sys

    # Remove the key entirely, and stop a developer's .env from filling it back in
    env = {k: v for k, v in os.environ.items() if k != "JWT_SECRET_KEY"}
    env["PYTHON_DOTENV_DISABLED"] = "1"
    script = (
        "import app.main\n"
        "from app.settings import check_required_settings\n"
        "check_required_settings()\n"
    )

    result = subprocess.run([sys.executable, "-c", script], cwd=os.getcwd(), env=env, capture_output=True, text=True)

    assert result.returncode != 0
    assert "KeyError" not in result.stderr
    assert "JWT_SECRET_KEY must be at least 32 characters" in result.stderr


def test_tokens_are_never_signed_with_a_weak_key(monkeypatch):
    import app.auth.core as core

    monkeypatch.setattr(core, "SECRET_KEY", "")

    with pytest.raises(RuntimeError):
        core.create_access_token({"sub": "1"})
