"""Money is stored as DECIMAL(10,2) and sent to Stripe in cents. Never do money
arithmetic in float: 19.99 * 3 is 59.970000000000006 in float."""
from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")


def to_decimal(value) -> Decimal:
    """A dollar amount as an exact two-place Decimal. Floats go through str() so
    10.1 becomes 10.10, not 10.0999999999999996447..."""
    if isinstance(value, float):
        value = str(value)
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def to_cents(value) -> int:
    return int(to_decimal(value) * 100)


def from_cents(cents: int) -> Decimal:
    return (Decimal(cents) / 100).quantize(CENT)
