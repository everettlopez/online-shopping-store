"""Shared pytest fixtures.

Every test gets its own empty in-memory SQLite database, wired into the app by
overriding the get_session dependency. Stripe is never called for real: payment
tests monkeypatch the stripe functions they need.
"""
import os

# Must be set before anything imports app.*: the app reads these at import time,
# and values already in the environment win over the developer's .env file.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["STRIPE_SECRET_KEY"] = "sk_test_dummy"
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test_dummy"

import itertools
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from app.main import app
from app.db.session import get_session
from app.auth.core import create_access_token, hash_password
from app.models import address, cart, category, order, product, user  # noqa: F401  (registers every table)
from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.models.address import Address
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem

TEST_PASSWORD = "Password123!"


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # MySQL enforces foreign keys; SQLite only does when asked
    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture
def client(engine):
    def get_test_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session
    # Not used as a context manager, so the startup migration check doesn't run
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def upload_dir(tmp_path, monkeypatch):
    """Send product image uploads to a temp folder instead of app/uploads."""
    monkeypatch.setattr("app.routes.product.UPLOAD_DIR", str(tmp_path))
    return tmp_path


# -----------------------------------------
# Factories
# -----------------------------------------

_counter = itertools.count(1)


def save(session, obj):
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@pytest.fixture
def make_user(session):
    def make_user(is_admin=False, password=TEST_PASSWORD, **fields):
        n = next(_counter)
        defaults = dict(
            email=f"user{n}@example.com",
            first_name=f"First{n}",
            last_name=f"Last{n}",
        )
        return save(session, User(**{**defaults, **fields}, hashed_password=hash_password(password), is_admin=is_admin))
    return make_user


@pytest.fixture
def make_category(session):
    def make_category(**fields):
        n = next(_counter)
        defaults = dict(name=f"Category {n}", sort_order=n)
        return save(session, Category(**{**defaults, **fields}))
    return make_category


@pytest.fixture
def make_product(session, make_category):
    base_time = datetime(2026, 1, 1)

    def make_product(category=None, **fields):
        n = next(_counter)
        category = category or make_category()
        # Explicit, increasing timestamps keep "newest" sorting deterministic
        created_at = base_time + timedelta(minutes=n)
        defaults = dict(
            title=f"Product {n}",
            price=10.0,
            stock_quantity=10,
            is_active=True,
            created_at=created_at,
            updated_at=created_at,
        )
        return save(session, Product(**{**defaults, **fields}, category_id=category.category_id))
    return make_product


@pytest.fixture
def make_address(session):
    def make_address(user, address_type="shipping", **fields):
        defaults = dict(line1="1 Main St", city="Springfield", state="IL", postal_code="62701")
        return save(session, Address(**{**defaults, **fields}, user_id=user.user_id, address_type=address_type))
    return make_address


@pytest.fixture
def add_to_cart(session):
    def add_to_cart(user, product, quantity=1):
        cart = session.exec(select(Cart).where(Cart.user_id == user.user_id)).first() or save(session, Cart(user_id=user.user_id))
        return save(session, CartItem(cart_id=cart.cart_id, product_id=product.product_id, quantity=quantity))
    return add_to_cart


@pytest.fixture
def make_order(session, make_address):
    def make_order(user, items=(), status="pending", **fields):
        """items: (product, quantity) pairs."""
        shipping = make_address(user, "shipping")
        billing = make_address(user, "billing")
        order = save(session, Order(
            user_id=user.user_id,
            first_name=user.first_name,
            last_name=user.last_name,
            shipping_address_id=shipping.address_id,
            billing_address_id=billing.address_id,
            order_number=f"ord{next(_counter):05d}",
            status=status,
            total_amount=sum(p.price * q for p, q in items),
            **fields,
        ))
        for product, quantity in items:
            session.add(OrderItem(
                order_id=order.order_id,
                product_id=product.product_id,
                quantity=quantity,
                unit_price=product.price,
                subtotal=product.price * quantity,
            ))
        session.commit()
        session.refresh(order)
        return order
    return make_order


# -----------------------------------------
# Users and authenticated clients
# -----------------------------------------

def bearer(user):
    return {"Authorization": f"Bearer {create_access_token({'sub': str(user.user_id)})}"}


@pytest.fixture
def auth_headers():
    """auth_headers(user) -> headers that authenticate as that user, for tests
    that act as more than one user with the plain `client`."""
    return bearer


@pytest.fixture
def user(make_user):
    return make_user()


@pytest.fixture
def admin(make_user):
    return make_user(is_admin=True)


@pytest.fixture
def user_client(client, user):
    client.headers.update(bearer(user))
    return client


@pytest.fixture
def admin_client(client, admin):
    client.headers.update(bearer(admin))
    return client
