import logging
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..utils.security import hash_password
from ..schemas.user import UserCreate

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
                Project.status == ProjectStatusEnum.EM_ANDAMENTO
            ))
            .group_by(User.id)
            .order_by(func.count(Project.id).desc())
        )

        result = await db.execute(stmt)
        workload_data = []
        for user, count in result:
            workload_data.append({
                "user": user,
                "active_projects_count": count
            })
            
        return workload_data
    
    @staticmethod
    async def create_user(current_user: User, db: AsyncSession, user_data: UserCreate) -> User:
        stmt = select(User).where(User.email == user_data.email)
        result = await db.execute(stmt)
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Um usuário com este e-mail já está cadastrado."
            )

        hashed_pw = await hash_password(user_data.password)

        new_user = User(
            name=user_data.name,
            email=user_data.email,
            hashed_password=hashed_pw,
            role=user_data.role,
            created_by=current_user.id
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        return new_user