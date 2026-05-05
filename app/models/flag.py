import enum
from datetime import datetime
from sqlalchemy import ForeignKey, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy import Enum as SQLEnum

from ..database import Base

class FlagSeverityEnum(str, enum.Enum):
    WARNING = "WARNING" #aviso formal
    FORMAL = "FORMAL"
    
class UserFlag(Base):
    __tablename__ = "user_flags"
    
    id: Mapped[int] = mapped_column(primary_key = True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    severity: Mapped[FlagSeverityEnum] = mapped_column(SQLEnum(FlagSeverityEnum), nullable = False)
    reason: Mapped[str] = mapped_column(Text, nullable = False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user: Mapped["User"] = relationship(back_populates="flags", foreign_keys=[user_id])