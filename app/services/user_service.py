import logging
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User
from ..models.project import Project, ProjectStatusEnum, project_members

logger = logging.getLogger(__name__)

class UserService:
    """
    Serviço para análise de capacidade e gestão de usuários.
    """

    @staticmethod
    async def get_users_workload(db: AsyncSession) -> list[dict]:
        """
        Retorna a lista de todos os usuários e a contagem de projetos ATIVOS (EM EXECUÇÃO)
        que cada um possui.
        
        A query utiliza LEFT JOIN para garantir que usuários sem projetos 
        também apareçam na lista (com contagem 0).
        """
        # SELECT users.*, COUNT(projects.id) 
        # FROM users
        # LEFT JOIN project_members ON users.id = project_members.user_id
        # LEFT JOIN projects ON project_members.project_id = projects.id AND projects.status = 'EXECUCAO'
        # GROUP BY users.id
        
        stmt = (
            select(User, func.count(Project.id).label("active_projects_count"))
            .outerjoin(project_members, User.id == project_members.c.user_id)
            .outerjoin(Project, and_(
                project_members.c.project_id == Project.id,
                Project.status == ProjectStatusEnum.EM_ANDAMENTO  # Assumindo status operacional
            ))
            .group_by(User.id)
            .order_by(func.count(Project.id).desc()) # Os mais sobrecarregados primeiro
        )

        result = await db.execute(stmt)
        
        # O resultado vem como tuplas (User, count)
        workload_data = []
        for user, count in result:
            workload_data.append({
                "user": user,
                "active_projects_count": count
            })
            
        return workload_data