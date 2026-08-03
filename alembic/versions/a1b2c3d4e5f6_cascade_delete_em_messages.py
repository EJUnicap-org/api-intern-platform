"""Cascade_delete_em_messages

Revision ID: a1b2c3d4e5f6
Revises: f450cf921666
Create Date: 2026-08-03 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f450cf921666'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adiciona ON DELETE CASCADE no FK messages.user_id.

    Impede que um aviso órfão derrube o GET /messages (user=None -> 500)
    e permite deletar um usuário que já publicou avisos sem violar a FK.
    """
    op.drop_constraint('messages_user_id_fkey', 'messages', type_='foreignkey')
    op.create_foreign_key(
        'messages_user_id_fkey', 'messages', 'users',
        ['user_id'], ['id'], ondelete='CASCADE'
    )


def downgrade() -> None:
    """Remove o ON DELETE CASCADE, voltando ao comportamento original."""
    op.drop_constraint('messages_user_id_fkey', 'messages', type_='foreignkey')
    op.create_foreign_key(
        'messages_user_id_fkey', 'messages', 'users', ['user_id'], ['id']
    )
