from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import ForeignKey, String, Enum as SQLEnum, select
from sqlalchemy.orm import selectinload
import enum
from pydantic import BaseModel, Field, validator
import secrets
import json
import logging
import redis.asyncio as redis
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import os
from contextlib import asynccontextmanager
from database import engine, Base, get_db_session

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        # A marreta: cria todas as tabelas que não existem
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(lifespan=lifespan)
router = APIRouter()
logger = logging.getLogger(__name__)

# Hash falso para mitigar Timing Attacks (mesmo custo computacional do Bcrypt real)
DUMMY_HASH = "$2b$12$SomeRandomSaltHereJustToTakeTime1234567890123456789012"
IS_PRODUCTION = os.getenv("ENV", "development") == "production"

# ======================== ESQUEMAS PYDANTIC ========================
class LoginRequest(BaseModel):
    email: str
    password: str

class OrganizationContactCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(default="", max_length=20)
    cargo: str = Field(default="", max_length=50)

class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    cnpj: str = Field(..., min_length=14, max_length=18)
    status: str = Field(default="LEAD")
    contacts: list[OrganizationContactCreate] = Field(default=[])
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ["LEAD", "CLIENTE", "ARQUIVADO"]
        if v.upper() not in valid_statuses:
            raise ValueError(f'status deve ser um de: {valid_statuses}')
        return v.upper()
    
    @validator('cnpj')
    def validate_cnpj(cls, v):
        cnpj_clean = v.replace('.', '').replace('/', '').replace('-', '')
        if not cnpj_clean.isdigit():
            raise ValueError('CNPJ deve conter apenas números')
        return cnpj_clean

class OrganizationContactResponse(BaseModel):
    id: int
    name: str
    phone: str
    cargo: str
    class Config:
        from_attributes = True

class OrganizationResponse(BaseModel):
    id: int
    name: str
    cnpj: str
    status: str
    contacts: list[OrganizationContactResponse] = []
    class Config:
        from_attributes = True

# ======================== MODELOS SQLALCHEMY ========================
class Base(DeclarativeBase):
    pass

# Herdar de str ajuda na serialização automática do FastAPI/Pydantic
class StatusEnum(str, enum.Enum):
    LEAD = "LEAD"
    CLIENTE = "CLIENTE"
    ARQUIVADO = "ARQUIVADO"

class Organization(Base):
    __tablename__ = "organization"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    cnpj: Mapped[str] = mapped_column(String(18))
    # Correção do typo "mapped_colum" e ajuste do Enum
    status: Mapped[StatusEnum] = mapped_column(SQLEnum(StatusEnum), default=StatusEnum.LEAD)
    
    contacts: Mapped[list["OrganizationContact"]] = relationship(
        back_populates="organization", 
        cascade="all, delete-orphan"
    )

class OrganizationContact(Base):
    __tablename__ = "organization_contact"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20))
    cargo: Mapped[str] = mapped_column(String(50))
    
    organization_id: Mapped[int] = mapped_column(ForeignKey("organization.id", ondelete="CASCADE"))
    organization: Mapped["Organization"] = relationship(back_populates="contacts")

# ======================== DEPENDÊNCIAS DE SEGURANÇA ========================
# Nota: get_db_session, get_redis_client e pwd_context devem estar definidos em outro lugar

async def get_current_user_id(request: Request) -> int:
    session_id = request.cookies.get("ej_session")
    if not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado")
    
    # Aqui entraria a busca no Redis pelo session_id para pegar o user_id
    # Exemplo mockado:
    user_id = 42 
    return user_id

def require_permission(required_permission: str):
    async def permission_check(
            user_id: int = Depends(get_current_user_id),
            # db: AsyncSession = Depends(get_db_session) # Reativar na implementação real
    ):
        # A validação no Redis (Soft Refresh) ou no DB seria feita aqui
        has_permission = True # Mockado para o arquivo compilar
        
        if not has_permission:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
        return user_id
    return permission_check

# ======================== ROTAS DE AUTENTICAÇÃO ========================
@router.post("/login")
async def login_for_access_token(
    credentials: LoginRequest,
    response: Response,
    # db: AsyncSession = Depends(get_db_session),
    # redis_client: redis.Redis = Depends(get_redis_client)
):
    # stmt = select(User).where(User.email == credentials.email)
    # result = await db.execute(stmt)
    # user = result.scalar_one_or_none()
    user = None # Mock para o arquivo compilar sem a tabela User definida aqui

    is_valid = False
    if user:
        is_valid = pwd_context.verify(credentials.password, user.password)
    else:
        # Executa o Dummy Hash para manter o tempo constante (~300ms)
        # pwd_context.verify(credentials.password, DUMMY_HASH)
        pass

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
        )
    
    # Restante da lógica de Redis e Cookies (omitido os await db.execute para brevidade)...
    session_id = secrets.token_urlsafe(32)
    
    response.set_cookie(
        key="ej_session",
        value=session_id,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="lax",
        max_age=3600
    )
    return {"message": "Login successful"}

@router.post("/logout")
async def logout_user(
    response: Response,
    request: Request,
    user_id: int = Depends(get_current_user_id),
    # redis_client: redis.Redis = Depends(get_redis_client)
):
    session_id = request.cookies.get("ej_session")
    response.delete_cookie(key="ej_session", httponly=True, secure=IS_PRODUCTION, samesite="lax")

    if not session_id:
        return {"message": "Sessão já estava inativa."}

    # try:
    #     async with redis_client.pipeline(transaction=True) as pipe:
    #         pipe.delete(f"session:{session_id}")
    #         pipe.srem(f"user_sessions:{user_id}", session_id)
    #         await pipe.execute()
    # except redis.RedisError as e:
    #     logger.error(f"Redis erro: {e}")
    #     raise HTTPException(status_code=500, detail="Erro interno")

    return {"message": "Sessão aniquilada com sucesso."}

# ======================== ROTAS DE NEGÓCIOS ========================
@app.post("/leads", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    org_data: OrganizationCreate,
    # user_id: int = Depends(require_permission("lead:create")),
    db: AsyncSession = Depends(get_db_session) 
):
    """Cria uma nova organização (Lead) com seus contatos."""
    try:
        new_org = Organization(
            name=org_data.name,
            cnpj=org_data.cnpj,
            status=StatusEnum(org_data.status) 
        )
        for contact_data in org_data.contacts:
            new_contact = OrganizationContact(
                name=contact_data.name,
                phone=contact_data.phone,
                cargo=contact_data.cargo,
                organization=new_org 
            )
            #new_org.contacts.append(new_contact)
         
        db.add(new_org)
        await db.commit()
        stmt = select(Organization).where(Organization.id == new_org.id).options(selectinload(Organization.contacts))
        result = await db.execute(stmt)
        org_completa = result.scalar_one()
        
        return org_completa
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(router)