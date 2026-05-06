import enum
from datetime import datetime, timezone
from sqlalchemy import String, Float, ForeignKey, DateTime, Enum as SQLEnum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base 

class PaymentMethodEnum(str, enum.Enum):
    PIX = "PIX"
    DINHEIRO = "DINHEIRO"
    CARTAO = "CARTAO"

class Expense(Base):
    """Gastos Corporativos da Diretoria Executiva (Hostinger, contador, etc)"""
    __tablename__ = "corporate_expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    receipt_url: Mapped[str | None] = mapped_column(String, nullable=True)
    
    # Armazena em UTC para não ter problema com o fuso de Recife vs fuso da Hostinger
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Rastreabilidade: quem da diretoria queimou esse dinheiro?
    registered_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    registered_by = relationship("User") 

class Sale(Base):
    """Entradas e Vendas na sede da EJ Unicap (Red Bull, Água, etc)"""
    __tablename__ = "headquarters_sales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_name: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    total_value: Mapped[float] = mapped_column(Float, nullable=False)
    payment_method: Mapped[PaymentMethodEnum] = mapped_column(SQLEnum(PaymentMethodEnum), nullable=False)
    
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Rastreabilidade: quem vendeu?
    registered_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    registered_by = relationship("User")
    
