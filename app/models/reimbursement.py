import enum
from decimal import Decimal
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Enum as SQLEnum, ForeignKey, Numeric ,func, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship


from ..database import Base

if TYPE_CHECKING:
    from .user import User

class StatusRefundEnum(str, enum.Enum):
    APPROVED = "APROVADO"
    DENIED = "REJEITADO"
    AWAITING = "AGUARDANDO"
    CLOSED = "FINALIZADO"

class TypeRefundEnum(str, enum.Enum):
    FUEL = "COMBUSTIVEL"
    FOOD = "ALIMENTACAO"
    MATERIAL = "MATERIAL"
    OTHER = "OUTROS"


class Reimbursement(Base):
    __tablename__ = "reimbursements"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(1500))
    category: Mapped[TypeRefundEnum] = mapped_column(SQLEnum(TypeRefundEnum), default=TypeRefundEnum.OTHER)
    value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    pix_key: Mapped[str] = mapped_column(String(32), nullable=False)
    receipt: Mapped[str] = mapped_column(String(255))
    status:  Mapped[StatusRefundEnum] = mapped_column(SQLEnum(StatusRefundEnum), default=StatusRefundEnum.AWAITING)
    user_id:  Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="reimbursements")
    date_time: Mapped[datetime] = mapped_column(DateTime, default=func.now())