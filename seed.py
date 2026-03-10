import os
from dotenv import load_dotenv

# 1. FORÇA o carregamento absoluto do .env
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'), override=True)

import asyncio
import logging
from sqlalchemy import select
# Importamos a Base para garantir que o Metadata esteja disponível
from app.database import engine, AsyncSessionLocal, Base
from app.models.user import User, RoleEnum
from app.utils.security import hash_password

print(f"DEBUG: Conectando no banco: {os.getenv('DATABASE_URL')}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_first_admin():
    # 2. SINCRONIZAÇÃO FORÇADA: Garante que as tabelas e colunas existam antes do INSERT
    logger.info("Sincronizando modelos com o banco de dados...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 3. EXECUÇÃO DO SEED
    async with AsyncSessionLocal() as session:
        # Verificamos pelo email que você realmente quer usar
        target_email = "projetos@ejunicap.com.br"
        stmt = select(User).where(User.email == target_email)
        result = await session.execute(stmt)
        
        if result.scalar_one_or_none():
            logger.info(f"Admin {target_email} já existe. Seed cancelado.")
            return

        logger.info(f"Criando o administrador: {target_email}")
        hashed_pw = await hash_password("070107Rossini135*")
        
        admin_user = User(
            name="Projetos EJ",
            email=target_email,
            hashed_password=hashed_pw, 
            role=RoleEnum.ADMIN,
            is_active=True
        )
        
        session.add(admin_user)
        try:
            await session.commit()
            logger.info("Primeiro Admin criado com sucesso no banco de dados!")
        except Exception as e:
            await session.rollback()
            logger.error(f"Falha Crítica ao inserir Admin: {e}")

if __name__ == "__main__":
    asyncio.run(seed_first_admin())