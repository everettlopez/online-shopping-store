from sqlmodel import Session as SQLModelSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator
from dotenv import load_dotenv
import os

from app.settings import sql_echo

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

# Logging every statement leaks data into the logs, so it's opt-in (SQL_ECHO=true)
engine = create_engine(
    DATABASE_URL,
    echo=sql_echo(),
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

ALEMBIC_INI = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "alembic.ini")

def ensure_schema_is_current():
    """Stop startup with a clear message when the database hasn't been migrated to the
    latest Alembic revision, instead of failing later on a missing table or column."""
    from alembic.config import Config
    from alembic.runtime.migration import MigrationContext
    from alembic.script import ScriptDirectory

    expected = ScriptDirectory.from_config(Config(ALEMBIC_INI)).get_current_head()

    with engine.connect() as connection:
        current = MigrationContext.configure(connection).get_current_revision()

    if current != expected:
        raise RuntimeError(
            f"Database schema is at revision {current or '(none)'} but the code expects {expected}. "
            "Run `alembic upgrade head` from the project root, then start the server again."
        )

def seed_database():
    # The schema is managed by Alembic (run `alembic upgrade head`); startup only seeds data
    ensure_schema_is_current()

    from app.database.category import database_seed_categories

    with SQLModelSession(engine) as session:
        database_seed_categories(session)

def get_session() -> Generator:
    with SQLModelSession(engine) as session:
        yield session
