"""Login tokens stop working when the password changes or the user logs out everywhere.
Tokens aren't stored, so each carries the user's token_version and must match it."""
from datetime import datetime, timedelta

import jwt
import pytest

from conftest import TEST_PASSWORD
from app.auth.core import ALGORITHM, SECRET_KEY, create_access_token, create_user_token
from app.models.password_reset import PasswordResetToken
from app.routes.auth import hash_reset_token

NEW_PASSWORD = "brand-new-password"


def me(client, token):
    """GET /auth/me with only this token (no cookie)."""
    client.cookies.clear()
    return client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def test_password_change_ends_other_sessions_but_not_this_one(client, user):
    phone = create_user_token(user)
    laptop = client.post("/api/auth/login", json={"email": user.email, "password": TEST_PASSWORD}).json()["access_token"]

    response = client.put("/api/auth/me/password", json={"old_password": TEST_PASSWORD, "new_password": NEW_PASSWORD},
                          headers=bearer(laptop))

    assert response.status_code == 200
    # The browser that changed it gets a new cookie and stays logged in
    fresh = response.json()["access_token"]
    assert response.cookies.get("shop_token") == fresh
    assert me(client, fresh).status_code == 200
    # Every earlier login is over, this browser's old token included
    for old in (phone, laptop):
        ended = me(client, old)
        assert ended.status_code == 401
        assert ended.json()["detail"] == "Your session has ended. Please log in again"


def test_password_reset_ends_every_session(client, session, user):
    stolen = create_user_token(user)
    session.add(PasswordResetToken(user_id=user.user_id, token_hash=hash_reset_token("reset-me"),
                                   created_at=datetime.utcnow(), expires_at=datetime.utcnow() + timedelta(minutes=30)))
    session.commit()

    assert client.post("/api/auth/reset-password", json={"token": "reset-me", "new_password": NEW_PASSWORD}).status_code == 200

    assert me(client, stolen).status_code == 401
    login = client.post("/api/auth/login", json={"email": user.email, "password": NEW_PASSWORD})
    assert me(client, login.json()["access_token"]).status_code == 200


def test_admin_setting_a_password_ends_the_users_sessions(client, auth_headers, user, admin):
    stolen = create_user_token(user)

    assert client.put(f"/api/admin/users/{user.user_id}", json={"password": NEW_PASSWORD}, headers=auth_headers(admin)).status_code == 200

    assert me(client, stolen).status_code == 401


def test_admin_edits_without_a_password_keep_sessions(client, auth_headers, user, admin):
    token = create_user_token(user)

    assert client.put(f"/api/admin/users/{user.user_id}", json={"first_name": "Robin", "password": ""}, headers=auth_headers(admin)).status_code == 200

    assert me(client, token).status_code == 200


def test_log_out_everywhere(client, user):
    phone = create_user_token(user)
    laptop = client.post("/api/auth/login", json={"email": user.email, "password": TEST_PASSWORD}).json()["access_token"]

    response = client.post("/api/auth/logout-all", headers=bearer(laptop))

    assert response.status_code == 200
    # The cookie is cleared (Max-Age=0)
    assert 'shop_token=""' in response.headers["set-cookie"]
    assert me(client, laptop).status_code == 401
    assert me(client, phone).status_code == 401
    # Logging in again works as usual
    login = client.post("/api/auth/login", json={"email": user.email, "password": TEST_PASSWORD})
    assert me(client, login.json()["access_token"]).status_code == 200


def test_log_out_everywhere_needs_a_login(client):
    assert client.post("/api/auth/logout-all").status_code == 401


def test_tokens_from_before_versions_still_work(client, user):
    # Issued before this change: no "ver" claim, which counts as version 0
    legacy = create_access_token({"sub": str(user.user_id)})

    assert me(client, legacy).status_code == 200


def test_other_users_sessions_are_untouched(client, user, make_user):
    other = make_user()
    token = create_user_token(other)

    assert client.post("/api/auth/logout-all", headers=bearer(create_user_token(user))).status_code == 200

    assert me(client, token).status_code == 200


@pytest.mark.parametrize("claims", [
    {"sub": "not-a-number"},
    {"sub": "1", "ver": "x"},
    {"ver": 0},
], ids=["bad-sub", "bad-ver", "no-sub"])
def test_malformed_tokens_are_rejected_not_errors(client, user, claims):
    token = jwt.encode({**claims, "exp": datetime.utcnow() + timedelta(minutes=5)}, SECRET_KEY, algorithm=ALGORITHM)

    assert me(client, token).status_code == 401


def test_tokens_without_an_expiry_are_rejected(client, user):
    forever = jwt.encode({"sub": str(user.user_id), "ver": 0}, SECRET_KEY, algorithm=ALGORITHM)

    assert me(client, forever).status_code == 401
