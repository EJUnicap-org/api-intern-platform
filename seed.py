import os
from dotenv import load_dotenv

# 1. FORÇA o carregamento absoluto do .env
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'), override=True)

import asyncio
import logging
from sqlalchemy import select
from app.database import engine, AsyncSessionLocal, Base
from app.models.user import User, RoleEnum
from app.models.flag import UserFlag
from app.models.project import Project
from app.models.task import Task
from app.models.reimbursement import Reimbursement
from app.models.time_record import ClockIn
from app.utils.security import hash_password

print(f"DEBUG: Conectando no banco: {os.getenv('DATABASE_URL')}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_first_admin():
    logger.info("Sincronizando modelos com o banco de dados...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        target_email = "projetos@ejunicap.com.br"
        stmt = select(User).where(User.email == target_email)
        result = await session.execute(stmt)
        
        if result.scalar_one_or_none():
            logger.info(f"Admin {target_email} já existe. Seed cancelado.")
            return

        logger.info(f"Criando o administrador: {target_email}")
        hashed_pw = await hash_password("Girafa2026@")
        
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