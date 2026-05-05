from pydantic import BaseModel

class TaskCreate(BaseModel):
    title: str
    assigned_to_id: int