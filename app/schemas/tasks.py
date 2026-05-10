from pydantic import BaseModel
from typing import Optional
from datetime import date

class TaskCreate(BaseModel):
    title: str
    assigned_to_id: int
    due_date: Optional[date]