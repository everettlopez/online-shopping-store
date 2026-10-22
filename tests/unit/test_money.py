from decimal import Decimal

import pytest

from app.money import from_cents, to_cents, to_decimal
from app.routes.payments import shipping_cents


def test_float_prices_become_exact_cents():
    # In float, 19.99 * 3 is 59.970000000000006 and 0.1 + 0.2 is 0.30000000000000004
    assert to_cents(19.99) * 3 == 5997
    assert from_cents(to_cents(19.99) * 3) == Decimal("59.97")
    assert to_decimal(0.1) + to_decimal(0.2) == Decimal("0.30")


@pytest.mark.parametrize("value, cents", [(Decimal("10.10"), 1010), ("6.95", 695), (0, 0), (75, 7500), (19.999, 2000)])
def test_to_cents(value, cents):
    assert to_cents(value) == cents


def test_from_cents_keeps_two_places():
    assert from_cents(5) == Decimal("0.05")
    assert str(from_cents(1200)) == "12.00"


@pytest.mark.parametrize("subtotal_cents, expected", [(0, 695), (7499, 695), (7500, 0), (12000, 0)])
def test_shipping_is_free_from_the_threshold(subtotal_cents, expected):
    # conftest pins SHIPPING_FLAT_RATE=6.95 and FREE_SHIPPING_THRESHOLD=75
    assert shipping_cents(subtotal_cents) == expected
