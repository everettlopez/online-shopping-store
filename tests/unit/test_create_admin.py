import pytest

import app.db.session as db_session
from app.create_admin import main, promote_to_admin
from app.models.user import User


def test_promotes_an_existing_account(session, make_user):
    user_id = make_user().user_id
    email = session.get(User, user_id).email

    assert promote_to_admin(session, f"  {email} ") == f"{email} is now an admin."

    session.expire_all()
    assert session.get(User, user_id).is_admin is True


def test_an_admin_stays_an_admin(session, make_user):
    admin = make_user(is_admin=True)

    assert promote_to_admin(session, admin.email) == f"{admin.email} is already an admin."


def test_unknown_email_is_reported(session):
    with pytest.raises(LookupError, match="Register it on the storefront first"):
        promote_to_admin(session, "nobody@example.com")


def test_command_uses_the_app_database(engine, session, make_user, monkeypatch, capsys):
    user_id = make_user().user_id
    email = session.get(User, user_id).email
    monkeypatch.setattr(db_session, "engine", engine)

    assert main([email]) == 0
    assert "is now an admin" in capsys.readouterr().out

    session.expire_all()
    assert session.get(User, user_id).is_admin is True


def test_command_exits_nonzero_for_unknown_email(engine, monkeypatch, capsys):
    monkeypatch.setattr(db_session, "engine", engine)

    assert main(["nobody@example.com"]) == 1
    assert "No account uses nobody@example.com" in capsys.readouterr().err


def test_command_needs_exactly_one_email(capsys):
    assert main([]) == 2
    assert "Usage" in capsys.readouterr().err
