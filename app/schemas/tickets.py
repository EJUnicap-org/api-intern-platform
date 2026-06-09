from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class TicketCreate(BaseModel):
    # O payload do seu teste envia "content" e "author_id"
    content: str = Field(..., min_length=5, description="Descrição do problema")
    author_id: int = Field(..., description="ID do autor do chamado")

class TicketResponse(BaseModel):
    id: int
    author_id: int
    assigned_to_id: Optional[int] = None
    description: str
    status: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)