from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, FastAPI, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import ForeignKey, String, Enum as SQLEnum, select
from sqlalchemy.orm import selectinload, DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.exc import IntegrityError
import redis.asyncio as redis
from pydantic import BaseModel, Field, validator
from contextlib import asynccontextmanager
import enum
import secrets
import logging
import os
import bcrypt
from database import engine, Base, get_db_session

logger = logging.getLogger(__name__)
IS_PRODUCTION = os.getenv("ENV", "development") == "production"
redis_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    redis_client = redis.from_url("redis://localhost:6379/0", decode_responses=True)
    
    yield
    await redis_client.aclose()

app = FastAPI(lifespan=lifespan)
router = APIRouter()

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email:Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    hashed_password:Mapped[str] = mapped_column(String(255), nullable=False)
    is_active:Mapped[bool] = mapped_column(default=True)

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

# previously a second Base was declared here, which conflicted with the
# `Base` imported from `database`.  Instead of redefining it we will reuse the
# original metadata so that all models share the same declarative base.

# (no new Base class needed)

class StatusEnum(str, enum.Enum):
    LEAD = "LEAD"
    CLIENTE = "CLIENTE"
    ARQUIVADO = "ARQUIVADO"

# `Organization` joins the same declarative base imported at the top of the
# file (`from database import engine, Base, get_db_session`).
class Organization(Base):
    __tablename__ = "organization"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    cnpj: Mapped[str] = mapped_column(String(18), unique=True)
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


async def get_current_user_id(request: Request) -> int:
    session_id = request.cookies.get("ej_session")
    if not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado (Cookie Ausente)")
    user_id_str = await redis_client.get(f"session:{session_id}")
    
    if not user_id_str:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado (Sessão Expirada ou Inválida no Redis)")
    
    return int(user_id_str)

def require_permission(required_permission: str):
    async def permission_check(
            user_id: int = Depends(get_current_user_id),
    ):
        has_permission = True 
        if not has_permission:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
        return user_id
    return permission_check


@router.post("/login")
async def login_for_access_token(
    credentials: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_session) # 1. Injetamos o banco de dados
):
    # 2. Buscamos o usuário pelo e-mail
    stmt = select(User).where(User.email == credentials.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # 3. Validamos a existência do usuário e a senha via Bcrypt
    if not user or not bcrypt.checkpw(credentials.password.encode('utf-8'), user.hashed_password.encode('utf-8')):
        # Usamos uma mensagem genérica por segurança (não revelar se o erro foi no e-mail ou na senha)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
        )

    # 4. Geramos a sessão e salvamos o ID REAL no Redis
    session_id = secrets.token_urlsafe(32)
    await redis_client.set(f"session:{session_id}", str(user.id), ex=3600)
    
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
    user_id: int = Depends(get_current_user_id), # Garante que o usuário é válido
):
    session_id = request.cookies.get("ej_session")
    
    # Apaga do banco e apaga do navegador
    await redis_client.delete(f"session:{session_id}")
    response.delete_cookie(key="ej_session", httponly=True, secure=IS_PRODUCTION, samesite="lax")
    
    return {"message": "Sessão aniquilada com sucesso."}

@app.post("/leads", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    org_data: OrganizationCreate,
    db: AsyncSession = Depends(get_db_session) 
):
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
         
        db.add(new_org)
        await db.commit()
        
        stmt = select(Organization).where(Organization.id == new_org.id).options(selectinload(Organization.contacts))
        result = await db.execute(stmt)
        org_completa = result.scalar_one()
        
        return org_completa
    except IntegrityError:
        await db.rollback() 
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este CNPJ já está cadastrado em nossa base."
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.get("/leads", response_model=list[OrganizationResponse]) 
async def get_leads(
    limit: int = Query(default=10, ge=1, le=100),
    user_id: int = Depends(require_permission("lead:create")),
    offset: int = Query(default=0, ge=0),
    cnpj_filter: str | None = Query(default=None, description="Filtra por parte do CNPJ"),
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(Organization).options(selectinload(Organization.contacts))
    
    if cnpj_filter:
        stmt = stmt.where(Organization.cnpj.contains(cnpj_filter))
        
    stmt = stmt.offset(offset).limit(limit)
    
    result = await db.execute(stmt)
    return result.scalars().all()

app.include_router(router)