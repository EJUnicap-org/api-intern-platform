from fastapi import APIRouter, Query, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..utils.security import get_current_user, require_role
from ..models.user import User, RoleEnum
from ..services.lead_service import create_lead, get_leads, update_lead_status, update_organization
from ..schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
    StatusUpdate,
)

router = APIRouter(prefix="/organizations", tags=["Orgs and Leads"])

@router.post("/leads", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_lead_route(
    org_data: OrganizationCreate,
    current_user: User = Depends(require_role([RoleEnum.MANAGER, RoleEnum.ADMIN])),
    db: AsyncSession = Depends(get_db_session)
):
    return await create_lead(org_data, db)

@router.get("/leads", response_model=list[OrganizationResponse])
async def get_leads_route(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    cnpj_filter: str | None = Query(default=None, description="Filtra por parte do CNPJ"),
    current_user: User = Depends(require_role([RoleEnum.MANAGER, RoleEnum.ADMIN])),
    db: AsyncSession = Depends(get_db_session),
):
    return await get_leads(limit, offset, cnpj_filter, db)


@router.patch("/leads/{lead_id}/status", response_model=OrganizationResponse)
async def update_lead_status_route(
    lead_id: int,
    status_update: StatusUpdate,
    current_user: User = Depends(require_role([RoleEnum.MANAGER, RoleEnum.ADMIN])),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Atualiza o status de um lead.
    - **lead_id**: ID da organização na URL
    - **status_update**: JSON contendo o novo status (LEAD, CLIENTE ou ARQUIVADO)
    """
    return await update_lead_status(lead_id, status_update.status, db)

@router.patch("/leads/{lead_id}", status_code=status.HTTP_200_OK)

async def update_organization_route(
    lead_id: int,
    update_data: OrganizationUpdate = str | None,
    current_user: User = Depends(require_role([RoleEnum.MANAGER, RoleEnum.ADMIN])),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Atualiza os dados de uma organização.
    - **lead_id**: ID da organização na URL
    - **data_update**: JSON contendo os novos dados(Nome, CNPJ)
    """
    return await update_organization(lead_id, update_data, db)