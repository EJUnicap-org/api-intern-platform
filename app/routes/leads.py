from fastapi import APIRouter, Query, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..utils.security import get_current_user, require_role
from ..models.user import User, RoleEnum
from ..services.lead_service import create_lead, get_leads, update_lead_status
from ..schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    StatusUpdate,
)

router = APIRouter()

@router.post("/leads", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_lead_route(
    org_data: OrganizationCreate,
    # Exigindo apenas que esteja logado (se qualquer consultor puder criar lead)
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    return await create_lead(org_data, db)


@router.get("/leads", response_model=list[OrganizationResponse])
async def get_leads_route(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    cnpj_filter: str | None = Query(default=None, description="Filtra por parte do CNPJ"),
    # Exigindo que seja Gerente ou Admin para listar todos os leads
    current_user: User = Depends(require_role([RoleEnum.MANAGER, RoleEnum.ADMIN])),
    db: AsyncSession = Depends(get_db_session),
):
    return await get_leads(limit, offset, cnpj_filter, db)


@router.patch("/leads/{lead_id}/status", response_model=OrganizationResponse)
async def update_lead_status_route(
    lead_id: int,
    status_update: StatusUpdate,
    # Exigindo que seja Gerente ou Admin para alterar status
    current_user: User = Depends(require_role([RoleEnum.MANAGER, RoleEnum.ADMIN])),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Atualiza o status de um lead.
    - **lead_id**: ID da organização na URL
    - **status_update**: JSON contendo o novo status (LEAD, CLIENTE ou ARQUIVADO)
    """
    return await update_lead_status(lead_id, status_update.status, db)