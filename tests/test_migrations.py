"""The Alembic migrations build the schema the models expect, and the startup check
notices a database that hasn't been migrated."""
import json

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


def test_address_snapshot_migration_backfills_existing_rows(database):
    # A database from before addresses had a recipient and orders kept a copy
    command.upgrade(Config(db_session.ALEMBIC_INI), "1ed8406a5e7d")
    with database.begin() as connection:
        connection.exec_driver_sql(
            "INSERT INTO users (user_id, email, hashed_password, first_name, last_name, created_at, is_admin) "
            "VALUES (1, 'a@example.com', 'x', 'Ada', 'Lovelace', '2026-01-01', 0)"
        )
        connection.exec_driver_sql(
            "INSERT INTO addresses (address_id, user_id, line1, city, state, postal_code, address_type, created_at) "
            "VALUES (7, 1, '1 Main St', 'Springfield', 'IL', '62701', 'shipping', '2026-01-01')"
        )
        connection.exec_driver_sql(
            "INSERT INTO orders (order_id, user_id, created_at, updated_at, shipping_address_id, billing_address_id, "
            "order_number, status, order_date, total_amount) "
            "VALUES (1, 1, '2026-01-01', '2026-01-01', 7, 7, 'abc12345', 'placed', '2026-01-01', 10)"
        )

    upgrade_to_head()

    with database.connect() as connection:
        full_name, country = connection.exec_driver_sql("SELECT full_name, country FROM addresses").one()
        shipping, billing = connection.exec_driver_sql("SELECT shipping_address, billing_address FROM orders").one()

    assert (full_name, country) == ("Ada Lovelace", "US")
    assert json.loads(shipping) == json.loads(billing) == {
        "full_name": "Ada Lovelace", "phone": None, "line1": "1 Main St", "line2": None, "city": "Springfield",
        "state": "IL", "postal_code": "62701", "county": None, "country": "US",
    }


def test_migrations_downgrade_and_upgrade_again(database):
    upgrade_to_head()

    command.downgrade(Config(db_session.ALEMBIC_INI), "1ed8406a5e7d")
    assert "full_name" not in {c["name"] for c in inspect(database).get_columns("addresses")}

    upgrade_to_head()
    db_session.ensure_schema_is_current()
