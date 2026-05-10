import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Ajuste os imports conforme a sua estrutura real
from main import app 
from app.database import get_db_session, Base

TEST_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/banco_teste")

@pytest_asyncio.fixture
async def db_session():
    """
    Cria um motor efêmero para CADA teste usando NullPool.
    Isso impede que o asyncpg tente reutilizar conexões entre Event Loops diferentes.
    """
    # NullPool desativa o cache de conexões, vital para testes paralelos/assíncronos
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
    TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Reconstrói o banco do zero estritamente para este teste
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        yield session
        
    # Destrói o banco após o teste terminar
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        
    await engine.dispose()

@pytest_asyncio.fixture
async def client(db_session):
    """Sequestra a injeção do FastAPI e limpa os rastros depois."""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db_session] = override_get_db
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
        
    # Remove o override para não contaminar outras execuções
    app.dependency_overrides.clear()