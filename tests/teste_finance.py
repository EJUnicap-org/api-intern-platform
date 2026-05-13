import pytest
from httpx import AsyncClient
from app.models.user import User, RoleEnum
from app.models.finance import Sale, PaymentMethodEnum
from app.utils.security import hash_password

pytestmark = pytest.mark.asyncio

async def test_diretoria_pode_auditar_redbull(client: AsyncClient, db_session):
    """Caminho Feliz: Diretor consegue ver o cofre completo."""
    senha = "senha_segura"
    # ARRANGE: Criar o Diretor e o Consultor
    diretor = User(name="Diretor Financeiro", email="fin@ej.com", hashed_password=await hash_password(senha), role=RoleEnum.MANAGER)
    consultor = User(name="Consultor Comprador", email="compra@ej.com", hashed_password=await hash_password(senha), role=RoleEnum.CONSULTANT)
    db_session.add_all([diretor, consultor])
    await db_session.commit()

    # ARRANGE: Criar uma compra de mentira no nome do Consultor
    venda = Sale(
        product_name="RedBull", quantity=2, total_value=14.0, 
        payment_method=PaymentMethodEnum.PIX, receipt_url="http://foto.com", 
        registered_by_id=consultor.id
    )
    db_session.add(venda)
    await db_session.commit()

    # Logar como Diretor
    resp_login = await client.post("/auth/login", data={"username": diretor.email, "password": senha})
    token = resp_login.json()["access_token"]

    # ACT: Disparar contra a auditoria
    headers = {"Authorization": f"Bearer {token}"}
    res = await client.get("/sales/redbull/all", headers=headers)

    # ASSERT: Validar sucesso
    assert res.status_code == 200, f"Erro na rota: {res.text}"
    dados = res.json()
    assert len(dados) > 0
    assert dados[0]["product_name"] == "RedBull"
    assert dados[0]["registered_by_id"] == consultor.id

async def test_consultor_nao_pode_auditar_redbull(client: AsyncClient, db_session):
    """Bloqueio de Segurança: Consultor toma 403 Forbidden se tentar auditar a EJ."""
    senha = "senha_segura"
    consultor = User(name="Curioso", email="curioso@ej.com", hashed_password=await hash_password(senha), role=RoleEnum.CONSULTANT)
    db_session.add(consultor)
    await db_session.commit()

    resp_login = await client.post("/auth/login", data={"username": consultor.email, "password": senha})
    token = resp_login.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    res = await client.get("/sales/redbull/all", headers=headers)

    # O sistema DEVE cuspir 403
    assert res.status_code == 403, "Falha de Segurança: O consultor conseguiu ver o caixa da EJ!"