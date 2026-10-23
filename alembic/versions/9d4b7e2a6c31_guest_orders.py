"""guest orders: optional user and saved addresses, order email and tracking token

Revision ID: 9d4b7e2a6c31
Revises: 072b6f643f76
Create Date: 2026-10-22 18:00:00.000000

"""
import secrets
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '9d4b7e2a6c31'
down_revision: Union[str, Sequence[str], None] = '072b6f643f76'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('orders', sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('orders', sa.Column('access_token', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=True))

    bind = op.get_bind()
    users = sa.table('users', sa.column('user_id'), sa.column('email'))
    orders = sa.table('orders', sa.column('order_id'), sa.column('user_id'), sa.column('email'), sa.column('access_token'))

    # Existing orders were all placed from an account: email the account holder, and
    # give each order its own tracking link
    emails = {u.user_id: u.email for u in bind.execute(sa.select(users))}
    for order in bind.execute(sa.select(orders.c.order_id, orders.c.user_id)).all():
        bind.execute(
            orders.update()
            .where(orders.c.order_id == order.order_id)
            .values(email=emails.get(order.user_id), access_token=secrets.token_urlsafe(32))
        )

    with op.batch_alter_table('orders') as batch:
        # Guests have no account and no saved addresses
        batch.alter_column('user_id', existing_type=sa.Integer(), nullable=True)
        batch.alter_column('shipping_address_id', existing_type=sa.Integer(), nullable=True)
        batch.alter_column('billing_address_id', existing_type=sa.Integer(), nullable=True)
        # One order per Checkout Session, even when the webhook and the success page race
        batch.drop_index('ix_orders_stripe_session_id')
        batch.create_index('ix_orders_stripe_session_id', ['stripe_session_id'], unique=True)
        batch.create_index('ix_orders_access_token', ['access_token'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('orders') as batch:
        batch.drop_index('ix_orders_access_token')
        batch.drop_index('ix_orders_stripe_session_id')
        batch.create_index('ix_orders_stripe_session_id', ['stripe_session_id'], unique=False)
        # Fails if guest orders exist, which can't be given back an owner
        batch.alter_column('billing_address_id', existing_type=sa.Integer(), nullable=False)
        batch.alter_column('shipping_address_id', existing_type=sa.Integer(), nullable=False)
        batch.alter_column('user_id', existing_type=sa.Integer(), nullable=False)
        batch.drop_column('access_token')
        batch.drop_column('email')
