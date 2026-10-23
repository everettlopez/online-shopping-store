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


def test_server_errors_are_logged_and_alerted(monkeypatch, sent_emails, caplog):
    from fastapi.testclient import TestClient
    from app.main import create_app

    monkeypatch.setenv("ALERT_EMAIL", "owner@shop.example")
    broken_app = create_app()

    @broken_app.get("/api/broken/{item_id}")
    def broken(item_id: int):
        raise RuntimeError("bug in the code")

    client = TestClient(broken_app)
    origin = {"Origin": "http://localhost:5173"}
    responses = [client.get(f"/api/broken/{n}", headers=origin) for n in (1, 2)]

    assert [r.status_code for r in responses] == [500, 500]
    assert responses[0].json() == {"detail": "Something went wrong on our end. Please try again."}
    # The storefront can still read the error
    assert responses[0].headers["access-control-allow-origin"] == "http://localhost:5173"
    # One alert per route, not one per request
    [alert] = sent_emails
    assert alert.subject == "[Online Store alert] The store hit a server error"
    assert "GET /api/broken/{item_id} failed with RuntimeError('bug in the code')" in alert.text
    assert "unhandled error method=GET route=/api/broken/{item_id}" in caplog.text
    assert "Traceback" in caplog.text
