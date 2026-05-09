import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.models.reimbursement import Reimbursement, StatusRefundEnum
from app.schemas.reimbursement import ReimbursementCreate, ReimbursementResponse, ReimbursementCreateResponse
from app.services.reimbursement_service import ReimbursementService

from ..database import get_db_session
from ..utils.security import get_current_user, require_role
from ..models.user import User, RoleEnum

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reimbursements", tags=["Reimbursements"])

@router.get("/", response_model=list[ReimbursementResponse])
async def list_reimbursements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        stmt = select(Reimbursement).options(selectinload(Reimbursement.user))

        if current_user.role not in [RoleEnum.MANAGER, RoleEnum.ADMIN, RoleEnum.EXECUTIVO]:
            stmt = stmt.where(Reimbursement.user_id == current_user.id)

        result = await db.execute(stmt)
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Erro ao listar reembolsos para user_id={current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao recuperar reembolsos."
        )

@router.post("/", response_model=ReimbursementResponse, status_code=status.HTTP_201_CREATED)
async def create_reimbursement(
    reimbursement_data: ReimbursementCreate,
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db_session)
):
    try:
        return await ReimbursementService.create_reimbursement(reimbursement_data, current_user.id, db)
    except HTTPException:
        raise 
    except Exception as e:
        logger.error(f"Erro ao criar reembolso para user_id={current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao registrar o reembolso. Tente novamente mais tarde."
        )
        
class ReimbursementStatusUpdate(BaseModel):
    status: StatusRefundEnum
    
@router.patch("/{reimbursement_id}/status", summary="Aprova ou Nega um reembolso (Apenas Diretoria)")
async def update_reimbursement_status(
    reimbursement_id: int,
    payload: ReimbursementStatusUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.EXECUTIVO]))
):
    try:
        result = await db.execute(select(Reimbursement).where(Reimbursement.id == reimbursement_id))
        reembolso = result.scalars().first()

        if not reembolso:
            raise HTTPException(status_code=404, detail="Reembolso não encontrado.")

        # Atualiza o status
        reembolso.status = payload.status
        await db.commit()
        await db.refresh(reembolso)

        return {"detail": f"Status atualizado para {payload.status.value}", "id": reembolso.id}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao processar decisão: {str(e)}")
    
    
@router.get("/all", summary="Lista todos os reembolsos (Apenas Diretoria)")
async def get_all_reimbursements(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.EXECUTIVO]))
):
    try:
        query = select(Reimbursement).options(selectinload(Reimbursement.user)).order_by(Reimbursement.date_time.desc())
        result = await db.execute(query)
        return result.scalars().all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar caixa geral: {str(e)}")