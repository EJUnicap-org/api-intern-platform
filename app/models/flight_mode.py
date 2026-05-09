from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date
from app.database import Base

class BlockedDate(Base):
    __tablename__ = "blocked_dates"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(100), nullable=False) # Ex: "RG", "Feriado"

class FlightMode(Base):
    __tablename__ = "flight_modes"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    
    user = relationship("User")