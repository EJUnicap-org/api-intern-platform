import logging
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.time_record import ClockIn, StatusClockInEnum

logger = logging.getLogger(__name__)
RECIFE_TZ = ZoneInfo("America/Recife")


class TimeRecordService:
    """
    Serviço de lógica de negócio para registro de ponto.
    
    Implementa o padrão de "alternância inteligente":
    - Mesmo botão para Entrada (criar novo WORKING) e Saída (fechar WORKING aberto)
    - Previne furos no espaço-tempo da tabela com ZoneInfo
    - Garante atomicidade através de transações e locks pessimistas (FOR UPDATE)
    """

    @staticmethod
    async def register_clockin(user_id: int, db: AsyncSession) -> ClockIn:
        """
        Registra o ponto do usuário. Implementa lógica de estado com proteção contra ponto esquecido.
        """
        now_utc = datetime.now(timezone.utc)
        now_recife = now_utc.astimezone(RECIFE_TZ)
        today_date = now_recife.date()
        stmt_open = select(ClockIn).where(
            and_(
                ClockIn.user_id == user_id,
                ClockIn.status == StatusClockInEnum.WORKING,
                ClockIn.end_time.is_(None)
            )
        ).order_by(ClockIn.start_time.desc()).limit(1).with_for_update()

        result = await db.execute(stmt_open)
        open_clockin = result.scalar_one_or_none()

        if open_clockin:
            if open_clockin.start_time.tzinfo is None:
                start_time_utc = open_clockin.start_time.replace(tzinfo=timezone.utc)
            else:
                start_time_utc = open_clockin.start_time
            point_recife = start_time_utc.astimezone(RECIFE_TZ)
            point_date = point_recife.date()
            
            if point_date < today_date:
                open_clockin.end_time = now_utc
                open_clockin.status = StatusClockInEnum.ANOMALY
                
                logger.warning(
                    f"Ponto aberto detectado para user_id={user_id} desde {point_date}. "
                    f"Fechado com ANOMALY (ignorado no total de horas). Novo ponto criado para hoje."
                )
                
                new_clockin = ClockIn(
                    user_id=user_id,
                    status=StatusClockInEnum.WORKING,
                    start_time=now_utc,
                    end_time=None
                )
                
                db.add(new_clockin)
                await db.flush()
                clockin_response = new_clockin
            else:
                open_clockin.end_time = now_utc
                open_clockin.status = StatusClockInEnum.FINISHED
                
                await db.flush()
                clockin_response = open_clockin
        else:
            
            new_clockin = ClockIn(
                user_id=user_id,
                status=StatusClockInEnum.WORKING,
                start_time=now_utc,
                end_time=None
            )
            
            db.add(new_clockin)
            await db.flush()
            clockin_response = new_clockin

        await db.commit()
        await db.refresh(clockin_response)

        return clockin_response

    @staticmethod
    async def week_summary(user_id: int, db: AsyncSession) -> dict:
        """Return summary dict for the current week (see route for Pydantic conversion)."""
        
        now_utc = datetime.now(timezone.utc)
        now_recife = now_utc.astimezone(RECIFE_TZ)
        start_of_week_recife = (now_recife - timedelta(days=now_recife.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        start_of_week_utc = start_of_week_recife.astimezone(timezone.utc)

        duration_expr = (
            func.extract("epoch", ClockIn.end_time)
            - func.extract("epoch", ClockIn.start_time)
        )

        stmt = select(
            func.coalesce(func.sum(duration_expr), 0).label("total_seconds")
        ).where(
            and_(
                ClockIn.user_id == user_id,
                ClockIn.status == StatusClockInEnum.FINISHED,
                ClockIn.start_time >= start_of_week_utc,
            )
        )

        result = await db.execute(stmt)
        total_seconds: float = result.scalar_one()
        total_minutes = int(total_seconds // 60)

        open_stmt = select(ClockIn).where(
            and_(
                ClockIn.user_id == user_id,
                ClockIn.status == StatusClockInEnum.WORKING,
                ClockIn.end_time.is_(None),
            )
        ).limit(1)
        open_row = (await db.execute(open_stmt)).scalar_one_or_none()

        # return plain data; route will marshal into Pydantic model
        return {
            "worked_minutes_this_week": total_minutes,
            "is_working": bool(open_row),
            "current_start_time": open_row.start_time if open_row else None,
        }

