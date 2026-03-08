from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

from app.database import engine, Base
from app.utils.redis_client import redis_client
from app.routes.auth import router as auth_router
from app.routes.leads import router as leads_router
from app.routes.time_records import router as time_records_router
from app.routes.projects import router as projects_router
from app.routes.users import router as users_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # O Base.metadata.create_all() foi removido.
    # A gestão do schema do banco de dados deve ser feita com Alembic.
    try:
        await redis_client.ping()
        logger.info("Conexão com o Redis estabelecida com sucesso.")
    except Exception as e:
        logger.error(f"Falha ao conectar com o Redis durante a inicialização: {e}", exc_info=True)

    yield
    await redis_client.aclose()
    logger.info("Conexão com o Redis fechada.")

app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(leads_router)
app.include_router(time_records_router)
app.include_router(projects_router)
app.include_router(users_router)
