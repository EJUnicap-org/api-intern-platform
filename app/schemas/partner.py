from pydantic import BaseModel, Field, ConfigDict
from app.models.partner import PartnerStatusEnum, PartnerTemperatureEnum

class PartnerCreate(BaseModel):
    name: str = Field(..., min_length=1)
    segment: str | None = None
    representative: str | None = None
    expectations: str | None = None
    status: PartnerStatusEnum = PartnerStatusEnum.CAPTACAO
    temperature: PartnerTemperatureEnum = PartnerTemperatureEnum.FRIO
    
class PartnerResponse(PartnerCreate):
    id: int
    metrificacao: str | None = None
    
    model_config = ConfigDict(from_attributes=True)
        
class PartnerStatusUpdate(BaseModel):
    status: PartnerStatusEnum
    
class PartnerUpdate(BaseModel):
    name: str | None = None
    segment: str | None = None
    representative: str | None = None
    expectations: str | None = None
    temperature: PartnerTemperatureEnum | None = None
    # metrificacao: str | None = None