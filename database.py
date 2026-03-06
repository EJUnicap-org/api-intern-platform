from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# O chassi fundamental
Base = declarative_base()

# A conexão assíncrona (Substitua a senha se necessário)
DATABASE_URL = "postgresql+asyncpg://postgres:root@localhost:5432/ejunicap_db"

engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session