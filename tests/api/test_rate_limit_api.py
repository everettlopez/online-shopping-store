import pytest

import app.rate_limit as rate_limit
from app.rate_limit import check_rate_limit

from conftest import TEST_PASSWORD


def bad_login(client, email="nobody@example.com"):
    return client.post("/api/auth/login", json={"email": email, "password": "wrong-password"})


def test_login_is_refused_after_too_many_attempts(client, monkeypatch):
    monkeypatch.setenv("AUTH_RATE_LIMIT_PER_MINUTE", "3")

    assert [bad_login(client).status_code for _ in range(3)] == [400, 400, 400]

    response = bad_login(client)
    assert response.status_code == 429
    assert response.json()["detail"].startswith("Too many attempts")
    assert 1 <= int(response.headers["Retry-After"]) <= 60


def test_a_blocked_client_cant_log_in_even_with_the_right_password(client, user, monkeypatch):
    monkeypatch.setenv("AUTH_RATE_LIMIT_PER_MINUTE", "2")
    bad_login(client, user.email)
    bad_login(client, user.email)

    response = client.post("/api/auth/login", json={"email": user.email, "password": TEST_PASSWORD})

    assert response.status_code == 429


def test_password_routes_share_the_auth_limit(client, monkeypatch):
    monkeypatch.setenv("AUTH_RATE_LIMIT_PER_MINUTE", "2")
    bad_login(client)
    client.post("/api/auth/forgot-password", json={"email": "nobody@example.com"})

    assert client.post("/api/auth/reset-password", json={"token": "x", "new_password": "whatever-123"}).status_code == 429
    assert client.post("/api/auth/register", json={}).status_code == 429


def test_order_lookup_is_limited(client, monkeypatch):
    monkeypatch.setenv("LOOKUP_RATE_LIMIT_PER_MINUTE", "2")
    lookup = {"order_number": "nope", "email": "pat@example.com"}

    assert client.post("/api/orders/lookup", json=lookup).status_code == 404
    assert client.get("/api/orders/track/nope", params={"token": "guess"}).status_code == 404
    assert client.post("/api/orders/lookup", json=lookup).status_code == 429


def test_checkout_is_limited(client, monkeypatch):
    monkeypatch.setenv("CHECKOUT_RATE_LIMIT_PER_MINUTE", "1")

    client.post("/api/payments/create-checkout-session", json={"items": []})

    assert client.post("/api/payments/create-checkout-session", json={"items": []}).status_code == 429


def test_groups_are_counted_separately(client, monkeypatch):
    monkeypatch.setenv("AUTH_RATE_LIMIT_PER_MINUTE", "1")
    bad_login(client)

    assert client.post("/api/orders/lookup", json={"order_number": "nope", "email": "pat@example.com"}).status_code == 404


def test_zero_turns_a_limit_off(client, monkeypatch):
    monkeypatch.setenv("AUTH_RATE_LIMIT_PER_MINUTE", "0")

    assert {bad_login(client).status_code for _ in range(15)} == {400}


def test_other_routes_arent_limited(client, monkeypatch):
    monkeypatch.setenv("AUTH_RATE_LIMIT_PER_MINUTE", "1")
    bad_login(client)

    assert client.get("/api/products/active").status_code == 200
    assert client.post("/api/auth/logout").status_code == 200


def test_clients_are_counted_separately(monkeypatch):
    monkeypatch.setenv("AUTH_RATE_LIMIT_PER_MINUTE", "1")
    check_rate_limit("auth", "10.0.0.1")

    check_rate_limit("auth", "10.0.0.2")
    with pytest.raises(Exception) as refused:
        check_rate_limit("auth", "10.0.0.1")
    assert refused.value.status_code == 429


def test_requests_older_than_a_minute_stop_counting(monkeypatch):
    monkeypatch.setenv("AUTH_RATE_LIMIT_PER_MINUTE", "1")
    now = [1000.0]
    monkeypatch.setattr(rate_limit.time, "monotonic", lambda: now[0])
    check_rate_limit("auth", "10.0.0.1")

    now[0] += 61
    check_rate_limit("auth", "10.0.0.1")


def test_idle_clients_are_forgotten(monkeypatch):
    now = [5000.0]
    monkeypatch.setattr(rate_limit.time, "monotonic", lambda: now[0])
    check_rate_limit("auth", "10.0.0.1")

    now[0] += 120
    check_rate_limit("auth", "10.0.0.2")

    assert ("auth", "10.0.0.1") not in rate_limit._hits
