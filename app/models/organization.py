import enum
from sqlalchemy import String, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class StatusEnum(str, enum.Enum):
    LEAD = "LEAD"
    CLIENTE = "CLIENTE"
    ARQUIVADO = "ARQUIVADO"


class Organization(Base):
    __tablename__ = "organization"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    cnpj: Mapped[str] = mapped_column(String(18), unique=True)
    status: Mapped[StatusEnum] = mapped_column(SQLEnum(StatusEnum), default=StatusEnum.LEAD)

    contacts: Mapped[list["OrganizationContact"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan"
    )


class OrganizationContact(Base):
    __tablename__ = "organization_contact"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20))
    cargo: Mapped[str] = mapped_column(String(50))

    organization_id: Mapped[int] = mapped_column(ForeignKey("organization.id", ondelete="CASCADE"))
    organization: Mapped["Organization"] = relationship(back_populates="contacts")
