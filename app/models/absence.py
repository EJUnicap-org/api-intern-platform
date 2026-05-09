import enum
from datetime import date, datetime
from sqlalchemy import String, ForeignKey, Enum as SQLEnum, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base

class AbsenceTypeEnum(str, enum.Enum):
    VACATION = "FERIAS"
    REDUCTION = "REDUCAO_CARGA"
    FLIGHT_MODE_WEEK = "SEMANA_MODO_AVIAO"

class AbsenceStatusEnum(str, enum.Enum):
    PENDING = "PENDENTE"
    AWAITING = "AGUARDANDO"
    APPROVED = "APROVADO"
    DENIED = "REJEITADO"

class Absence(Base):
    __tablename__ = "absences"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    
    user = relationship("User")
    
    absence_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    
    status: Mapped[AbsenceStatusEnum] = mapped_column(
        SQLEnum(AbsenceStatusEnum), default=AbsenceStatusEnum.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    
class AbsenceRequest(Base):
    __tablename__ = "absence_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    type: Mapped[AbsenceTypeEnum] = mapped_column(SQLEnum(AbsenceTypeEnum), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[AbsenceStatusEnum] = mapped_column(SQLEnum(AbsenceStatusEnum), default=AbsenceStatusEnum.AWAITING)
    
    user = relationship("User")