"""add_executivo_to_roleenum

Revision ID: b9566a187803
Revises: 6a27b35c8f52
Create Date: 2026-05-14 06:44:38.487555

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b9566a187803'
down_revision: Union[str, Sequence[str], None] = '6a27b35c8f52'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE roleenum ADD VALUE IF NOT EXISTS 'EXECUTIVO'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
