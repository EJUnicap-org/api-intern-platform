from fastapi import APIRouter, Query, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..utils.security import require_permission
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
    db: AsyncSession = Depends(get_db_session)
):
    return await create_lead(org_data, db)


@router.get("/leads", response_model=list[OrganizationResponse])
async def get_leads_route(
    limit: int = Query(default=10, ge=1, le=100),
    user_id: int = Depends(require_permission("lead:create")),
    offset: int = Query(default=0, ge=0),
    cnpj_filter: str | None = Query(default=None, description="Filtra por parte do CNPJ"),
    db: AsyncSession = Depends(get_db_session),
):
    return await get_leads(limit, offset, cnpj_filter, db)


@router.patch("/leads/{lead_id}/status", response_model=OrganizationResponse)
async def update_lead_status_route(
    lead_id: int,
    status_update: StatusUpdate,
    user_id: int = Depends(require_permission("lead:update")),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Atualiza o status de um lead.

    - **lead_id**: ID da organização na URL
    - **status_update**: JSON contendo o novo status (LEAD, CLIENTE ou ARQUIVADO)

    Returns: Organização atualizada com todos os seus contatos
    """
    return await update_lead_status(lead_id, status_update.status, db)
