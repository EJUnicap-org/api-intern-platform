from typing import List
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from sqlalchemy import Enum as SQLEnum

from ..database import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.flags import UserFlag
    from app.models.project import Project
    from app.models.task import Task
    from app.models.reimbursement import Reimbursement
    from app.models.clockin import ClockIn

class RoleEnum(str, enum.Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    CONSULTANT = "CONSULTANT"
    PC = "PC"
    EXECUTIVO = "EXECUTIVO"

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
    created_by: Mapped[int | None]
    flags: Mapped[list["UserFlag"]] = relationship(
        "UserFlag", back_populates="user", foreign_keys="UserFlag.user_id", cascade="all, delete-orphan"
    )
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="assignee")