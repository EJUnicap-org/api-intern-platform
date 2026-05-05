from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ..models.project import Project
from ..models.task import Task, TaskStatusEnum


class TaskService:
    @staticmethod
    async def create_task_for_project(project_id: int, payload: dict, db: AsyncSession):
        # Busca o projeto e faz o join automático com a lista de membros
        stmt = select(Project).options(selectinload(Project.members)).where(Project.id == project_id)
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Projeto não encontrado.")

        # O Filtro de Segurança: O membro designado está na equipe?
        member_ids = [member.id for member in project.members]
        if payload.assigned_to_id not in member_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="O usuário selecionado não está alocado na equipe deste projeto."
            )

        # Se passou, cria a tarefa amarrada ao projeto e ao usuário
        new_task = Task(
            title=payload.title,
            project_id=project_id,
            assigned_to_id=payload.assigned_to_id
        )
        
        db.add(new_task)
        try:
            await db.commit()
            await db.refresh(new_task)
            return new_task
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Erro ao salvar tarefa: {str(e)}")
        
    @staticmethod
    async def complete_task(task_id: int, current_user_id: int, db: AsyncSession):
        stmt = select(Task).where(Task.id == task_id)
        result = await db.execute(stmt)
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(status_code=404, detail="Tarefa não encontrada.")

        # O Filtro de Segurança: O usuário é o dono da tarefa?
        if task.assigned_to_id != current_user_id:
             raise HTTPException(
                 status_code=status.HTTP_403_FORBIDDEN, 
                 detail="Você não tem permissão para concluir uma tarefa de outro membro."
             )

        # Atualiza o status (Verifique se o seu Enum usa "COMPLETED" ou "CONCLUIDO")
        task.status = TaskStatusEnum.COMPLETED 
        
        try:
            await db.commit()
            return {"message": "Tarefa concluída com sucesso."}
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Erro ao concluir: {str(e)}")