import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..utils.security import get_current_user
from ..models.user import User
from ..schemas.projects import ProjectCreate, ProjectResponse
from ..services.project_service import ProjectService
from ..models.project import Project

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        project = await ProjectService.create_project(project_data, current_user.id, db)
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Lista os projetos.
    
    - **Gerentes/Admins**: Veem todos os projetos.
    - **Consultores**: Veem apenas projetos onde são membros.
    """
    try:
        stmt = select(Project).options(selectinload(Project.members))

        if current_user.role != "MANAGER":
            stmt = stmt.where(Project.members.any(User.id == current_user.id))

        result = await db.execute(stmt)
        return result.scalars().all()

    except Exception as e:
        logger.error(f"Erro ao listar projetos para user_id={current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao recuperar projetos."
        )