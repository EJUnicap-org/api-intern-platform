"""
Modelo de Registro de Ponto (ClockIn).
Regra de Negócio: Puramente Administrativo (RH).
Não possui vínculo com Projetos (Costing).
"""
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, DateTime, Enum
from datetime import datetime
import enum

from ..database import Base

class StatusClockInEnum(str, enum.Enum):
    WORKING = "WORKING"
    FINISHED = "FINISHED"
    ANOMALY = "ANOMALY"  # Para pontos fechados automaticamente pelo sistema

class ClockIn(Base):
    __tablename__ = "clock_in"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    
    status: Mapped[StatusClockInEnum] = mapped_column(
        Enum(StatusClockInEnum), 
        default=StatusClockInEnum.WORKING,
        nullable=False
    )
    
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Auditoria básica
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)