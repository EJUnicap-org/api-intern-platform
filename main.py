from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import logging

logger = logging.getLogger(__name__)
load_dotenv()

from app.database import engine, Base
from app.utils.redis_client import redis_client
from app.routes.auth import router as auth_router
from app.routes.leads import router as leads_router
from app.routes.CorporeteTransactions import router as financial_router
from app.routes.absence import router as absence_router
from app.routes.time_records import router as time_records_router
from app.routes.projects import router as projects_router
from app.routes.users import router as users_router
from app.routes.flag_router import router as flag_router
from app.routes.tasks import router as tasks_router
from app.routes.files import router as files_router
from app.routes.reimbursement import router as reimbursement_router

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

# === CONFIGURAÇÃO DO CORS ===
origins = [
    "http://localhost:3000",      # Padrão React
    "http://localhost:5173",      # Padrão Vite/Vue
    "http://localhost:5500",      # Live Server (Nome)
    "http://127.0.0.1:5500",
    "https://ej-unicap.vercel.app",  # dominio oficial
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ===

app.include_router(auth_router)
app.include_router(leads_router)
app.include_router(time_records_router)
app.include_router(reimbursement_router)
app.include_router(financial_router)
app.include_router(projects_router)
app.include_router(tasks_router)
app.include_router(users_router)
app.include_router(absence_router)
app.include_router(flag_router)
app.include_router(files_router)