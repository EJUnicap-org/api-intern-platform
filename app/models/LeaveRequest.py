import enum
from datetime import date, datetime
from sqlalchemy import String, ForeignKey, Enum as SQLEnum, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base

class LeaveTypeEnum(str, enum.Enum):
    VACATION = "FÉRIAS"
    SICK_LEAVE = "LICENÇA MÉDICA"
    PERSONAL_LEAVE = "LICENÇA PESSOAL"
    HOME_OFFICE = "MODO AVIAO"
    REDUCTION = "REDUÇÃO DE CARGA"
    
class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    
    