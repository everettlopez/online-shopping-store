"""exact money columns, order shipping and tax amounts, stripe customer id

Revision ID: 5b8e2f4c9a17
Revises: c3f9a1d2b7e4
Create Date: 2026-10-22 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '5b8e2f4c9a17'
down_revision: Union[str, Sequence[str], None] = 'c3f9a1d2b7e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


MONEY = sa.Numeric(precision=10, scale=2)

# (table, column) pairs that held money as FLOAT; MySQL's FLOAT is single precision,
# so 19.99 was stored as 19.9899997... Converting to DECIMAL rounds it back to cents
FLOAT_MONEY_COLUMNS = [
    ('products', 'price'),
    ('orders', 'total_amount'),
    ('order_items', 'unit_price'),
    ('order_items', 'subtotal'),
]


def upgrade() -> None:
    """Upgrade schema."""
    for table, column in FLOAT_MONEY_COLUMNS:
        with op.batch_alter_table(table) as batch:
            batch.alter_column(column, existing_type=sa.Float(), type_=MONEY, existing_nullable=False)

    op.add_column('orders', sa.Column('subtotal_amount', MONEY, nullable=True))
    op.add_column('orders', sa.Column('shipping_amount', MONEY, nullable=True))
    op.add_column('orders', sa.Column('tax_amount', MONEY, nullable=True))
    op.add_column('users', sa.Column('stripe_customer_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True))

    # Orders so far charged neither shipping nor tax: the whole total was the items
    op.execute("UPDATE orders SET subtotal_amount = total_amount, shipping_amount = 0, tax_amount = 0")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('users') as batch:
        batch.drop_column('stripe_customer_id')
    with op.batch_alter_table('orders') as batch:
        batch.drop_column('tax_amount')
        batch.drop_column('shipping_amount')
        batch.drop_column('subtotal_amount')

    for table, column in FLOAT_MONEY_COLUMNS:
        with op.batch_alter_table(table) as batch:
            batch.alter_column(column, existing_type=MONEY, type_=sa.Float(), existing_nullable=False)
