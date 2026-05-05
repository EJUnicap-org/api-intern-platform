from typing import List

from fastapi import APIRouter, Depends, status, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

# Importações Absolutas (O Padrão Exigido)
from app.database import get_db_session
from app.utils.security import require_role
from app.models.user import User, RoleEnum
from app.models.flag import UserFlag
from app.schemas.flag import FlagCreate, FlagResponse

router = APIRouter(prefix="/users", tags=["Flags & Punições"])

@router.post("/{target_user_id}/flags", response_model=FlagResponse, status_code=status.HTTP_201_CREATED)
async def apply_flag(
    target_user_id: int,
    flag_data: FlagCreate,
    current_admin: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.PC])),
    db: AsyncSession = Depends(get_db_session)
):
    """(Apenas Admins) Aplica uma bandeira a um membro específico."""
    target = await db.scalar(select(User).where(User.id == target_user_id))
    if not target:
        raise HTTPException(status_code=404, detail="Usuário alvo não encontrado.")

    new_flag = UserFlag(
        user_id=target_user_id,
        severity=flag_data.severity,
        reason=flag_data.reason,
        created_by=current_admin.id
    )
    
    db.add(new_flag)
    await db.commit()
    await db.refresh(new_flag)
    
    return new_flag

@router.get("/me/flags", response_model=List[FlagResponse])
async def get_my_flags(
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.MANAGER, RoleEnum.CONSULTANT])),
    db: AsyncSession = Depends(get_db_session)
):
    """(Uso Geral) Retorna o histórico de bandeiras do próprio usuário."""
    stmt = select(UserFlag).where(UserFlag.user_id == current_user.id).order_by(UserFlag.created_at.desc())
    result = await db.scalars(stmt)
    return list(result.all())

from sqlalchemy.orm import selectinload

# ... (resto do seu código existente no flag_router.py) ...

@router.get("/all", response_model=List[FlagResponse], summary="Painel de P&C: Histórico de todas as bandeiras")
async def get_all_flags(
    # O CADEADO: P&C e ADMIN têm acesso total ao painel de infrações
    current_user: User = Depends(require_role([RoleEnum.PC, RoleEnum.ADMIN])),
    db: AsyncSession = Depends(get_db_session)
):
    """(Exclusivo P&C/Admin) Retorna todas as bandeiras da EJ Unicap."""
    
    # O Advogado do Diabo na prática: Trazemos o usuário junto (selectinload) 
    # para que o Front-end possa exibir o NOME de quem tomou a punição, e não apenas o ID.
    stmt = select(UserFlag).options(selectinload(UserFlag.user)).order_by(UserFlag.created_at.desc())
    result = await db.scalars(stmt)
    
    return list(result.all())

@router.delete("/flags/{flag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_flag(
    flag_id: int,
    # Apenas P&C ou Admin podem revogar
    current_admin: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.PC])), 
    db: AsyncSession = Depends(get_db_session)
):
    stmt = select(UserFlag).where(UserFlag.id == flag_id)
    flag = await db.scalar(stmt)
    
    if not flag:
        raise HTTPException(status_code=404, detail="Bandeira não encontrada.")
    
    await db.delete(flag)
    await db.commit()
    
    # Retorna 204 No Content (sucesso sem corpo de resposta)
    return Response(status_code=status.HTTP_204_NO_CONTENT)