import enum
from datetime import datetime
from sqlalchemy import String, Enum as SQLEnum, ForeignKey, Table, Column, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

class ProjectStatusEnum(str, enum.Enum):
    NEGOTIATION = "NEGOCIACAO"
    EXECUTION = "EXECUCAO"
    COMPLETED = "CONCLUIDO"
    CANCELED = "CANCELADO"

# Tabela Associativa para a relação N:N entre Projetos e Usuários
project_members = Table(
    "project_members",
    Base.metadata,
    Column("project_id", ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1500))
    
    status: Mapped[ProjectStatusEnum] = mapped_column(
        SQLEnum(ProjectStatusEnum), default=ProjectStatusEnum.NEGOTIATION
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    # Prazo nasce nulo, não com a data atual. É definido pelo gerente.
    deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # FK para a Organização (Cliente do Lead)
    # Assumindo que a tabela se chama 'organizations' no plural. Ajuste se for singular.
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organization.id"))
    organization: Mapped["Organization"] = relationship(back_populates="projects")

    # Relação N:N com Usuários (Membros alocados ao projeto)
    members: Mapped[list["User"]] = relationship(
        secondary=project_members, back_populates="projects"
    )
