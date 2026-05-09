from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field, model_validator
from datetime import date

from app.database import get_db_session
from app.utils.security import get_current_user, require_role
from app.models.user import User, RoleEnum
from app.models.absence import AbsenceRequest, AbsenceTypeEnum, AbsenceStatusEnum

router = APIRouter(prefix="/leave-requests", tags=["Férias & Afastamentos Longos"])

class LeaveRequestCreate(BaseModel):
    type: AbsenceTypeEnum = Field(..., description="FERIAS, REDUCAO_CARGA ou SEMANA_MODO_AVIAO")
    start_date: date = Field(..., description="Data de início")
    end_date: date = Field(..., description="Data de término")
    reason: str | None = Field(None, description="Justificativa para a diretoria")

    @model_validator(mode='after')
    def validate_temporal_logic(self) -> 'LeaveRequestCreate':
        if self.start_date > self.end_date:
            raise ValueError("Erro Lógico: A data de início não pode ser posterior à data de término.")
        if self.start_date < date.today():
            raise ValueError("Regra de Negócio: Não é permitido solicitar afastamentos retroativos.")
        return self

class LeaveStatusUpdate(BaseModel):
    status: AbsenceStatusEnum = Field(..., description="APROVADO ou REJEITADO")

@router.post("/", status_code=status.HTTP_201_CREATED, summary="Solicitar Férias ou Redução")
async def create_leave_request(
    payload: LeaveRequestCreate, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db_session)
):
    stmt = select(AbsenceRequest).where(
        AbsenceRequest.user_id == current_user.id,
        AbsenceRequest.status != AbsenceStatusEnum.DENIED,
        AbsenceRequest.start_date <= payload.end_date,
        AbsenceRequest.end_date >= payload.start_date
    )
    result = await db.execute(stmt)
    
    if result.scalars().first():
        raise HTTPException(
            status_code=400, 
            detail="Você já possui uma solicitação pendente ou aprovada que conflita com este período."
        )

    new_request = AbsenceRequest(
        user_id=current_user.id,
        type=payload.type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        reason=payload.reason,
        status=AbsenceStatusEnum.PENDING
    )
    db.add(new_request)
    await db.commit()
    return {"message": "Solicitação registrada com sucesso e enviada para a Diretoria."}

@router.get("/me", summary="Meus Pedidos de Afastamento")
async def get_my_leave_requests(
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db_session)
):
    stmt = select(AbsenceRequest).where(AbsenceRequest.user_id == current_user.id).order_by(AbsenceRequest.start_date.desc())
    result = await db.scalars(stmt)
    return list(result.all())

@router.get("/all", summary="Painel da Diretoria: Todos os Pedidos")
async def get_all_leave_requests(
    current_admin: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.EXECUTIVO])), 
    db: AsyncSession = Depends(get_db_session)
):
    stmt = select(AbsenceRequest).options(selectinload(AbsenceRequest.user)).order_by(AbsenceRequest.start_date.desc())
    result = await db.scalars(stmt)
    return list(result.all())

@router.patch("/{request_id}/status", summary="Aprovar/Negar Pedido")
async def evaluate_leave_request(
    request_id: int,
    payload: LeaveStatusUpdate,
    current_admin: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.EXECUTIVO])), 
    db: AsyncSession = Depends(get_db_session)
):
    stmt = select(AbsenceRequest).where(AbsenceRequest.id == request_id)
    leave_req = await db.scalar(stmt)
    
    if not leave_req:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada.")
    if leave_req.status != AbsenceStatusEnum.PENDING:
        raise HTTPException(status_code=400, detail=f"Este pedido já foi processado ({leave_req.status.value}).")

    leave_req.status = payload.status
    await db.commit()
    return {"message": f"Pedido de {leave_req.type.value} alterado para {payload.status.value}."}