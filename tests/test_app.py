import importlib
import os
import pkgutil

import pytest

import app
from app.db.session import get_session
from app.settings import upload_dir


def test_health_check(client):
    response = client.get("/api")

    assert response.status_code == 200
    assert response.json() == {"message": "API is running"}


def test_health_reports_database_ok(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_reports_database_down(client):
    class BrokenSession:
        def exec(self, statement):
            raise RuntimeError("database is down")

    client.app.dependency_overrides[get_session] = lambda: BrokenSession()

    response = client.get("/api/health")

    assert response.status_code == 503


def test_upload_dir_can_be_moved_to_a_volume(monkeypatch, tmp_path):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))
    assert upload_dir() == str(tmp_path)

    monkeypatch.delenv("UPLOAD_DIR")
    assert upload_dir().endswith(os.path.join("app", "uploads"))


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
