from pydantic import BaseModel, Field
from typing import List

# 1. Primeiro as dependências menores
class CostItem(BaseModel):
    title: str
    quantity: float
    unit_value: float
    
# 2. Depois a classe Pai
class PricingRequest(BaseModel):
    personnel_costs: List[CostItem] = Field(..., description="Horas de consultores e gerentes")
    direct_costs: List[CostItem] = Field(..., description="Hospedagem, press kit, transporte, etc.")
    outsourced_costs: List[CostItem] = Field(default_factory=list)
    fixed_cost_allocation: float = Field(
        default=0.0, 
        description="Valor em Reais a ser embutido para cobrir os custos fixos operacionais da sede"
    )
    margin_percent: float = Field(default=0.35, description="Margem de Lucro (ex: 0.35 para 35%)")
    tax_percent: float = Field(default=0.06, description="Imposto (ex: 0.06 para 6%)")

# 3. Em seguida, a classe Filha herda da classe Pai já declarada acima
class PricingExportRequest(PricingRequest):
    lead_id: int = Field(..., description="ID da organização/lead no banco de dados para buscar os dados de cabeçalho do PDF")

# 4. As respostas
class PricingResponse(BaseModel):
    total_direct_cost: float
    tax_value: float
    margin_value: float
    final_project_value: float