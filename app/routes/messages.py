from fastapi import APIRouter, Depends, HTTPException, Query, status, Request

from slowapi import Limiter
from slowapi.util import get_remote_address

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db_session
from app.utils.security import require_role
from app.models.user import User, RoleEnum
from app.models.message import Message
from app.schemas.messages import MessageCreate, MessageResponse

def jwt_limiter_key(request: Request) -> str:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
    return get_remote_address(request)

limiter = Limiter(key_func=jwt_limiter_key)

router = APIRouter(prefix="/messages", tags=["Quadro de avisos"])

@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def post_announcement(
    request: Request,
    payload: MessageCreate,
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.MANAGER])),
    db: AsyncSession = Depends(get_db_session)
):
    """Publica um novo aviso no geral"""
    new_message = Message(
        user_id = current_user.id,
        content = payload.content
    )
    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)
    new_message.user = current_user
    return new_message

@router.get("/", response_model=list[MessageResponse])
async def get_announcements(
    limit: int = Query(default=20, le=50, description="Máximo de mensagens por página"),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db_session)
):
    """Retorna os avisos mais recentes. Paginação OBRIGATÓRIA.
    Público: o quadro de avisos precisa carregar na primeira abertura do site,
    antes do token do usuário hidratar no frontend."""


    stmt = (
        select(Message)
        .options(selectinload(Message.user))
        .order_by(Message.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    
    result = await db.scalars(stmt)
    return list(result.all())