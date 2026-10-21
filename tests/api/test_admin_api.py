from sqlmodel import select

from conftest import TEST_PASSWORD

from app.models.address import Address
from app.models.cart import Cart, CartItem


def test_admin_home(admin_client):
    assert admin_client.get("/api/admin/").status_code == 200


def test_admin_routes_require_admin(client, user, auth_headers):
    assert client.get("/api/admin/users").status_code == 401
    assert client.get("/api/admin/users", headers=auth_headers(user)).status_code == 403


def test_list_users(admin_client, admin, make_user):
    make_user(first_name="Aaron")

    response = admin_client.get("/api/admin/users", params={"sort": "name"})

    assert response.status_code == 200
    assert response.json()["metadata"] == {"count": 2, "sort": "name"}
    assert response.json()["users"][0]["first_name"] == "Aaron"
    assert "hashed_password" not in response.json()["users"][0]


def test_create_user(admin_client):
    response = admin_client.post("/api/admin/users", json={
        "email": "staff@example.com", "password": "pw", "first_name": "Staff", "last_name": "Member", "is_admin": True,
    })

    assert response.status_code == 200
    assert response.json()["is_admin"] is True
    assert admin_client.post("/api/auth/login", json={"email": "staff@example.com", "password": "pw"}).status_code == 200


def test_create_user_duplicate_email(admin_client, user):
    response = admin_client.post("/api/admin/users", json={
        "email": user.email, "password": "pw", "first_name": "A", "last_name": "B",
    })

    assert response.status_code == 409


def test_update_user(admin_client, user):
    response = admin_client.put(f"/api/admin/users/{user.user_id}", json={"first_name": "Renamed", "is_admin": True})

    assert response.status_code == 200
    assert response.json()["first_name"] == "Renamed"
    assert response.json()["is_admin"] is True


def test_update_user_password(admin_client, user):
    assert admin_client.put(f"/api/admin/users/{user.user_id}", json={"password": "reset-pw"}).status_code == 200
    assert admin_client.post("/api/auth/login", json={"email": user.email, "password": "reset-pw"}).status_code == 200


def test_update_user_blank_password_keeps_old_one(admin_client, user):
    assert admin_client.put(f"/api/admin/users/{user.user_id}", json={"password": ""}).status_code == 200
    assert admin_client.post("/api/auth/login", json={"email": user.email, "password": TEST_PASSWORD}).status_code == 200


def test_update_user_email_conflict(admin_client, user, make_user):
    other = make_user()

    assert admin_client.put(f"/api/admin/users/{user.user_id}", json={"email": other.email}).status_code == 409
    assert admin_client.put(f"/api/admin/users/{user.user_id}", json={"email": user.email}).status_code == 200


def test_admin_cannot_remove_own_admin_rights(admin_client, admin):
    assert admin_client.put(f"/api/admin/users/{admin.user_id}", json={"is_admin": False}).status_code == 400


def test_update_missing_user(admin_client):
    assert admin_client.put("/api/admin/users/999", json={"first_name": "X"}).status_code == 404


def test_delete_user_with_cart_and_addresses(admin_client, session, user, make_address, make_product, add_to_cart):
    make_address(user)
    add_to_cart(user, make_product())

    assert admin_client.delete(f"/api/admin/users/{user.user_id}").status_code == 200

    assert session.exec(select(Address)).all() == []
    assert session.exec(select(Cart)).all() == []
    assert session.exec(select(CartItem)).all() == []


def test_delete_user_with_orders_is_refused(admin_client, user, make_order):
    make_order(user)

    assert admin_client.delete(f"/api/admin/users/{user.user_id}").status_code == 409


def test_admin_cannot_delete_self(admin_client, admin):
    assert admin_client.delete(f"/api/admin/users/{admin.user_id}").status_code == 400


def test_delete_missing_user(admin_client):
    assert admin_client.delete("/api/admin/users/999").status_code == 404
