import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text

from main import app
from app.models.tickets import Ticket, TicketStatus
client = TestClient(app)

# 1. Adicione a palavra async
@pytest.mark.asyncio
async def test_criar_chamado_formal_sucesso(client, db_session):
    # 1. Garante que o usuário 1 existe antes de fazer o POST
    await db_session.execute(
        text("INSERT INTO users (id, name, email, hashed_password, role, is_active) VALUES (1, 'User Mock', 'mock@ejunicap.com', 'hashedpass', 'CONSULTANT', true) ON CONFLICT DO NOTHING")
    )
    await db_session.commit()

    payload = {
        "content": "O servidor de email parou.",
        "author_id": 1
    }

    # 2. Dispara a rota
    response = await client.post("/tickets/", json=payload)
    
    assert response.status_code == 201, f"Erro na API: {response.text}"
    data = response.json()
    assert data["description"] == payload["content"]
    assert data["status"] == TicketStatus.OPEN.value

    # 3. VALIDAÇÃO CORRETA:
    # O objeto 'data' já contém o que a API devolveu. Use-o para buscar no banco.
    stmt = select(Ticket).where(Ticket.id == data["id"])
    result = await db_session.execute(stmt)
    ticket_no_banco = result.scalar_one_or_none()
    
    assert ticket_no_banco is not None
    assert ticket_no_banco.description == payload["content"]