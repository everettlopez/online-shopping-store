import importlib
import pkgutil

import pytest

import app


def test_health_check(client):
    response = client.get("/api")

    assert response.status_code == 200
    assert response.json() == {"message": "API is running"}


def test_every_router_is_mounted(client):
    paths = client.get("/openapi.json").json()["paths"]

    for path in [
        "/api/auth/login",
        "/api/addresses/",
        "/api/orders/",
        "/api/cart/",
        "/api/products/",
        "/api/categories/",
        "/api/admin/users",
        "/api/payments/webhook",
    ]:
        assert path in paths, path


def test_factories_share_the_test_database(user_client, user):
    # A user created through the session fixture is visible to the app
    response = user_client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json()["email"] == user.email


@pytest.mark.parametrize("module", [m.name for m in pkgutil.walk_packages(app.__path__, "app.")])
def test_every_module_imports(module):
    importlib.import_module(module)
