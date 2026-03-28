from pydantic import BaseModel, Field, ConfigDict

from ..models.user import RoleEnum

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID único do usuário")
    name: str = Field(..., description="Nome completo do usuário")
    email: str = Field(..., description="E-mail do usuário")

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., description="E-mail institucional")
    password: str = Field(..., min_length=8)
    role: RoleEnum = Field(description="Cargo do usuário", default=RoleEnum.CONSULTANT)