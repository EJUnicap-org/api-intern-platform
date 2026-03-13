import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reimbursement import Reimbursement
from app.schemas.reimbursement import ReimbursementCreate, ReimbursementResponse, ReimbursementCreateResponse
from app.services.reimbursement_service import ReimbursementService

from ..database import get_db_session
from ..utils.security import get_current_user
from ..models.user import User, RoleEnum

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reimbursements", tags=["Reimbursements"])

@router.get("/", response_model=list[ReimbursementResponse])
async def list_reimbursements(
    current_user: User = Depends(get_current_user), # A PORTA ESTÁ ABERTA PARA TODOS LOGADOS
    db: AsyncSession = Depends(get_db_session),
):
    try:
        stmt = select(Reimbursement).options(selectinload(Reimbursement.user))

        # A LÓGICA DE ESCOPO (IDOR PREVENTED)
        if current_user.role not in [RoleEnum.MANAGER, RoleEnum.ADMIN]:
            stmt = stmt.where(Reimbursement.user_id == current_user.id)

        result = await db.execute(stmt)
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Erro ao listar reembolsos para user_id={current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao recuperar reembolsos."
        )

@router.post("/", response_model=ReimbursementCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_reimbursement(
    reimbursement_data: ReimbursementCreate,
    current_user: User = Depends(get_current_user), # CONSULTOR TAMBÉM PODE PEDIR REEMBOLSO
    db: AsyncSession = Depends(get_db_session)
):
    try:
        # Retorna o dicionário esperado (reembolso + URL pré-assinada)
        return await ReimbursementService.create_reimbursement(reimbursement_data, current_user.id, db)
    except HTTPException:
        raise # Deixa passar as validações de extensão de arquivo (400) do Service
    except Exception as e:
        logger.error(f"Erro ao criar reembolso para user_id={current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao registrar o reembolso. Tente novamente mais tarde."
        )