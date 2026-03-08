import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..utils.security import get_current_user_id
from ..schemas.time_record import ClockInResponse, TimeSummaryResponse
from ..services.time_record_service import TimeRecordService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/clockins", tags=["Time Records"])


@router.post("/register", response_model=ClockInResponse, status_code=status.HTTP_201_CREATED)
async def register_clockin(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        clockin = await TimeRecordService.register_clockin(user_id, db)
        return clockin
    except Exception as e:
        # Log detalhado do erro para auditoria interna (nunca expor para cliente)
        logger.error(
            f"Erro ao registrar ponto para user_id={user_id}",
            exc_info=True
        )
        # Resposta genérica e cega ao cliente (sem stack trace ou detalhes sensíveis)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro interno ao registrar o ponto. Tente novamente mais tarde."
        )


@router.get("/summary", response_model=TimeSummaryResponse)
async def get_week_summary(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    """Return the work-time summary for the current week."""
    try:
        summary_data = await TimeRecordService.week_summary(user_id, db)
        return summary_data
    except Exception:
        logger.error(
            f"Erro ao obter resumo de ponto para user_id={user_id}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha ao recuperar resumo. Tente novamente mais tarde.",
        )
