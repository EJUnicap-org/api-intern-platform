from pydantic import BaseModel, Field, ConfigDict
from app.models.tickets import TicketStatus
from typing import Optional
from datetime import datetime

class TicketCreate(BaseModel):
    content: str = Field(..., min_length=5, description="Descrição detalhada do problema")

class TicketResponse(BaseModel):
    id: int
    author_id: int
    assigned_to_id: Optional[int] = None
    description: str
    status: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
class TicketStatusUpdate(BaseModel):
    status: TicketStatus