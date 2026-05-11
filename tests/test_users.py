import pytest
from httpx import AsyncClient
from app.models.user import User, RoleEnum

# Altere para a sua função real de hash
from app.utils.security import hash_password

pytestmark = pytest.mark.asyncio

async def test_acesso_rota_protegida_com_token(client: AsyncClient, db_session):
    """
    Testa se uma rota protegida de usuários aceita o token JWT gerado pelo sistema.
    """
    # 1. ARRANGE: Criar o usuário no banco isolado
    senha_plana = "senha_de_admin_123"
    utilizador = User(
        name="Rossini Admin",
        email="admin@ejunicap.com.br",
        hashed_password=await hash_password(senha_plana),
        role=RoleEnum.MANAGER
    )
    db_session.add(utilizador)
    await db_session.commit()

    # 1.5. ARRANGE: Enganar o sistema de Auth para pegar um token real
    resposta_login = await client.post(
        "/auth/login",
        data={"username": "admin@ejunicap.com.br", "password": senha_plana}
    )
    token = resposta_login.json()["access_token"]

    # 2. ACT: Disparar contra a rota protegida com o token no Header
    # Ajuste "/users/me" para a rota real de leitura de usuário que você quer testar
    headers = {"Authorization": f"Bearer {token}"}
    resposta_user = await client.get("/auth/me", headers=headers)

    # 3. ASSERT: Validar se o sistema liberou o acesso e devolveu os dados
    assert resposta_user.status_code == 200, f"Acesso negado ou erro na rota: {resposta_user.text}"
    
    dados = resposta_user.json()
    assert dados["email"] == "admin@ejunicap.com.br", "O sistema retornou os dados do usuário errado."
    assert dados["nome"] == "Rossini Admin", "Falha no mapeamento do JSON de resposta."
    
async def test_acesso_rota_protegida_sem_token_ou_invalido(client: AsyncClient):
    """
    Garante que o sistema bloqueia intrusos de forma previsível e elegante.
    """
    # 1. ACT & ASSERT: Ataque sem nenhum cabeçalho de Autorização
    resposta_vazia = await client.get("/auth/me")
    assert resposta_vazia.status_code == 401, "Falha de Segurança: Rota permitiu acesso sem token."

    # 2. ACT & ASSERT: Ataque com um token completamente forjado
    headers_falsos = {"Authorization": "Bearer token_falso_inventado_por_hacker"}
    resposta_falsa = await client.get("/auth/me", headers=headers_falsos)
    assert resposta_falsa.status_code == 401, "Falha de Segurança: O sistema aceitou um JWT inválido."
    
    # Validando se a mensagem de erro é a padrão e segura
    assert "detail" in resposta_falsa.json(), "O erro não retornou detalhes."