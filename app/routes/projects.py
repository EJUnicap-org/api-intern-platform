import logging, asyncio
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session

from ..schemas.pert import ProjetoInput
from ..utils.security import get_current_user, require_role
from ..models.user import User, RoleEnum

from ..schemas.riskpath import TaskInput
from ..schemas.tasks import TaskCreate
from ..schemas.projects import ProjectCreate, ProjectResponse, ProjectAllocationRequest, ProjectUpdate

from app.services.pert_service import PertService
from ..services.task_service import TaskService
from ..services.project_service import ProjectService
from ..services.pdf_service import PdfService

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
        
@router.patch("/{project_id}/diagnostic", status_code=status.HTTP_200_OK)
async def endpoint_update_pert(
    project_id: int,
    payload: ProjetoInput,
    current_user: User = Depends(require_role([RoleEnum.MANAGER, RoleEnum.ADMIN])),
    db: AsyncSession = Depends(get_db_session),
):
    if not payload.tasks:
        raise HTTPException(status_code=400, detail="O dicionário de tarefas está vazio.")
    
    try:
        resultado_diagnostico = await asyncio.to_thread(PertService.calculate_full_diagnostic, payload.tasks)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    stmt = (
        update(Project)
        .where(Project.id == project_id)
        .values(pert_diagnostic=resultado_diagnostico)
        .returning(Project.id)
    )
    
    result = await db.execute(stmt)
    updated_id = result.scalar_one_or_none()
    
    if not updated_id:
        raise HTTPException(status_code=404, detail="Projeto não encontrado na base de dados.")
        
    await db.commit()
    
    return {
        "status": "sucesso",
        "mensagem": f"Diagnóstico PERT calculado e salvo com sucesso no projeto {project_id}.",
        "dados": resultado_diagnostico
    }
    
@router.get("/{project_id}/diagnostic", status_code=status.HTTP_200_OK)
async def endpoint_get_pert(
    project_id: int,
    current_user: User = Depends(require_role([RoleEnum.MANAGER, RoleEnum.ADMIN])),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Retorna exclusivamente o diagnóstico PERT de um projeto (Acesso restrito a Gestores).
    """
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    projeto = result.scalar_one_or_none()

    if not projeto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Projeto não encontrado."
        )
        
    if not projeto.pert_diagnostic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="O diagnóstico PERT ainda não foi calculado para este projeto."
        )

    return {
        "project_id": projeto.id,
        "pert_diagnostic": projeto.pert_diagnostic
    }
    
@router.get("/{project_id}/diagnostic/pdf", status_code=status.HTTP_200_OK)
async def endpoint_generate_pert_pdf(
    project_id: int,
    current_user: User = Depends(require_role([RoleEnum.MANAGER, RoleEnum.ADMIN])),
    db: AsyncSession = Depends(get_db_session)
):
    """Gera e retorna o arquivo PDF com o diagnóstico PERT do projeto."""
    
    # 1. Busca os dados no banco
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    projeto = result.scalar_one_or_none()
    
    # 2. Validações precisas
    if not projeto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projeto não encontrado na base de dados."
        )
    
    if not projeto.pert_diagnostic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="O diagnóstico PERT ainda não foi calculado para este projeto. Rode a análise matemática primeiro."
        )
    
    # 3. Extração (cuidado com os nomes das variáveis)
    project_title = projeto.title
    diagnostic_pert = projeto.pert_diagnostic
    
    # 4. Orquestração Assíncrona (Protegendo o Event Loop)
    pdf_bytes = await asyncio.to_thread(
        PdfService.build_pert_pdf, 
        project_title, 
        diagnostic_pert
    )
    
    # 5. O Empacotamento HTTP
    headers = {
        "Content-Disposition": f'attachment; filename="diagnostico_pert_projeto_{project_id}.pdf"'
    }
    
    return Response(
        content=pdf_bytes, 
        media_type="application/pdf", 
        headers=headers
    )
    
@router.patch("/{project_id}/editar", status_code=status.HTTP_200_OK)
async def endpoint_update_project(
    project_id: int,
    payload: ProjectUpdate,
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.MANAGER])),
    db: AsyncSession = Depends(get_db_session),
):
    return await ProjectService.update_project(project_id, payload, db)

@router.post("/{project_id}/tasks", status_code=status.HTTP_201_CREATED)
async def endpoint_create_project_task(
    project_id: int,
    payload: TaskCreate,
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.MANAGER])), # Proteção RBAC
    db: AsyncSession = Depends(get_db_session),
):
    return await TaskService.create_task_for_project(project_id, payload, db)