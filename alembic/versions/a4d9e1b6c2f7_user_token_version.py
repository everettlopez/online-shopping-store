"""user token version: ending every session when the password changes

Revision ID: a4d9e1b6c2f7
Revises: e7a2c5d8f913
Create Date: 2026-10-23 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4d9e1b6c2f7'
down_revision: Union[str, Sequence[str], None] = 'e7a2c5d8f913'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Existing tokens have no version, which counts as 0, so nobody is logged out
    op.add_column('users', sa.Column('token_version', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('users') as batch:
        batch.drop_column('token_version')
