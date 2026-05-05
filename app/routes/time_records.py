import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db_session
from ..utils.security import get_current_user  
from ..models.user import User  
from ..utils.security import require_role
from app.models.time_record import ClockIn
from ..models.user import RoleEnum
from ..schemas.time_record import ClockInResponse, TimeSummaryResponse
from ..services.time_record_service import TimeRecordService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/clockins", tags=["Time Records"])

@router.post("/register", response_model=ClockInResponse, status_code=status.HTTP_201_CREATED)
async def register_clockin(
    current_user: User = Depends(get_current_user),  
    db: AsyncSession = Depends(get_db_session),
):
    try:
        clockin = await TimeRecordService.register_clockin(current_user.id, db)
        return clockin
    except Exception as e:
        logger.error(
            f"Erro ao registrar ponto para user_id={current_user.id}", 
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro interno ao registrar o ponto. Tente novamente mais tarde."
        )

@router.get("/summary", response_model=TimeSummaryResponse)
async def get_week_summary(
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db_session),
):
    """Return the work-time summary for the current week."""
    try:
        
        summary_data = await TimeRecordService.week_summary(current_user.id, db)
        return summary_data
    except Exception:
        logger.error(
            f"Erro ao obter resumo de ponto para user_id={current_user.id}", 
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha ao recuperar resumo. Tente novamente mais tarde.",
        )
        
@router.get("/all", response_model=list[TimeSummaryResponse])
async def get_all_time_records(
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.PC])),
    db: AsyncSession = Depends(get_db_session)
):
    stmt = select(ClockIn).options(selectinload(ClockIn.user)).order_by(ClockIn.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()