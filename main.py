import logging
from dotenv import load_dotenv

# 1. CARREGAMENTO DE AMBIENTE (Prioridade Máxima)
load_dotenv()
logger = logging.getLogger(__name__)

# 2. IMPORTAÇÕES DE TERCEIROS E FRAMEWORK
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# 3. IMPORTAÇÕES LOCAIS DA APLICAÇÃO
from app.database import engine, Base
from app.routes.messages import limiter
from app.routes.tickets import router as tickets_router
from app.routes.auth import router as auth_router
from app.routes.leads import router as leads_router
from app.routes.messages import router as message_router
from app.routes.CorporeteTransactions import router as corp_router
from app.routes.flight_mode import router as flight_mode_router
from app.routes.financial import router as financial_router
from app.routes.pricing import router as pricing_router
from app.routes.absences import router as absence_router
from app.routes.leave_request import router as leave_request_router
from app.routes.time_records import router as time_records_router
from app.routes.projects import router as projects_router
from app.routes.partners import router as partners_router
from app.routes.users import router as users_router
from app.routes.flag_router import router as flag_router
from app.routes.tasks import router as tasks_router
from app.routes.files import router as files_router
from app.routes.reimbursement import router as reimbursement_router

# 4. INICIALIZAÇÃO DA APLICAÇÃO
app = FastAPI(title="API Interna EJ Unicap")

# 5. CONFIGURAÇÃO DE SEGURANÇA E RATE LIMITING (SlowAPI)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# 6. CONFIGURAÇÃO DO CORS
origins = [
    "https://ej-unicap.vercel.app",  
    "https://ejunicap.com.br",       
    "https://www.ejunicap.com.br",
    "http://127.0.0.1:5500",         
    "http://localhost:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 7. REGISTRO DE ROTAS
app.include_router(auth_router)
app.include_router(leads_router)
app.include_router(time_records_router)
app.include_router(reimbursement_router)
app.include_router(financial_router)
app.include_router(corp_router)
app.include_router(projects_router)
app.include_router(partners_router)
app.include_router(tasks_router)
app.include_router(pricing_router)
app.include_router(users_router)
app.include_router(message_router)
app.include_router(tickets_router)
app.include_router(absence_router)
app.include_router(leave_request_router)
app.include_router(flag_router)
app.include_router(flight_mode_router)
app.include_router(files_router)