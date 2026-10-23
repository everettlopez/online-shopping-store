"""Shared pytest fixtures.

Every test gets its own empty in-memory SQLite database, wired into the app by
overriding the get_session dependency. Stripe is never called for real: payment
tests monkeypatch the stripe functions they need. Emails are never sent: the
autouse sent_emails fixture records them instead.
"""
import os

# Must be set before anything imports app.*: the app reads these at import time,
# and values already in the environment win over the developer's .env file.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-that-is-at-least-32-chars"
os.environ["STRIPE_SECRET_KEY"] = "sk_test_dummy"
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test_dummy"
# Pin the deployment settings too, so a developer's .env can't change test results
os.environ["FRONTEND_URL"] = "http://localhost:5173"
os.environ["CORS_ORIGINS"] = "http://localhost:5173,http://127.0.0.1:5173"
os.environ["COOKIE_SAMESITE"] = "none"
os.environ["COOKIE_SECURE"] = "true"
os.environ["ENABLE_DOCS"] = "true"
os.environ["SQL_ECHO"] = "false"
os.environ["SHIPPING_FLAT_RATE"] = "6.95"
os.environ["FREE_SHIPPING_THRESHOLD"] = "75"
os.environ["STRIPE_AUTOMATIC_TAX"] = "true"
os.environ["STRIPE_PRODUCT_TAX_CODE"] = "txcd_30011000"
os.environ["STORE_NAME"] = "Online Store"
os.environ["RESEND_API_KEY"] = ""
os.environ["EMAIL_FROM"] = "Online Store <onboarding@resend.dev>"
os.environ["ORDERS_EMAIL_FROM"] = ""
os.environ["ACCOUNT_EMAIL_FROM"] = ""
os.environ["EMAIL_REPLY_TO"] = ""
os.environ["PASSWORD_RESET_MINUTES"] = "30"

import itertools
from datetime import datetime, timedelta

import pytest
import stripe
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from app.main import app
from app.db.session import get_session
from app.auth.core import create_access_token, hash_password
from app.rate_limit import reset_rate_limits
from app.models import address, cart, category, order, password_reset, product, user  # noqa: F401  (registers every table)
from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.models.address import Address
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem
from app.schemas.address import address_snapshot

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


@pytest.fixture(autouse=True)
def fresh_rate_limits():
    """Every test starts with no requests counted against the rate limits."""
    reset_rate_limits()
    yield
    reset_rate_limits()


@pytest.fixture(autouse=True)
def stripe_customers(monkeypatch):
    """Checkout creates or updates the buyer's Stripe Customer (for Stripe Tax).
    Record those calls instead of reaching Stripe: {"create": [...], "modify": [...]}."""
    calls = {"create": [], "modify": []}

    def create(**kwargs):
        calls["create"].append(kwargs)
        return stripe.Customer.construct_from({"id": f"cus_test_{len(calls['create'])}"}, "sk_test")

    def modify(customer_id, **kwargs):
        calls["modify"].append((customer_id, kwargs))
        return stripe.Customer.construct_from({"id": customer_id}, "sk_test")

    monkeypatch.setattr(stripe.Customer, "create", create)
    monkeypatch.setattr(stripe.Customer, "modify", modify)
    return calls


@pytest.fixture(autouse=True)
def sent_emails(monkeypatch):
    """Record every email the app sends (EmailMessage objects) instead of sending it."""
    sent = []
    monkeypatch.setattr("app.mail.deliver", sent.append)
    return sent


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
        defaults = dict(full_name="Pat Doe", line1="1 Main St", city="Springfield", state="IL", postal_code="62701")
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
        """items: (product, quantity) pairs. user=None makes a guest order, which has
        address copies but no saved addresses."""
        n = next(_counter)
        if user:
            shipping = make_address(user, "shipping")
            billing = make_address(user, "billing")
            owner = dict(
                user_id=user.user_id,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                shipping_address_id=shipping.address_id,
                billing_address_id=billing.address_id,
                shipping_address=address_snapshot(shipping),
                billing_address=address_snapshot(billing),
            )
        else:
            copy = dict(full_name="Guest Shopper", line1="2 Oak Ave", city="Springfield", state="IL", postal_code="62701", country="US")
            owner = dict(first_name="Guest", last_name="Shopper", email=f"guest{n}@example.com",
                         shipping_address=copy, billing_address=copy)
        order = save(session, Order(**{
            **owner,
            "order_number": f"ord{n:05d}",
            "access_token": f"token-{n:05d}",
            "status": status,
            "total_amount": sum(p.price * q for p, q in items),
            **fields,
        }))
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
