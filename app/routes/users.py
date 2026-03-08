from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, ConfigDict

from ..database import get_db_session
from ..utils.security import require_permission
from ..services.user_service import UserService
from ..schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["Users & Analytics"])

class UserWorkloadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    user: UserResponse
    active_projects_count: int = Field(..., description="Quantidade de projetos em execução alocados")

@router.get("/workload", response_model=list[UserWorkloadResponse])
async def get_team_workload(
    # Apenas gerentes podem ver a carga de trabalho de todos
    user_id: int = Depends(require_permission("team:view_workload")),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Dashboard de Capacidade: Lista todos os consultores e sua carga atual de projetos ativos.
    Usado para decidir alocações de novas demandas.
    """
    return await UserService.get_users_workload(db)