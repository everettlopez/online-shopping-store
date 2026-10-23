from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse

from sqlmodel import select

from conftest import TEST_PASSWORD
from app.models.password_reset import PasswordResetToken
from app.routes.auth import FORGOT_PASSWORD_MESSAGE

NEW_PASSWORD = "brand-new-password"


def request_reset(client, email):
    return client.post("/api/auth/forgot-password", json={"email": email})


def token_from(message):
    """The token in the reset link of a sent password reset email."""
    link = next(word for word in message.text.split() if "/reset-password?" in word)
    return parse_qs(urlparse(link).query)["token"][0]


def reset(client, token, password=NEW_PASSWORD):
    return client.post("/api/auth/reset-password", json={"token": token, "new_password": password})


def login(client, email, password):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def test_forgot_password_emails_a_reset_link(client, user, sent_emails):
    response = request_reset(client, user.email)

    assert response.status_code == 200
    assert response.json() == {"message": FORGOT_PASSWORD_MESSAGE}
    [message] = sent_emails
    assert message.to == user.email
    assert "http://localhost:5173/reset-password?token=" in message.text
    assert token_from(message) in message.html


def test_unknown_email_gets_the_same_answer_and_no_email(client, sent_emails):
    response = request_reset(client, "nobody@example.com")

    assert response.status_code == 200
    assert response.json() == {"message": FORGOT_PASSWORD_MESSAGE}
    assert sent_emails == []


def test_token_is_stored_only_as_a_hash(client, session, user, sent_emails):
    request_reset(client, user.email)

    stored = session.exec(select(PasswordResetToken)).one()
    assert stored.token_hash != token_from(sent_emails[0])
    assert len(stored.token_hash) == 64


def test_reset_link_sets_a_new_password(client, user, sent_emails):
    request_reset(client, user.email)

    response = reset(client, token_from(sent_emails[0]))

    assert response.status_code == 200
    assert login(client, user.email, NEW_PASSWORD).status_code == 200
    assert login(client, user.email, TEST_PASSWORD).status_code == 400


def test_reset_link_works_once(client, user, sent_emails):
    request_reset(client, user.email)
    token = token_from(sent_emails[0])

    assert reset(client, token).status_code == 200
    response = reset(client, token, "another-password")

    assert response.status_code == 400
    assert "invalid or has expired" in response.json()["detail"]
    assert login(client, user.email, NEW_PASSWORD).status_code == 200


def test_expired_reset_link_is_refused(client, session, user, sent_emails):
    request_reset(client, user.email)
    stored = session.exec(select(PasswordResetToken)).one()
    stored.expires_at = datetime.utcnow() - timedelta(seconds=1)
    session.add(stored)
    session.commit()

    assert reset(client, token_from(sent_emails[0])).status_code == 400
    assert login(client, user.email, TEST_PASSWORD).status_code == 200


def test_wrong_token_is_refused(client, user):
    assert reset(client, "not-a-real-token").status_code == 400
    assert login(client, user.email, TEST_PASSWORD).status_code == 200


def test_new_password_must_be_long_enough(client, user, sent_emails):
    request_reset(client, user.email)

    assert reset(client, token_from(sent_emails[0]), "short").status_code == 422


def test_second_request_within_a_minute_sends_nothing(client, user, sent_emails):
    request_reset(client, user.email)
    response = request_reset(client, user.email)

    assert response.json() == {"message": FORGOT_PASSWORD_MESSAGE}
    assert len(sent_emails) == 1


def test_using_a_link_cancels_older_links(client, session, user, sent_emails):
    request_reset(client, user.email)
    # Let the cooldown pass for the first link, then ask again
    first = session.exec(select(PasswordResetToken)).one()
    first.created_at -= timedelta(minutes=5)
    session.add(first)
    session.commit()
    request_reset(client, user.email)
    old_token, new_token = token_from(sent_emails[0]), token_from(sent_emails[1])

    assert reset(client, new_token).status_code == 200
    assert reset(client, old_token, "another-password").status_code == 400


def test_a_new_link_clears_out_spent_ones(client, session, user):
    request_reset(client, user.email)
    expired = session.exec(select(PasswordResetToken)).one()
    expired.created_at -= timedelta(minutes=5)
    expired.expires_at = datetime.utcnow() - timedelta(minutes=1)
    session.add(expired)
    session.commit()
    expired_hash = expired.token_hash

    request_reset(client, user.email)

    session.expire_all()
    hashes = [t.token_hash for t in session.exec(select(PasswordResetToken)).all()]
    assert len(hashes) == 1 and expired_hash not in hashes


def test_account_with_a_reset_link_can_be_deleted(client, auth_headers, session, user):
    user_id = user.user_id
    request_reset(client, user.email)

    response = client.request("DELETE", "/api/auth/me", json={"current_password": TEST_PASSWORD}, headers=auth_headers(user))
    assert response.status_code == 200
    assert session.exec(select(PasswordResetToken).where(PasswordResetToken.user_id == user_id)).all() == []
