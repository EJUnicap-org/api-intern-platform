import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..utils.security import get_current_user_id
from ..schemas.projects import ProjectCreate, ProjectResponse
from ..services.project_service import ProjectService
from ..models.project import Project
from ..models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        project = await ProjectService.create_project(project_data, user_id, db)
        return project
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao criar projeto: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao criar projeto. Tente novamente mais tarde."
        )


@router.get("/", response_model=list[ProjectResponse])
async def list_projects(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Lista os projetos.
    
    - **Gerentes/Admins**: Veem todos os projetos.
    - **Consultores**: Veem apenas projetos onde são membros.
    """
    try:
        # 1. Identificar quem é o usuário para aplicar a regra de negócio
        stmt_user = select(User).where(User.id == user_id)
        result_user = await db.execute(stmt_user)
        user = result_user.scalar_one()

        # 2. Construir a query base com Eager Loading
        stmt = select(Project).options(selectinload(Project.members))

        # 3. Aplicar filtro de segurança (Row-Level Security via Application)
        # Se NÃO for admin/gerente, filtra onde o usuário está na lista de membros
        # Assumindo que existe um campo 'role' ou lógica similar. 
        # Se não houver, a regra padrão segura é: só vê o que participa.
        if getattr(user, "role", "CONSULTANT") != "MANAGER":
            stmt = stmt.where(Project.members.any(User.id == user_id))

        result = await db.execute(stmt)
        return result.scalars().all()

    except Exception as e:
        logger.error(f"Erro ao listar projetos para user_id={user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao recuperar projetos."
        )