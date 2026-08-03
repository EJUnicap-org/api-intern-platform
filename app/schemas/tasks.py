from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, datetime

from app.models.task import TaskStatusEnum


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: TaskStatusEnum = TaskStatusEnum.PENDING


class TaskCreate(TaskBase):
    assigned_to_id: int
    project_id: int


class TaskUpdate(TaskBase):
    pass


class TaskResponse(TaskBase):
    id: int
    project_id: int
    assigned_to_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
