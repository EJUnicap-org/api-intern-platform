import pytest
from httpx import AsyncClient
from app.models.user import User, RoleEnum
from app.utils.security import hash_password # Confirme se o import de hash é este mesmo

pytestmark = pytest.mark.asyncio

async def test_pc_ou_admin_pode_aplicar_bandeira(client: AsyncClient, db_session):
    """Caminho Feliz: Admin do P&C aplicando uma bandeira WARNING."""
    # 1. ARRANGE: Criar Admin e Consultor Alvo
    senha = "senha_padrao_123"
    admin_pc = User(name="Admin PC", email="admin@ej.com", hashed_password=await hash_password(senha), role=RoleEnum.PC)
    consultor = User(name="Consultor Alvo", email="alvo@ej.com", hashed_password=await hash_password(senha), role=RoleEnum.CONSULTANT)
    
    db_session.add_all([admin_pc, consultor])
    await db_session.commit()

    # Logar como Admin
    resp_login = await client.post("/auth/login", data={"username": admin_pc.email, "password": senha})
    token_admin = resp_login.json()["access_token"]

    # 2. ACT: Disparar contra a SUA rota real /users/{id}/flags
    headers = {"Authorization": f"Bearer {token_admin}"}
    payload = {
        "severity": "WARNING", # Baseado no seu FlagSeverityEnum
        "reason": "Conduta inadequada na Reunião Geral."
    }
    
    resposta = await client.post(f"/users/{consultor.id}/flags", json=payload, headers=headers)

    # 3. ASSERT: Validar se criou no banco (Status 201 do seu router)
    assert resposta.status_code == 201, f"Falha na rota: {resposta.text}"
    assert resposta.json()["detail"] == "Bandeira aplicada com sucesso."

async def test_consultor_nao_pode_aplicar_bandeira(client: AsyncClient, db_session):
    """Caminho de Falha: Consultor tentando punir alguém (Vazamento de Permissão)."""
    senha = "senha_padrao_123"
    consultor_invasor = User(name="Invasor", email="invasor@ej.com", hashed_password=await hash_password(senha), role=RoleEnum.CONSULTANT)
    vitima = User(name="Vitima", email="vitima@ej.com", hashed_password=await hash_password(senha), role=RoleEnum.CONSULTANT)
    
    db_session.add_all([consultor_invasor, vitima])
    await db_session.commit()

    # Logar como Consultor
    resp_login = await client.post("/auth/login", data={"username": consultor_invasor.email, "password": senha})
    token_invasor = resp_login.json()["access_token"]

    # ACT: Consultor tenta usar a rota
    headers = {"Authorization": f"Bearer {token_invasor}"}
    payload = {
        "severity": "FORMAL",
        "reason": "Tentando forjar uma demissão."
    }
    
    resposta = await client.post(f"/users/{vitima.id}/flags", json=payload, headers=headers)

    # ASSERT: O seu utils.security.require_role DEVE barrar isso com 403
    assert resposta.status_code == 403, "Falha de Segurança: Consultor conseguiu emitir bandeira!"