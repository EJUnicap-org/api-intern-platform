from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field
from datetime import date

from app.database import get_db_session
from app.utils.security import get_current_user, require_role
from app.models.user import User, RoleEnum
from app.models.absence import Absence, AbsenceStatusEnum 

router = APIRouter(prefix="/absences", tags=["Faltas & Compliance"])
class AbsenceCreate(BaseModel):
    absence_date: date = Field(..., description="Data da ausência")
    reason: str = Field(..., min_length=10, description="Justificativa detalhada")

class AbsenceStatusUpdate(BaseModel):
    status: AbsenceStatusEnum = Field(..., description="APROVADA ou REJEITADA")

@router.post("/", status_code=status.HTTP_201_CREATED, summary="Submeter justificativa de falta")
async def create_absence(
    payload: AbsenceCreate, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db_session)
):
    """Membro envia uma justificativa de falta para o P&C avaliar."""
    new_absence = Absence(
        user_id=current_user.id, 
        absence_date=payload.absence_date, 
        reason=payload.reason,
        status=AbsenceStatusEnum.PENDING
    )
    
    db.add(new_absence)
    await db.commit()
    return {"message": "Justificativa enviada com sucesso para análise."}

@router.get("/", summary="Listar minhas faltas")
async def get_my_absences(
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db_session)
):
    """Membro visualiza o status das próprias faltas reportadas."""
    stmt = select(Absence).where(Absence.user_id == current_user.id).order_by(Absence.absence_date.desc())
    result = await db.scalars(stmt)
    return list(result.all())

@router.get("/all", summary="Painel P&C: Todas as Faltas")
async def get_all_absences(
    current_admin: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.PC])), 
    db: AsyncSession = Depends(get_db_session)
):
    """(Exclusivo P&C) Lista as faltas de toda a organização com os dados do usuário."""
    stmt = select(Absence).options(selectinload(Absence.user)).order_by(Absence.absence_date.desc())
    result = await db.scalars(stmt)
    return list(result.all())

@router.patch("/{absence_id}/status", summary="Avaliar Justificativa")
async def evaluate_absence(
    absence_id: int,
    payload: AbsenceStatusUpdate,
    current_admin: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.PC])), 
    db: AsyncSession = Depends(get_db_session)
):
    """(Exclusivo P&C) Aprova ou Rejeita a justificativa de um membro."""
    stmt = select(Absence).where(Absence.id == absence_id)
    absence = await db.scalar(stmt)
    
    if not absence:
        raise HTTPException(status_code=404, detail="Registro de falta não encontrado.")
    
    if absence.status != AbsenceStatusEnum.PENDING:
        raise HTTPException(status_code=400, detail=f"Esta falta já foi {absence.status.value}.")

    absence.status = payload.status
    await db.commit()
    
    return {"message": f"Justificativa {payload.status.value} com sucesso."}