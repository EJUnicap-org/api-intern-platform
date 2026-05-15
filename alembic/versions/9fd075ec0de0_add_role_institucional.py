"""add_role_institucional

Revision ID: 9fd075ec0de0
Revises: a59a34365c60
Create Date: 2026-05-15 18:57:06.939736

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9fd075ec0de0'
down_revision: Union[str, Sequence[str], None] = 'a59a34365c60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE roleenum ADD VALUE 'INSTITUCIONAL'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
