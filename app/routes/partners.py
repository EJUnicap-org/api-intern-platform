import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db_session
from app.utils.security import get_current_user, require_role
from app.models.user import User, RoleEnum
from app.models.partner import Partner
from app.schemas.partner import PartnerCreate, PartnerResponse, PartnerStatusUpdate, PartnerUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/partners", tags=["Rede de Parceiros (PRM)"])

@router.post("/", response_model=PartnerResponse, status_code=status.HTTP_201_CREATED)
async def create_partner(
    payload: PartnerCreate,
    current_user: User = Depends(require_role([RoleEnum.MANAGER, RoleEnum.ADMIN, RoleEnum.EXECUTIVO])),
    db: AsyncSession = Depends(get_db_session)
):
    """Cadastra uma nova empresa na rede de parcerias institucionais."""
    try:
        new_partner = Partner(**payload.model_dump())
        db.add(new_partner)
        await db.commit()
        await db.refresh(new_partner)
        return new_partner
    except Exception as e:
        logger.error(f"Erro ao criar parceiro: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao cadastrar parceiro.")

@router.get("/", response_model=list[PartnerResponse])
async def get_partners(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Lista todos os parceiros para alimentar o Kanban da Diretoria."""
    stmt = select(Partner).order_by(Partner.id.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.patch("/{partner_id}/status", response_model=PartnerResponse)
async def update_partner_status(
    partner_id: int,
    payload: PartnerStatusUpdate,
    current_user: User = Depends(require_role([RoleEnum.MANAGER, RoleEnum.ADMIN, RoleEnum.EXECUTIVO])),
    db: AsyncSession = Depends(get_db_session)
):
    """Move o parceiro pelo funil (Recebe o gatilho de Drag and Drop do Frontend)."""
    stmt = select(Partner).where(Partner.id == partner_id)
    result = await db.execute(stmt)
    partner = result.scalar_one_or_none()

    if not partner:
        raise HTTPException(status_code=404, detail="Parceiro não encontrado.")

    partner.status = payload.status
    await db.commit()
    await db.refresh(partner)
    return partner

@router.patch("/{partner_id}", response_model=PartnerResponse)
async def update_partner_details(
    partner_id: int,
    payload: PartnerUpdate,
    current_user: User = Depends(require_role([RoleEnum.MANAGER, RoleEnum.ADMIN, RoleEnum.EXECUTIVO])),
    db: AsyncSession = Depends(get_db_session)
):
    stmt = select(Partner).where(Partner.id == partner_id)
    result = await db.execute(stmt)
    partner = result.scalar_one_or_none()

    if not partner:
        raise HTTPException(status_code=404, detail="Parceiro não encontrado.")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(partner, key, value)

    await db.commit()
    await db.refresh(partner)
    return partner

@router.delete("/{partner_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_partner(
    partner_id: int,
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.EXECUTIVO])),
    db: AsyncSession = Depends(get_db_session)
):
    """Deleta um parceiro permanentemente do banco de dados (Restrito)."""
    stmt = select(Partner).where(Partner.id == partner_id)
    result = await db.execute(stmt)
    partner = result.scalar_one_or_none()

    if not partner:
        raise HTTPException(status_code=404, detail="Parceiro não encontrado.")

    await db.delete(partner)
    await db.commit()
    return None