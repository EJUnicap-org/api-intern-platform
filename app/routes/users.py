from sqlalchemy import select
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select

from app.models.task import Task
from app.models.project import Project

from ..models.time_record import ClockIn, StatusClockInEnum
from ..database import get_db_session
from ..utils.security import get_current_user, require_role 
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
    
    is_working: bool = Field(..., description="Verdadeiro se o consultor estiver com o ponto aberto")
    current_start_time: datetime | None = Field(None, description="Horário de início do turno atual (UTC)")

@router.get("/workload", response_model=list[UserWorkloadResponse])
async def get_team_workload(
    current_user: User = Depends(require_role([RoleEnum.MANAGER, RoleEnum.ADMIN, RoleEnum.PC])),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Dashboard de Capacidade e Live Tracking: 
    Lista consultores, carga de projetos e status do ponto em tempo real.
    """
    # 1. Mantém a lógica original intacta (pega usuários e contagem de projetos)
    workload_base = await UserService.get_users_workload(db)

    # 2. Faz uma ÚNICA query rápida buscando apenas quem está trabalhando AGORA
    stmt = select(ClockIn).where(
        and_(
            ClockIn.status == StatusClockInEnum.WORKING,
            ClockIn.end_time.is_(None)
        )
    )
    result = await db.execute(stmt)
    pontos_abertos = result.scalars().all()

    # 3. Cria um Hash Map para busca O(1) -> { user_id : start_time }
    turnos_map = {ponto.user_id: ponto.start_time for ponto in pontos_abertos}

    # 4. Mescla os dados em memória
    lista_final = []
    for item in workload_base:
        # Extrai o ID do usuário de forma segura, dependendo se o seu Service retorna Objeto ou Dicionário
        u_id = item.user.id if hasattr(item, 'user') else item['user'].id
        
        start_time = turnos_map.get(u_id)

        lista_final.append(
            UserWorkloadResponse(
                user=item.user if hasattr(item, 'user') else item['user'],
                active_projects_count=item.active_projects_count if hasattr(item, 'active_projects_count') else item['active_projects_count'],
                is_working=(start_time is not None),
                current_start_time=start_time
            )
        )

    return lista_final


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

@router.get("/{user_id}", summary="Raio-X: Obter dados de um utilizador e a sua carga de trabalho")
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    # Fazemos o JOIN automático com Tasks e, dentro das Tasks, com o Project
    stmt = (
        select(User)
        .options(
            selectinload(User.tasks).selectinload(Task.project)
        )
        .where(User.id == user_id)
    )
    result = await db.execute(stmt)
    user_db = result.scalar_one_or_none()

    if not user_db:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado no sistema.")

    # Mapeamento estrito para satisfazer o Front-end
    tasks_formatadas = []
    for t in user_db.tasks:
        tasks_formatadas.append({
            "id": t.id,
            "title": t.title,
            "status": t.status.value if hasattr(t.status, 'value') else t.status,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "project": {
                "id": t.project.id if t.project else None,
                "title": t.project.title if t.project else getattr(t.project, 'name', None) if t.project else None
            } if getattr(t, 'project', None) else None
        })

    # Resposta final unificada
    return {
        "id": user_db.id,
        "nome": getattr(user_db, "name", getattr(user_db, "nome", "Sem Nome")),
        "email": user_db.email,
        "role": user_db.role.value if hasattr(user_db.role, 'value') else user_db.role,
        "tasks": tasks_formatadas
    }