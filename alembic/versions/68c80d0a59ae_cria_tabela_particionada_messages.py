"""Cria_tabela_particionada_messages

Revision ID: 68c80d0a59ae
Revises: 9fd075ec0de0
Create Date: 2026-06-08 08:26:52.168947
"""
from alembic import op

# AS VARIÁVEIS OBRIGATÓRIAS DEVEM ESTAR AQUI NO ESCOPO GLOBAL
revision = '68c80d0a59ae'
down_revision = '9fd075ec0de0'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Cria a Tabela Pai
    op.execute("""
        CREATE TABLE messages (
            id SERIAL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            PRIMARY KEY (id, created_at)
        ) PARTITION BY RANGE (created_at);
    """)

    # 2. Cria a partição do mês atual (Junho 2026)
    op.execute("""
        CREATE TABLE messages_y2026m06 PARTITION OF messages
        FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');
    """)

    # 3. Cria a partição do mês seguinte preventivamente (Julho 2026)
    op.execute("""
        CREATE TABLE messages_y2026m07 PARTITION OF messages
        FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');
    """)

    # 4. Cria a Stored Procedure de manutenção que o n8n vai chamar
    op.execute("""
        CREATE OR REPLACE FUNCTION maintain_message_partitions() RETURNS void AS $$
        DECLARE
            next_month DATE := DATE_TRUNC('month', NOW() + INTERVAL '1 month');
            next_next_month DATE := next_month + INTERVAL '1 month';
            partition_name_new TEXT;
            old_month DATE := DATE_TRUNC('month', NOW() - INTERVAL '6 months');
            partition_name_old TEXT;
        BEGIN
            partition_name_new := 'messages_y' || TO_CHAR(next_month, 'YYYY') || 'm' || TO_CHAR(next_month, 'MM');
            partition_name_old := 'messages_y' || TO_CHAR(old_month, 'YYYY') || 'm' || TO_CHAR(old_month, 'MM');

            EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF messages FOR VALUES FROM (%L) TO (%L);', partition_name_new, next_month, next_next_month);
            EXECUTE format('DROP TABLE IF EXISTS %I;', partition_name_old);
        END;
        $$ LANGUAGE plpgsql;
    """)

def downgrade():
    op.execute("DROP FUNCTION IF EXISTS maintain_message_partitions();")
    op.execute("DROP TABLE IF EXISTS messages CASCADE;")