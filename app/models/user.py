from typing import List
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from sqlalchemy import Enum as SQLEnum

from ..database import Base

class RoleEnum(str, enum.Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    CONSULTANT = "CONSULTANT"

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleEnum] = mapped_column(SQLEnum(RoleEnum), default=RoleEnum.CONSULTANT)
    is_active: Mapped[bool] = mapped_column(default=True)
    reimbursements: Mapped[List["Reimbursement"]] = relationship(back_populates="user")
    clockins: Mapped[List["ClockIn"]] = relationship(back_populates="user")
    projects: Mapped[list["Project"]] = relationship(
        secondary="project_members", back_populates="members"
    )