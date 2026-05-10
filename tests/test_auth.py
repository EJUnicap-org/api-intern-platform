import pytest
from httpx import AsyncClient
from app.models.user import User, RoleEnum

from app.utils.security import hash_password

pytestmark = pytest.mark.asyncio

async def test_login_sucesso_gera_jwt(client: AsyncClient, db_session):
    """
    Testa se o sistema autentica um utilizador válido e devolve o Access Token.
    """
    senha_plana = "senha_forte_123"
    utilizador_teste = User(
        name="Consultor Fantasma",
        email="fantasma@ejunicap.com.br",
        hashed_password=await hash_password(senha_plana),
        role=RoleEnum.CONSULTANT
    )
    db_session.add(utilizador_teste)
    await db_session.commit()

    resposta = await client.post(
        "/auth/login", 
        data={
            "username": "fantasma@ejunicap.com.br", 
            "password": senha_plana
        }
    )

    assert resposta.status_code == 200, f"Falha arquitetural no Login: {resposta.text}"
    
    dados = resposta.json()
    assert "access_token" in dados, "O payload não contém o JWT."
    assert dados["token_type"] == "bearer", "O tipo de token está incorreto."


async def test_login_falha_com_senha_incorreta(client: AsyncClient, db_session):
    """
    Testa se o sistema barra um ataque ou erro de digitação com 401 Unauthorized.
    """
    # 1. ARRANGE: Cria o utilizador alvo
    utilizador_alvo = User(
        name="Alvo Teste",
        email="alvo@ejunicap.com.br",
        hashed_password=await hash_password("senha_correta"),
        role=RoleEnum.CONSULTANT
    )
    db_session.add(utilizador_alvo)
    await db_session.commit()

    # 2. ACT: Forçar o erro de senha
    resposta = await client.post(
        "/auth/login", 
        data={
            "username": "alvo@ejunicap.com.br", 
            "password": "senha_completamente_errada"
        }
    )

    # 3. ASSERT: A porta tem de ficar fechada
    assert resposta.status_code == 401, "Falha Crítica: O sistema aceitou uma senha errada."
    assert "access_token" not in resposta.json(), "O sistema vazou um token para um intruso."