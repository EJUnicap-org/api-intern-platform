import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..utils.security import get_current_user  # 1. IMPORTAÇÃO CORRETA
from ..models.user import User  # 2. IMPORTAÇÃO DO MODELO
from ..schemas.time_record import ClockInResponse, TimeSummaryResponse
from ..services.time_record_service import TimeRecordService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/clockins", tags=["Time Records"])

@router.post("/register", response_model=ClockInResponse, status_code=status.HTTP_201_CREATED)
async def register_clockin(
    current_user: User = Depends(get_current_user),  # 3. INJEÇÃO CORRETA
    db: AsyncSession = Depends(get_db_session),
):
    try:
        # 4. EXTRAÇÃO DO ID
        clockin = await TimeRecordService.register_clockin(current_user.id, db)
        return clockin
    except Exception as e:
        logger.error(
            f"Erro ao registrar ponto para user_id={current_user.id}", # 5. LOG CORRIGIDO
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro interno ao registrar o ponto. Tente novamente mais tarde."
        )

@router.get("/summary", response_model=TimeSummaryResponse)
async def get_week_summary(
    current_user: User = Depends(get_current_user), # 6. INJEÇÃO CORRETA
    db: AsyncSession = Depends(get_db_session),
):
    """Return the work-time summary for the current week."""
    try:
        # 7. EXTRAÇÃO DO ID
        summary_data = await TimeRecordService.week_summary(current_user.id, db)
        return summary_data
    except Exception:
        logger.error(
            f"Erro ao obter resumo de ponto para user_id={current_user.id}", # 8. LOG CORRIGIDO
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha ao recuperar resumo. Tente novamente mais tarde.",
        )