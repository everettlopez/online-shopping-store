from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt

from app.auth.core import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    get_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.auth.dependencies import admin_required


def test_hash_and_verify_password():
    hashed = hash_password("secret")

    assert hashed != "secret"
    assert verify_password("secret", hashed)
    assert not verify_password("wrong", hashed)


def test_access_token_round_trip():
    token = create_access_token({"sub": "42"})
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    assert payload["sub"] == "42"
    assert "exp" in payload


def test_cookie_token_is_preferred_over_bearer():
    bearer = HTTPAuthorizationCredentials(scheme="Bearer", credentials="from-header")

    assert get_access_token(cookie_token="from-cookie", bearer_token=bearer) == "from-cookie"
    assert get_access_token(cookie_token=None, bearer_token=bearer) == "from-header"


def test_missing_token_is_rejected():
    with pytest.raises(HTTPException) as error:
        get_access_token(cookie_token=None, bearer_token=None)

    assert error.value.status_code == 401


def test_current_user_from_valid_token(session, user):
    token = create_access_token({"sub": str(user.user_id)})

    assert get_current_user(token=token, session=session).user_id == user.user_id


@pytest.mark.parametrize("token", [
    "not-a-jwt",
    create_access_token({"no_sub": "1"}),
    jwt.encode({"sub": "1", "exp": datetime.utcnow() - timedelta(minutes=1)}, SECRET_KEY, algorithm=ALGORITHM),
    jwt.encode({"sub": "1"}, "some-other-secret", algorithm=ALGORITHM),
], ids=["garbage", "no-sub", "expired", "wrong-secret"])
def test_invalid_tokens_are_rejected(session, token):
    with pytest.raises(HTTPException) as error:
        get_current_user(token=token, session=session)

    assert error.value.status_code == 401


def test_token_for_deleted_user_is_rejected(session):
    token = create_access_token({"sub": "999"})

    with pytest.raises(HTTPException) as error:
        get_current_user(token=token, session=session)

    assert error.value.status_code == 404


def test_admin_required(user, admin):
    assert admin_required(admin) is admin

    with pytest.raises(HTTPException) as error:
        admin_required(user)

    assert error.value.status_code == 403


def test_cookie_authenticates_requests(client, user):
    client.cookies.set("shop_token", create_access_token({"sub": str(user.user_id)}))

    assert client.get("/api/auth/me").json()["user_id"] == user.user_id


def test_anonymous_request_to_protected_route(client):
    assert client.get("/api/auth/me").status_code == 401
