import pytest
from httpx import AsyncClient
from app.models.user import User, RoleEnum
from app.models.message import Message
from app.utils.security import hash_password

pytestmark = pytest.mark.asyncio

async def test_quadro_carrega_sem_token(client: AsyncClient, db_session):
    """GET /messages é público: carrega na primeira abertura do site, sem autenticação."""
    autor = User(name="Autor Teste", email="autor@ej.com", hashed_password=await hash_password("senha_segura"), role=RoleEnum.MANAGER)
    db_session.add(autor)
    await db_session.commit()
    await db_session.refresh(autor)

    db_session.add(Message(user_id=autor.id, content="Aviso geral da EJ"))
    await db_session.commit()

    resposta = await client.get("/messages/")
    assert resposta.status_code == 200, f"Quadro público deveria responder 200: {resposta.text}"

    dados = resposta.json()
    assert len(dados) == 1
    assert dados[0]["content"] == "Aviso geral da EJ"
    assert dados[0]["user_id"] == autor.id
    assert dados[0]["user"]["name"] == "Autor Teste"


async def test_publicar_aviso_exige_autenticacao(client: AsyncClient):
    """POST /messages sem token -> 401 Unauthorized."""
    resposta = await client.post("/messages/", json={"content": "Aviso sem token"})
    assert resposta.status_code == 401, "Rotear de publicação deveria exigir autenticação."


async def test_consultor_nao_pode_publicar_aviso(client: AsyncClient, db_session):
    """POST /messages como CONSULTANT -> 403 (publicação é restrita a ADMIN/MANAGER)."""
    consultor = User(name="Consultor", email="consultor@ej.com", hashed_password=await hash_password("senha_segura"), role=RoleEnum.CONSULTANT)
    db_session.add(consultor)
    await db_session.commit()

    resp_login = await client.post("/auth/login", data={"username": consultor.email, "password": "senha_segura"})
    token = resp_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resposta = await client.post("/messages/", json={"content": "Aviso proibido"}, headers=headers)
    assert resposta.status_code == 403, "Consultor não deveria publicar avisos."


async def test_manager_pode_publicar_aviso(client: AsyncClient, db_session):
    """POST /messages como MANAGER -> 201 com user_id e user aninhado."""
    manager = User(name="Gestor", email="gestor@ej.com", hashed_password=await hash_password("senha_segura"), role=RoleEnum.MANAGER)
    db_session.add(manager)
    await db_session.commit()

    resp_login = await client.post("/auth/login", data={"username": manager.email, "password": "senha_segura"})
    token = resp_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resposta = await client.post("/messages/", json={"content": "Aviso oficial"}, headers=headers)
    assert resposta.status_code == 201, f"Manager deveria publicar: {resposta.text}"

    dados = resposta.json()
    assert dados["content"] == "Aviso oficial"
    assert dados["user_id"] == manager.id
    assert dados["user"]["name"] == "Gestor"
