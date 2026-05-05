from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

from app.models.flag import FlagSeverityEnum
from app.schemas.user import UserResponse 

class FlagCreate(BaseModel):
    severity: FlagSeverityEnum = Field(..., description="Nível da infração")
    reason: str = Field(..., min_length=5, description="Motivo claro da aplicação da bandeira")

class FlagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    severity: FlagSeverityEnum
    reason: str
    created_at: datetime
    created_by: int | None
    user: UserResponse | None = None