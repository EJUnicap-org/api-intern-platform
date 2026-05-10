import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from main import app 
from app.database import get_db_session, Base

# O robô do GitHub Actions vai injetar o DATABASE_URL verdadeiro da base de dados efêmera aqui
TEST_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/banco_teste")

# Criação do motor assíncrono exclusivo para os testes
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """
    Constrói as tabelas na base de dados efêmera antes de qualquer teste correr,
    e destrói tudo no final da sessão.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db_session():
    """Fornece uma sessão isolada para cada teste."""
    async with TestingSessionLocal() as session:
        yield session

@pytest_asyncio.fixture
async def client(db_session):
    """
    Sequestra a injeção de dependência do FastAPI.
    Sempre que uma rota pedir o `get_db_session`, injetamos a sessão de testes.
    """
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db_session] = override_get_db
    
    # Usa o AsyncClient do httpx para suportar rotas assíncronas do FastAPI
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac