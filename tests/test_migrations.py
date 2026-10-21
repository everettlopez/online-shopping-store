"""The Alembic migrations build the schema the models expect, and the startup check
notices a database that hasn't been migrated."""
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlmodel import SQLModel

import app.db.session as db_session


@pytest.fixture
def database(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'migrations.db'}"
    # alembic/env.py reads DATABASE_URL; the startup check uses app.db.session.engine
    monkeypatch.setenv("DATABASE_URL", url)
    engine = create_engine(url)
    monkeypatch.setattr(db_session, "engine", engine)
    yield engine
    engine.dispose()


def upgrade_to_head():
    command.upgrade(Config(db_session.ALEMBIC_INI), "head")


def test_migrations_create_every_model_table_and_column(database):
    upgrade_to_head()

    inspector = inspect(database)
    for table in SQLModel.metadata.sorted_tables:
        assert inspector.has_table(table.name), table.name
        columns = {c["name"] for c in inspector.get_columns(table.name)}
        assert columns == set(table.columns.keys()), table.name


def test_startup_check_passes_after_upgrade(database):
    upgrade_to_head()

    db_session.ensure_schema_is_current()


def test_startup_check_fails_on_unmigrated_database(database):
    with pytest.raises(RuntimeError, match="alembic upgrade head"):
        db_session.ensure_schema_is_current()


def test_startup_seeds_categories(database):
    upgrade_to_head()

    db_session.seed_database()

    with database.connect() as connection:
        assert connection.exec_driver_sql("SELECT COUNT(*) FROM categories").scalar() > 0
