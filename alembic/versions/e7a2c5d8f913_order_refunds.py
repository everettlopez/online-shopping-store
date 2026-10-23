"""order refunds: amount refunded, when it was refunded in full, and when it was restocked

Revision ID: e7a2c5d8f913
Revises: 9d4b7e2a6c31
Create Date: 2026-10-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7a2c5d8f913'
down_revision: Union[str, Sequence[str], None] = '9d4b7e2a6c31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Existing orders have had nothing refunded through the store
    op.add_column('orders', sa.Column('refunded_amount', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'))
    op.add_column('orders', sa.Column('refunded_at', sa.DateTime(), nullable=True))
    op.add_column('orders', sa.Column('restocked_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('orders') as batch:
        batch.drop_column('restocked_at')
        batch.drop_column('refunded_at')
        batch.drop_column('refunded_amount')
