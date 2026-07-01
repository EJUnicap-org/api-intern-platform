import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reimbursement import Reimbursement
from app.schemas.reimbursement import ReimbursementCreate, ReimbursementResponse, ReimbursementCreateResponse
from app.services.reimbursement_service import ReimbursementService
from ..services.task_service import TaskService
from ..schemas.tasks import TaskResponse

from ..database import get_db_session
from ..utils.security import get_current_user
from ..models.user import User, RoleEnum

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tasks", tags=["Tarefas"])

@router.get("/me", response_model=list[TaskResponse], status_code=status.HTTP_200_OK)
async def get_my_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    return await TaskService.get_user_tasks(current_user.id, db)


@router.patch("/{task_id}/complete", status_code=status.HTTP_200_OK)
async def endpoint_complete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    return await TaskService.complete_task(task_id, current_user.id, db)
