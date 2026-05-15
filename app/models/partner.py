import enum
from sqlalchemy import String, Enum as SQLEnum, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class PartnerStatusEnum(str, enum.Enum):
    CAPTACAO = "CAPTAÇÃO"
    ATIVACAO = "ATIVAÇÃO"
    ENCANTAMENTO = "ENCANTAMENTO"
    GERENCIAMENTO = "GERENCIAMENTO"
    CONGELADO = "CONGELADO"
    FINALIZADA = "FINALIZADA"
    
class PartnerTemperatureEnum(str, enum.Enum):
    QUENTE = "QUENTE"
    FRIO = "FRIO"
    
class Partner(Base):
    __tablename__ = "partners"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    segment: Mapped[str | None] = mapped_column(String(100))
    representative: Mapped[str | None] = mapped_column(String(100)) 
    expectations: Mapped[str | None] = mapped_column(Text)
    
    status: Mapped[PartnerStatusEnum] = mapped_column(
        SQLEnum(PartnerStatusEnum), default=PartnerStatusEnum.CAPTACAO
    )
    
    temperature: Mapped[PartnerTemperatureEnum] = mapped_column(
        SQLEnum(PartnerTemperatureEnum), default=PartnerTemperatureEnum.FRIO
    )

    metrificacao: Mapped[str | None] = mapped_column(String(200))