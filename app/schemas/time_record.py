from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from ..models.time_record import StatusClockInEnum


class ClockInResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="ID único do registro de ponto")
    user_id: int = Field(..., description="ID do usuário que bateu o ponto")
    status: StatusClockInEnum = Field(..., description="Status atual do ponto")
    start_time: datetime = Field(..., description="Horário de início do expediente (UTC)")
    end_time: datetime | None = Field(None, description="Horário de saída (UTC), None se ainda trabalhando")
    created_at: datetime = Field(..., description="Quando o registro foi criado (UTC)")
    updated_at: datetime = Field(..., description="Última atualização do registro (UTC)")

class TimeSummaryResponse(BaseModel):
    worked_minutes_this_week: int = Field(
        ..., 
        description="Total de minutos trabalhados e consolidados (FINISHED) na semana atual."
    )
    is_working: bool = Field(
        ..., 
        description="Verdadeiro se o consultor tiver um ponto WORKING em aberto agora."
    )
    current_start_time: datetime | None = Field(
        None, 
        description="Horário de início do turno atual (UTC). Nulo se is_working for falso."
    )