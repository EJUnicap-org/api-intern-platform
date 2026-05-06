from sqlalchemy import select
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, ConfigDict

from ..database import get_db_session
from ..utils.security import require_role 
from ..models.user import User, RoleEnum
from ..services.user_service import UserService
from ..schemas.user import UserResponse, UserCreate

router = APIRouter(prefix="/users", tags=["Users & Analytics"])

class UserRoleUpdate(BaseModel):
    role: RoleEnum

class UserWorkloadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    user: UserResponse
    active_projects_count: int = Field(..., description="Quantidade de projetos em execução alocados")

@router.get("/workload", response_model=list[UserWorkloadResponse])
async def get_team_workload(
    current_user: User = Depends(require_role([RoleEnum.MANAGER, RoleEnum.ADMIN])),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Dashboard de Capacidade: Lista todos os consultores e sua carga atual de projetos ativos.
    Usado para decidir alocações de novas demandas.
    """
    return await UserService.get_users_workload(db)

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate, 
    current_user: User = Depends(require_role([RoleEnum.ADMIN])),
    db: AsyncSession = Depends(get_db_session)
):
    return await UserService.create_user(current_user, db, user_data)

@router.get("/", status_code=status.HTTP_200_OK)
async def list_all_users(
    current_admin: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.MANAGER, RoleEnum.PC])),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Retorna a lista limpa de todos os usuários cadastrados para o painel administrativo.
    """
    stmt = select(User)
    result = await db.execute(stmt)
    usuarios = result.scalars().all()
    
    return [
        {
            "id": u.id,
            "name": u.name, # ou u.nome
            "email": u.email,
            "role": u.role
        }
        for u in usuarios
    ]

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.MANAGER]))
):
    return await UserService.delete_user(user_id, db)


@router.patch("/{target_user_id}/role", summary="Alterar Nível de Acesso (Passagem de Bastão)")
async def update_user_role(
    target_user_id: int,
    payload: UserRoleUpdate,
    current_admin: User = Depends(require_role([RoleEnum.ADMIN])), 
    db: AsyncSession = Depends(get_db_session)
):
    """Permite que a direx promova ou rebaixe membros"""
    stmt = select(User).where(User.id == target_user_id)
    target_user = await db.scalar(stmt)
    
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    if target_user.id == current_admin.id and payload.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=400, detail="Você não pode remover seu próprio acesso de ADMIN.")

    target_user.role = payload.role
    await db.commit()
    
    return {"message": f"Cargo atualizado para {payload.role.value} com sucesso."}