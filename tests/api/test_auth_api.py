from conftest import TEST_PASSWORD

NEW_USER = {"email": "new@example.com", "password": "pw-123456", "first_name": "New", "last_name": "User"}


def test_register_then_login(client):
    assert client.post("/api/auth/register", json=NEW_USER).status_code == 200

    response = client.post("/api/auth/login", json={"email": NEW_USER["email"], "password": NEW_USER["password"]})

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert "shop_token" in response.headers["set-cookie"]


def test_register_duplicate_email(client, user):
    response = client.post("/api/auth/register", json={**NEW_USER, "email": user.email})

    assert response.status_code == 400


def test_register_invalid_email(client):
    assert client.post("/api/auth/register", json={**NEW_USER, "email": "not-an-email"}).status_code == 422


def test_login_wrong_password(client, user):
    response = client.post("/api/auth/login", json={"email": user.email, "password": "wrong"})

    assert response.status_code == 400


def test_login_unknown_email(client):
    response = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "x"})

    assert response.status_code == 400


def test_logout_clears_cookie(client):
    response = client.post("/api/auth/logout")

    assert response.status_code == 200
    assert 'shop_token=""' in response.headers["set-cookie"]


def test_me(user_client, user):
    body = user_client.get("/api/auth/me").json()

    assert body["email"] == user.email
    assert body["is_admin"] is False
    assert "hashed_password" not in body


def test_update_email(user_client):
    response = user_client.put("/api/auth/me/email", params={"new_email": "changed@example.com"})

    assert response.status_code == 200
    assert response.json()["email"] == "changed@example.com"


def test_update_email_already_taken(user_client, make_user):
    other = make_user()

    assert user_client.put("/api/auth/me/email", params={"new_email": other.email}).status_code == 400


def test_update_password(user_client, user):
    response = user_client.put("/api/auth/me/password", params={"old_password": TEST_PASSWORD, "new_password": "brand-new"})

    assert response.status_code == 200
    assert user_client.post("/api/auth/login", json={"email": user.email, "password": "brand-new"}).status_code == 200
    assert user_client.post("/api/auth/login", json={"email": user.email, "password": TEST_PASSWORD}).status_code == 400


def test_update_password_must_change(user_client):
    response = user_client.put("/api/auth/me/password", params={"old_password": TEST_PASSWORD, "new_password": TEST_PASSWORD})

    assert response.status_code == 400


def test_update_password_wrong_old_password(user_client):
    response = user_client.put("/api/auth/me/password", params={"old_password": "wrong", "new_password": "brand-new"})

    assert response.status_code == 400


def test_delete_account(user_client):
    assert user_client.delete("/api/auth/me").status_code == 200
    assert user_client.get("/api/auth/me").status_code == 404


def test_delete_account_with_addresses_and_cart(user_client, user, make_address, make_product, add_to_cart):
    make_address(user)
    add_to_cart(user, make_product())

    assert user_client.delete("/api/auth/me").status_code == 200
    assert user_client.get("/api/auth/me").status_code == 404


def test_delete_account_with_orders_is_refused(user_client, user, make_order):
    make_order(user)

    assert user_client.delete("/api/auth/me").status_code == 409
    assert user_client.get("/api/auth/me").status_code == 200
