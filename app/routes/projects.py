import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..utils.security import get_current_user, require_role
from ..models.user import User, RoleEnum
from ..schemas.projects import ProjectCreate, ProjectResponse, ProjectAllocationRequest
from ..services.project_service import ProjectService
from ..models.project import Project

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(require_role([RoleEnum.MANAGER, RoleEnum.ADMIN])),
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

        if current_user.role not in [RoleEnum.MANAGER, RoleEnum.ADMIN]:
            stmt = stmt.where(Project.members.any(User.id == current_user.id))

        result = await db.execute(stmt)
        return result.scalars().all()

    except Exception as e:
        logger.error(f"Erro ao listar projetos para user_id={current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao recuperar projetos."
        )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Retorna os detalhes de um projeto específico pelo ID.
    """
    try:
        # Consulta o banco de dados filtrando pelo ID e garantindo o carregamento dos membros
        stmt = select(Project).options(selectinload(Project.members)).where(Project.id == project_id)
        result = await db.execute(stmt)
        project = result.scalars().first()

        # Retorna erro 404 explícito caso o projeto não seja encontrado
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Projeto não encontrado."
            )
            
         # Validação de autorização OBRIGATÓRIA contra IDOR
        if current_user.role not in [RoleEnum.MANAGER, RoleEnum.ADMIN]:
            is_member = any(member.id == current_user.id for member in project.members)
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Você não tem permissão para visualizar este projeto."
                )

        return project

    except HTTPException:
        # Repassa exceções HTTP (como o 404 ou 403) sem alterá-las
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar projeto {project_id} para user_id={current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao buscar o projeto."
        )
    
@router.post("/{project_id}/members", status_code=status.HTTP_200_OK)
async def add_members_to_project(
    project_id: int,
    allocation_request: ProjectAllocationRequest,
    current_user: User = Depends(require_role([RoleEnum.MANAGER, RoleEnum.ADMIN])),
    db: AsyncSession = Depends(get_db_session),     
):
    """
    Adiciona membros a um projeto existente.
    """
    try:
        await ProjectService.add_members_to_project(
            project_id, 
            allocation_request.member_ids, 
            current_user.id, 
            db
        )
        return {"message": "Membros adicionados com sucesso."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao adicionar membros ao projeto {project_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao adicionar membros ao projeto."
        )