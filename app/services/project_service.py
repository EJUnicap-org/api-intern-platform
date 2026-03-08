import logging
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.project import Project
from ..models.user import User
from ..models.organization import Organization
from ..schemas.projects import ProjectCreate

logger = logging.getLogger(__name__)


class ProjectService:
    """
    Serviço de lógica de negócio para projetos.
    """

    @staticmethod
    async def create_project(project_data: ProjectCreate, user_id: int, db: AsyncSession) -> Project:
        """
        Cria um novo projeto, validando e associando os membros.

        Args:
            project_data: Dados do projeto a ser criado.
            db: Sessão do banco de dados.

        Returns:
            O projeto criado.

        Raises:
            ValueError: Se algum dos member_ids não corresponder a um usuário existente.
        """
        unique_member_ids = set(project_data.member_ids)

        # Verificar se a organização existe
        if project_data.organization_id is not None:
            stmt_org = select(Organization).where(Organization.id == project_data.organization_id)
            result_org = await db.execute(stmt_org)
            org = result_org.scalar_one_or_none()
            if not org:
                raise ValueError(f"Organização com ID {project_data.organization_id} não existe.")

        # Buscar usuários pelos IDs fornecidos
        stmt = select(User).where(User.id.in_(unique_member_ids))
        result = await db.execute(stmt)
        users = result.scalars().all()

        # Verificar se todos os IDs existem
        found_ids = {user.id for user in users}
        if len(users) != len(unique_member_ids):
            missing_ids = unique_member_ids - found_ids
            raise ValueError(f"Os seguintes IDs de membros não existem: {list(missing_ids)}")

        # Criar o projeto
        project = Project(
            title=project_data.title,
            description=project_data.description,
            organization_id=project_data.organization_id,
            deadline=project_data.deadline,
            members=users,  # Associar os usuários encontrados
        )
        db.add(project)
        await db.commit()

        # Recarregar com relacionamentos para evitar MissingGreenlet
        stmt = select(Project).options(selectinload(Project.members)).where(Project.id == project.id)
        result = await db.execute(stmt)
        project_loaded = result.scalar_one()

        logger.info(f"Projeto '{project_loaded.title}' criado com ID {project_loaded.id}")
        return project_loaded