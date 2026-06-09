from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1500, description="Conteúdo do aviso")
    
class MessageAuthorResponse(BaseModel):
    id: int
    name: str
    
class MessageResponse(BaseModel):
    id: int
    content: str
    created_at: datetime
    user: MessageAuthorResponse
    model_config = ConfigDict(from_attributes=True)