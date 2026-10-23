"""Make an existing account an admin, for a new store's first admin (after that,
admins manage each other from the admin Users page).

Register the account on the storefront first, then run from the project root:

    python -m app.create_admin owner@example.com

or, in the production container:

    docker exec <api container> python -m app.create_admin owner@example.com
"""
import sys

from sqlmodel import Session

from app.database.users import database_get_user_by_email


def promote_to_admin(session: Session, email: str) -> str:
    """Make the account with this email an admin. Returns a message for the operator;
    raises LookupError when no account uses the email."""
    user = database_get_user_by_email(session, email.strip())
    if not user:
        raise LookupError(f"No account uses {email}. Register it on the storefront first, then run this again.")

    if user.is_admin:
        return f"{user.email} is already an admin."

    user.is_admin = True
    session.add(user)
    session.commit()
    return f"{user.email} is now an admin."


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("Usage: python -m app.create_admin <email>", file=sys.stderr)
        return 2

    # Imported here so the usage message works without a configured database
    from app.db.session import engine

    with Session(engine) as session:
        try:
            print(promote_to_admin(session, argv[0]))
        except LookupError as e:
            print(e, file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
