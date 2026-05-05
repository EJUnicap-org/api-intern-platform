from pydantic import BaseModel, Field
from datetime import datetime
from app.models.finance import PaymentMethodEnum

class ExpenseBase(BaseModel):
    title: str
    description: str | None = None
    value: float = Field(..., gt=0, description="O valor da despesa deve ser estritamente positivo.")
    receipt_url: str | None = None

class ExpenseCreate(ExpenseBase):
    """O que o front-end envia ao criar."""
    pass

class ExpenseResponse(ExpenseBase):
    """O que a API devolve (inclui IDs e datas geradas)."""
    id: int
    date: datetime
    registered_by_id: int

    class Config:
        from_attributes = True

class SaleBase(BaseModel):
    product_name: str
    quantity: int = Field(default=1, gt=0, description="Não faz sentido vender 0 ou negativo.")
    total_value: float = Field(..., gt=0)
    payment_method: PaymentMethodEnum

class SaleCreate(SaleBase):
    """O que o front-end envia no registro de venda."""
    pass

class SaleResponse(SaleBase):
    """O que a API devolve."""
    id: int
    date: datetime
    registered_by_id: int

    class Config:
        from_attributes = True