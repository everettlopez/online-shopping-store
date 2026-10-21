from datetime import datetime

from sqlmodel import select

from app.database.category import DEFAULT_CATEGORIES, database_get_categories, database_seed_categories
from app.database.products import database_get_product_read, database_get_product_reads
from app.database.users import (
    database_delete_user,
    database_get_user_by_email,
    database_get_user_by_id,
    database_get_users,
    database_user_has_orders,
)
from app.models.address import Address
from app.models.cart import Cart, CartItem
from app.models.category import Category
from app.models.user import User


def test_seed_categories_on_empty_database(session):
    database_seed_categories(session)

    categories = database_get_categories(session, "order")
    assert [c.name for c in categories] == [name for _, name in DEFAULT_CATEGORIES]
    assert [c.sort_order for c in categories] == list(range(1, len(DEFAULT_CATEGORIES) + 1))


def test_seed_categories_is_idempotent(session):
    database_seed_categories(session)
    database_seed_categories(session)

    assert len(session.exec(select(Category)).all()) == len(DEFAULT_CATEGORIES)


def test_seed_categories_leaves_existing_categories_alone(session, make_category):
    make_category(name="Custom")

    database_seed_categories(session)

    assert [c.name for c in session.exec(select(Category)).all()] == ["Custom"]


def test_get_categories_sorting(session, make_category):
    make_category(name="Bravo", sort_order=1)
    make_category(name="Alpha", sort_order=3)
    make_category(name="Charlie", sort_order=2)

    assert [c.name for c in database_get_categories(session, "name")] == ["Alpha", "Bravo", "Charlie"]
    assert [c.name for c in database_get_categories(session, "order")] == ["Bravo", "Charlie", "Alpha"]
    assert [c.name for c in database_get_categories(session, "id")] == ["Bravo", "Alpha", "Charlie"]
    assert len(database_get_categories(session, "unknown")) == 3


def test_get_users_sorting(session, make_user):
    make_user(first_name="Zed", created_at=datetime(2026, 1, 2))
    make_user(first_name="Amy", created_at=datetime(2026, 1, 3))
    make_user(first_name="Max", created_at=datetime(2026, 1, 1))

    assert [u.first_name for u in database_get_users(session, "name")] == ["Amy", "Max", "Zed"]
    assert [u.first_name for u in database_get_users(session, "created_at")] == ["Max", "Zed", "Amy"]
    assert [u.first_name for u in database_get_users(session, "id")] == ["Zed", "Amy", "Max"]
    assert len(database_get_users(session)) == 3


def test_get_user_by_id_and_email(session, user):
    assert database_get_user_by_id(session, user.user_id).email == user.email
    assert database_get_user_by_email(session, user.email).user_id == user.user_id
    assert database_get_user_by_id(session, 999) is None
    assert database_get_user_by_email(session, "nobody@example.com") is None


def test_get_product_reads(session, make_category, make_product):
    category = make_category(name="Shoes")
    first = make_product(category=category)
    second = make_product(category=category)

    reads = database_get_product_reads(session, [first.product_id, second.product_id, 999])

    assert set(reads) == {first.product_id, second.product_id}
    assert reads[first.product_id].category.name == "Shoes"
    assert database_get_product_reads(session, []) == {}
    assert database_get_product_read(session, 999) is None


def test_user_has_orders(session, user, make_user, make_order):
    make_order(user)

    assert database_user_has_orders(session, user.user_id)
    assert not database_user_has_orders(session, make_user().user_id)


def test_delete_user_removes_cart_and_addresses(session, user, make_user, make_address, make_product, add_to_cart):
    other = make_user()
    make_address(user)
    make_address(other)
    add_to_cart(user, make_product())
    add_to_cart(other, make_product())

    database_delete_user(session, user)

    assert session.get(User, user.user_id) is None
    assert session.exec(select(Address)).all()[0].user_id == other.user_id
    assert [c.user_id for c in session.exec(select(Cart)).all()] == [other.user_id]
    assert len(session.exec(select(CartItem)).all()) == 1
