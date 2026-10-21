from datetime import datetime

import pytest

from app.models.address import Address


ADDRESS = {
    "full_name": "Sam Rivera",
    "phone": "512-555-0100",
    "line1": "500 Market St",
    "line2": "Apt 2",
    "city": "Austin",
    "state": "TX",
    "postal_code": "73301",
    "county": "Travis",
    "address_type": "shipping",
}


def test_create_and_list_addresses(user_client, user):
    created = user_client.post("/api/addresses/", json=ADDRESS)

    assert created.status_code == 200
    assert created.json()["user_id"] == user.user_id
    assert created.json()["full_name"] == "Sam Rivera"
    assert created.json()["phone"] == "512-555-0100"
    assert created.json()["country"] == "US"   # the default

    listed = user_client.get("/api/addresses/").json()
    assert [a["address_id"] for a in listed] == [created.json()["address_id"]]


def test_address_type_must_be_shipping_or_billing(user_client):
    assert user_client.post("/api/addresses/", json={**ADDRESS, "address_type": "vacation"}).status_code == 422


def test_filter_addresses_by_type(user_client, user, make_address):
    make_address(user, "shipping")
    make_address(user, "billing")

    assert [a["address_type"] for a in user_client.get("/api/addresses/", params={"address_type": "billing"}).json()] == ["billing"]
    assert [a["address_type"] for a in user_client.get("/api/addresses/", params={"address_type": "shipping"}).json()] == ["shipping"]
    assert len(user_client.get("/api/addresses/").json()) == 2


def test_other_users_addresses_are_hidden(user_client, make_user, make_address):
    make_address(make_user())

    assert user_client.get("/api/addresses/").json() == []


def test_update_address(user_client, user, make_address):
    address = make_address(user)

    response = user_client.put(f"/api/addresses/{address.address_id}", json={**ADDRESS, "city": "Dallas"})

    assert response.status_code == 200
    assert response.json()["city"] == "Dallas"


def test_cannot_update_someone_elses_address(user_client, make_user, make_address):
    address = make_address(make_user())

    assert user_client.put(f"/api/addresses/{address.address_id}", json=ADDRESS).status_code == 404
    assert user_client.put("/api/addresses/999", json=ADDRESS).status_code == 404


@pytest.mark.parametrize("field", ["full_name", "line1", "city", "state", "postal_code"])
def test_required_address_fields(user_client, field):
    assert user_client.post("/api/addresses/", json={**ADDRESS, field: ""}).status_code == 422
    assert user_client.post("/api/addresses/", json={k: v for k, v in ADDRESS.items() if k != field}).status_code == 422


@pytest.mark.parametrize("country, status", [("CA", 200), ("ca", 422), ("USA", 422)])
def test_country_is_a_two_letter_code(user_client, country, status):
    assert user_client.post("/api/addresses/", json={**ADDRESS, "country": country}).status_code == status


def test_delete_address(user_client, user, make_address, session):
    address = make_address(user)
    address_id = address.address_id

    assert user_client.delete(f"/api/addresses/{address_id}").status_code == 200
    assert user_client.get("/api/addresses/").json() == []

    # Hidden, not removed: orders and checkouts in progress still point at the row
    session.expire_all()
    assert session.get(Address, address_id).deleted_at is not None


def test_deleted_address_cannot_be_edited_or_deleted_again(user_client, user, make_address):
    address = make_address(user, deleted_at=datetime(2026, 1, 1))

    assert user_client.put(f"/api/addresses/{address.address_id}", json=ADDRESS).status_code == 404
    assert user_client.delete(f"/api/addresses/{address.address_id}").status_code == 404


def test_deleting_an_address_keeps_it_on_orders(user_client, user, make_order):
    order = make_order(user)

    assert user_client.delete(f"/api/addresses/{order.shipping_address_id}").status_code == 200

    shown = user_client.get(f"/api/orders/{order.order_number}").json()["shipping_address"]
    assert shown["line1"] == "1 Main St" and shown["full_name"] == "Pat Doe"


def test_cannot_delete_someone_elses_address(user_client, make_user, make_address):
    address = make_address(make_user())

    assert user_client.delete(f"/api/addresses/{address.address_id}").status_code == 404


def test_all_addresses_is_admin_only(client, user, admin, make_address, auth_headers):
    make_address(user)
    make_address(admin)
    make_address(user, deleted_at=datetime(2026, 1, 1))

    assert client.get("/api/addresses/all", headers=auth_headers(user)).status_code == 403
    assert len(client.get("/api/addresses/all", headers=auth_headers(admin)).json()) == 2


def test_addresses_require_login(client):
    assert client.get("/api/addresses/").status_code == 401
    assert client.post("/api/addresses/", json=ADDRESS).status_code == 401
