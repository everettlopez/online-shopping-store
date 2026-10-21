"""order address snapshots and address recipient fields

Revision ID: c3f9a1d2b7e4
Revises: 1ed8406a5e7d
Create Date: 2026-10-22 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'c3f9a1d2b7e4'
down_revision: Union[str, Sequence[str], None] = '1ed8406a5e7d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ADDRESS_FIELDS = ("full_name", "phone", "line1", "line2", "city", "state", "postal_code", "county", "country")


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('addresses', sa.Column('full_name', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('addresses', sa.Column('phone', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('addresses', sa.Column('country', sqlmodel.sql.sqltypes.AutoString(), server_default='US', nullable=False))
    op.add_column('addresses', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.add_column('orders', sa.Column('shipping_address', sa.JSON(), nullable=True))
    op.add_column('orders', sa.Column('billing_address', sa.JSON(), nullable=True))

    bind = op.get_bind()
    users = sa.table('users', sa.column('user_id'), sa.column('first_name'), sa.column('last_name'))
    addresses = sa.table('addresses', sa.column('address_id'), sa.column('user_id'), *[sa.column(f) for f in ADDRESS_FIELDS])
    orders = sa.table(
        'orders', sa.column('order_id'), sa.column('shipping_address_id'), sa.column('billing_address_id'),
        sa.column('shipping_address', sa.JSON()), sa.column('billing_address', sa.JSON()),
    )

    # Existing addresses had no recipient: use the account holder's name
    names = {u.user_id: f"{u.first_name} {u.last_name}".strip() for u in bind.execute(sa.select(users))}
    for address in bind.execute(sa.select(addresses.c.address_id, addresses.c.user_id)).all():
        bind.execute(
            addresses.update()
            .where(addresses.c.address_id == address.address_id)
            .values(full_name=names.get(address.user_id) or "Customer")
        )

    with op.batch_alter_table('addresses') as batch:
        batch.alter_column('full_name', existing_type=sqlmodel.sql.sqltypes.AutoString(), nullable=False)

    # Copy each existing order's addresses as they are now (the closest record there is)
    saved = {
        row.address_id: {f: getattr(row, f) for f in ADDRESS_FIELDS}
        for row in bind.execute(sa.select(addresses)).all()
    }
    for order in bind.execute(sa.select(orders.c.order_id, orders.c.shipping_address_id, orders.c.billing_address_id)).all():
        bind.execute(
            orders.update()
            .where(orders.c.order_id == order.order_id)
            .values(shipping_address=saved.get(order.shipping_address_id), billing_address=saved.get(order.billing_address_id))
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('orders', 'billing_address')
    op.drop_column('orders', 'shipping_address')
    with op.batch_alter_table('addresses') as batch:
        batch.drop_column('deleted_at')
        batch.drop_column('country')
        batch.drop_column('phone')
        batch.drop_column('full_name')
