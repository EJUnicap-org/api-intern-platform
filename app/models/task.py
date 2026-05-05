import enum
from datetime import datetime
from sqlalchemy import String, Enum as SQLEnum, ForeignKey, Column, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base

class TaskStatusEnum(str, enum.Enum):
    PENDING = "PENDENTE"
    IN_PROGRESS = "EM_ANDAMENTO"
    COMPLETED = "CONCLUIDO"

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    
    status: Mapped[TaskStatusEnum] = mapped_column(
        SQLEnum(TaskStatusEnum), default=TaskStatusEnum.PENDING
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )

    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    project: Mapped["Project"] = relationship(back_populates="tasks")

    assigned_to_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assignee: Mapped["User"] = relationship(back_populates="tasks")