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


def upgrade():
    with op.get_context().autocommit_block():
        op.execute("""
        DO $$
        BEGIN
            -- Tenta o nome todo em minúsculo (Padrão padrão)
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'roleenum') THEN
                ALTER TYPE roleenum ADD VALUE IF NOT EXISTS 'INSTITUCIONAL';
            
            -- Tenta o nome com maiúsculas (Se o SQLAlchemy forçou aspas)
            ELSIF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'RoleEnum') THEN
                ALTER TYPE "RoleEnum" ADD VALUE IF NOT EXISTS 'INSTITUCIONAL';
            
            -- Tenta com snake_case
            ELSIF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'role_enum') THEN
                ALTER TYPE role_enum ADD VALUE IF NOT EXISTS 'INSTITUCIONAL';
            END IF;
        END
        $$;
        """)

def downgrade():
    pass
