from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..models.organization import Organization, OrganizationContact, StatusEnum


async def create_lead(org_data, db):
    try:
        new_org = Organization(
            name=org_data.name,
            cnpj=org_data.cnpj,
            status=StatusEnum(org_data.status)
        )
        for contact_data in org_data.contacts:
            new_contact = OrganizationContact(
                name=contact_data.name,
                phone=contact_data.phone,
                cargo=contact_data.cargo,
                organization=new_org
            )

        db.add(new_org)
        await db.commit()

        stmt = select(Organization).where(Organization.id == new_org.id).options(selectinload(Organization.contacts))
        result = await db.execute(stmt)
        org_completa = result.scalar_one()

        return org_completa
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este CNPJ já está cadastrado em nossa base."
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


async def get_leads(limit, offset, cnpj_filter, db):
    stmt = select(Organization).options(selectinload(Organization.contacts))

    if cnpj_filter:
        stmt = stmt.where(Organization.cnpj.contains(cnpj_filter))

    stmt = stmt.offset(offset).limit(limit)

    result = await db.execute(stmt)
    return result.scalars().all()


async def update_lead_status(lead_id: int, new_status: str, db: AsyncSession):
    """
    Atualiza o status de uma organização pelo ID de forma assíncrona e idempotente.
    """
    stmt = select(Organization).where(Organization.id == lead_id).options(selectinload(Organization.contacts))
    result = await db.execute(stmt)
    org = result.scalar_one_or_none()

    # Se não existe, corta a requisição
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organização não encontrada"
        )

    # 1. Cláusula de Eficiência: Se o status já é o desejado, aborte o I/O no banco
    if org.status.value == new_status:
        return org

    # Mutação em memória
    org.status = StatusEnum(new_status)
    
    # 2 e 3. Commita a transação (o add() é implícito) e ignora o refresh letal
    await db.commit()

    return org
