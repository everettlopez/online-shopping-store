ADDRESS = {
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


def test_delete_address(user_client, user, make_address):
    address = make_address(user)

    assert user_client.delete(f"/api/addresses/{address.address_id}").status_code == 200
    assert user_client.get("/api/addresses/").json() == []


def test_cannot_delete_someone_elses_address(user_client, make_user, make_address):
    address = make_address(make_user())

    assert user_client.delete(f"/api/addresses/{address.address_id}").status_code == 404


def test_all_addresses_is_admin_only(client, user, admin, make_address, auth_headers):
    make_address(user)
    make_address(admin)

    assert client.get("/api/addresses/all", headers=auth_headers(user)).status_code == 403
    assert len(client.get("/api/addresses/all", headers=auth_headers(admin)).json()) == 2


def test_addresses_require_login(client):
    assert client.get("/api/addresses/").status_code == 401
    assert client.post("/api/addresses/", json=ADDRESS).status_code == 401
