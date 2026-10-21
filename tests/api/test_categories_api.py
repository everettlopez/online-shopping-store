import pytest


def names(response):
    return [c["name"] for c in response.json()["categories"]]


def test_list_categories(client, make_category):
    make_category(name="Women", sort_order=2)
    make_category(name="Men", sort_order=1)

    response = client.get("/api/categories/", params={"sort": "order"})

    assert response.status_code == 200
    assert response.json()["metadata"] == {"count": 2, "sort": "order"}
    assert names(response) == ["Men", "Women"]
    assert names(client.get("/api/categories/", params={"sort": "name"})) == ["Men", "Women"]


def test_get_category(client, make_category):
    category = make_category(name="Jewelry")

    assert client.get(f"/api/categories/{category.category_id}").json()["name"] == "Jewelry"
    assert client.get("/api/categories/999").status_code == 404


def test_create_category_goes_to_end_of_nav(admin_client, make_category):
    make_category(sort_order=7)

    response = admin_client.post("/api/categories/", json={"name": "Sale", "description": "Discounts"})

    assert response.status_code == 200
    assert response.json()["sort_order"] == 8


def test_create_first_category(admin_client):
    assert admin_client.post("/api/categories/", json={"name": "Sale"}).json()["sort_order"] == 1


def test_create_duplicate_category_name_ignores_case(admin_client, make_category):
    make_category(name="Shoes")

    assert admin_client.post("/api/categories/", json={"name": " shoes "}).status_code == 409


def test_update_category(admin_client, make_category):
    category = make_category(name="Old")

    response = admin_client.put(f"/api/categories/{category.category_id}", json={"name": "New", "description": "Updated"})

    assert response.status_code == 200
    assert response.json()["name"] == "New"
    assert response.json()["description"] == "Updated"


def test_update_category_keeping_own_name(admin_client, make_category):
    category = make_category(name="Same")

    assert admin_client.put(f"/api/categories/{category.category_id}", json={"name": "same"}).status_code == 200


def test_update_category_name_conflict(admin_client, make_category):
    make_category(name="Taken")
    category = make_category(name="Other")

    assert admin_client.put(f"/api/categories/{category.category_id}", json={"name": "Taken"}).status_code == 409


def test_update_missing_category(admin_client):
    assert admin_client.put("/api/categories/999", json={"name": "X"}).status_code == 404


def test_reorder_categories(admin_client, make_category):
    a, b, c = make_category(name="A"), make_category(name="B"), make_category(name="C")

    response = admin_client.put("/api/categories/reorder", json={"category_ids": [c.category_id, a.category_id, b.category_id]})

    assert response.status_code == 200
    assert names(response) == ["C", "A", "B"]
    assert [cat["sort_order"] for cat in response.json()["categories"]] == [1, 2, 3]


@pytest.mark.parametrize("pick", [
    lambda ids: ids[:2],                    # missing one
    lambda ids: ids + [ids[0]],             # duplicate
    lambda ids: ids[:2] + [999],            # unknown id
], ids=["missing", "duplicate", "unknown"])
def test_reorder_must_list_every_category_once(admin_client, make_category, pick):
    ids = [make_category().category_id for _ in range(3)]

    assert admin_client.put("/api/categories/reorder", json={"category_ids": pick(ids)}).status_code == 400


def test_delete_category(admin_client, make_category):
    category = make_category()

    assert admin_client.delete(f"/api/categories/{category.category_id}").status_code == 200
    assert admin_client.get(f"/api/categories/{category.category_id}").status_code == 404
    assert admin_client.delete("/api/categories/999").status_code == 404


def test_delete_category_in_use(admin_client, make_category, make_product):
    category = make_category()
    make_product(category=category)

    assert admin_client.delete(f"/api/categories/{category.category_id}").status_code == 409


def test_category_writes_require_admin(client, user, auth_headers, make_category):
    category = make_category()
    requests = [
        ("post", "/api/categories/", {"name": "X"}),
        ("put", f"/api/categories/{category.category_id}", {"name": "X"}),
        ("put", "/api/categories/reorder", {"category_ids": [category.category_id]}),
        ("delete", f"/api/categories/{category.category_id}", None),
    ]

    for method, url, body in requests:
        kwargs = {"json": body} if body is not None else {}
        assert client.request(method, url, **kwargs).status_code == 401
        assert client.request(method, url, headers=auth_headers(user), **kwargs).status_code == 403
