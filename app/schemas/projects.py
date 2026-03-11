from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from ..models.project import ProjectStatusEnum
from .user import UserResponse


class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=1500)
    organization_id: int | None = Field(None, gt=0)
    deadline: datetime | None = Field(None, description="data limite do projeto")
    member_ids: list[int] = Field(..., min_length=1, description="Lista de IDs dos consultores (mínimo 1)")


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID único do projeto")
    title: str = Field(..., description="Título do projeto")
    description: str | None = Field(None, description="Descrição do projeto")
    status: ProjectStatusEnum = Field(..., description="Status atual do projeto")
    deadline: datetime | None = Field(None, description="Prazo do projeto")
    members: list[UserResponse] = Field(..., description="Lista de membros alocados")


class ProjectAllocationRequest(BaseModel):
    member_ids: list[int] = Field(..., min_length=1)
    