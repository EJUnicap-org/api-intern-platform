from pydantic import BaseModel, Field, ConfigDict


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID único do usuário")
    name: str = Field(..., description="Nome completo do usuário")
    email: str = Field(..., description="E-mail do usuário")