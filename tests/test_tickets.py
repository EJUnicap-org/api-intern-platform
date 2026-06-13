import pytest
from sqlalchemy import select, text

from main import app
from app.models.tickets import Ticket, TicketStatus
from app.models.user import User, RoleEnum
from app.utils.security import get_current_user

# 1. Função Mock para enganar o FastAPI e simular que há um Token JWT válido na requisição
async def mock_current_user():
    return User(
        id=1, 
        name="User Mock", 
        email="mock@ejunicap.com", 
        role=RoleEnum.CONSULTANT, 
        is_active=True
    )

@pytest.mark.asyncio
async def test_criar_chamado_formal_sucesso(client, db_session):
    # 2. Garante que o usuário 1 existe no banco para satisfazer a ForeignKey do Ticket
    await db_session.execute(
        text("INSERT INTO users (id, name, email, hashed_password, role, is_active) VALUES (1, 'User Mock', 'mock@ejunicap.com', 'hashedpass', 'CONSULTANT', true) ON CONFLICT DO NOTHING")
    )
    await db_session.commit()

    # 3. Injeta o mock da dependência ANTES de disparar a rota
    app.dependency_overrides[get_current_user] = mock_current_user

    # 4. Payload estrito e limpo: SEM o author_id, como exige a sua política de segurança
    payload = {
        "content": "O servidor de email parou."
    }

    # 5. Dispara a rota (O 'client' aqui é a fixture assíncrona que o Pytest injeta)
    response = await client.post("/tickets/", json=payload)
    
    # 6. Limpa o override imediatamente para não vazar a falsa autenticação para outros testes
    app.dependency_overrides.clear()

    # Validações de Rede
    assert response.status_code == 201, f"Erro na API: {response.text}"
    data = response.json()
    assert data["description"] == payload["content"]
    assert data["status"] == TicketStatus.OPEN.value

    # 7. Validação Estrita de Banco de Dados
    stmt = select(Ticket).where(Ticket.id == data["id"])
    result = await db_session.execute(stmt)
    ticket_no_banco = result.scalar_one_or_none()
    
    assert ticket_no_banco is not None
    assert ticket_no_banco.description == payload["content"]
    # Valida se o banco atrelou o chamado ao autor extraído pelo token JWT falso (ID 1)
    assert ticket_no_banco.author_id == 1