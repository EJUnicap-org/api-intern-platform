from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from datetime import date

# Importe os seus models e dependências (get_db_session, get_current_user, etc)
from ..models.absence import Absence
from ..database import get_db_session
from ..utils.security import get_current_user


router = APIRouter(prefix="/absences", tags=["Absences"])

class AbsenceCreate(BaseModel):
    absence_date: date
    reason: str

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_absence(
    payload: AbsenceCreate, 
    current_user = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db_session)
):
    new_absence = Absence(
        user_id=current_user.id, 
        absence_date=payload.absence_date, 
        reason=payload.reason
    )
    db.add(new_absence)
    await db.commit()
    return {"message": "Justificativa enviada com sucesso."}

@router.get("/")
async def get_my_absences(
    current_user = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db_session)
):
    # Busca apenas as faltas de quem está logado, da mais recente para a mais antiga
    stmt = select(Absence).where(Absence.user_id == current_user.id).order_by(Absence.absence_date.desc())
    result = await db.execute(stmt)
    absences = result.scalars().all()
    return absences