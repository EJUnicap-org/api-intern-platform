from datetime import date as dt_date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field

from app.database import get_db_session
from app.utils.security import get_current_user, require_role
from app.models.user import RoleEnum, User
from app.models.absence import AbsenceRequest, AbsenceStatusEnum
from app.models.flight_mode import FlightMode, BlockedDate

router = APIRouter(prefix="/flight-mode", tags=["Modo Avião Automático"])

class FlightModeCreate(BaseModel):
    date: dt_date = Field(..., description="Data desejada para o Modo Avião")
    
class GenerateRGRequest(BaseModel):
    start_date: dt_date = Field(..., description="Data da primeira RG (Ex: 2026-05-13)")
    occurrences: int = Field(15, description="Quantas RGs projetar para o futuro")

@router.post("/", status_code=status.HTTP_201_CREATED, summary="Reservar Modo Avião")
async def book_flight_mode(
    payload: FlightModeCreate, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db_session)
):
    target_date = payload.date
    
    if target_date < dt_date.today():
        raise HTTPException(status_code=400, detail="Você não pode agendar Modo Avião retroativo.")
        
    stmt_blocked = select(BlockedDate).where(BlockedDate.date == target_date)
    blocked = await db.scalar(stmt_blocked)
    if blocked:
        raise HTTPException(status_code=403, detail=f"Data bloqueada pelo P&C: {blocked.description}")

    start_of_week = target_date - timedelta(days=target_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    stmt_week = select(FlightMode).where(
        FlightMode.user_id == current_user.id,
        FlightMode.date >= start_of_week,
        FlightMode.date <= end_of_week
    )
    existing_booking = await db.scalar(stmt_week)
    
    if existing_booking:
        raise HTTPException(
            status_code=429, 
            detail=f"Cota semanal excedida. Você já tem Modo Avião marcado para {existing_booking.date.strftime('%d/%m/%Y')} nesta semana."
        )

    new_booking = FlightMode(user_id=current_user.id, date=target_date)
    db.add(new_booking)
    await db.commit()
    
    return {"message": "Modo Avião reservado com sucesso!"}

# 1. ROTA GERADORA DE RGs (P&C)
@router.post("/generate-rgs", summary="Direx/P&C: Gerar calendário de RGs")
async def generate_rg_calendar(
    payload: GenerateRGRequest,
    current_admin: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.EXECUTIVO, RoleEnum.PC])),
    db: AsyncSession = Depends(get_db_session)
):
    """Gera bloqueios automáticos a cada 14 dias a partir de uma data âncora."""
    generated = 0
    for i in range(payload.occurrences):
        rg_date = payload.start_date + timedelta(days=14 * i)
        
        stmt = select(BlockedDate).where(BlockedDate.date == rg_date)
        exists = await db.scalar(stmt)
        
        if not exists:
            db.add(BlockedDate(date=rg_date, description="RG (Reunião Geral Obrigatória)"))
            generated += 1
            
    await db.commit()
    return {"message": f"{generated} datas de RG foram bloqueadas com sucesso no sistema."}

@router.delete("/{flight_id}", summary="Cancelar Reserva de Modo Avião")
async def cancel_flight_mode(
    flight_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Permite que o membro cancele um modo avião agendado."""
    stmt = select(FlightMode).where(FlightMode.id == flight_id)
    flight = await db.scalar(stmt)
    
    if not flight:
        raise HTTPException(status_code=404, detail="Reserva não encontrada.")
        
    if flight.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Você só pode cancelar suas próprias reservas.")
        
    if flight.date < dt_date.today():
        raise HTTPException(status_code=400, detail="Não é possível cancelar uma reserva passada.")
        
    await db.delete(flight)
    await db.commit()
    return {"message": "Reserva de Modo Avião cancelada com sucesso."}

@router.get("/my-calendar", summary="Ver meu cronograma completo de afastamentos")
async def get_my_calendar(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    stmt_absences = select(AbsenceRequest).where(AbsenceRequest.user_id == current_user.id)
    absences = await db.scalars(stmt_absences)
    
    stmt_flights = select(FlightMode).where(FlightMode.user_id == current_user.id)
    flights = await db.scalars(stmt_flights)
    
    calendar = []
    
    for a in absences:
        calendar.append({
            "id": a.id,
            "category": "LICENCA",
            "type": a.type.value,
            "start_date": a.start_date,
            "end_date": a.end_date,
            "status": a.status.value,
            "reason": a.reason
        })
        
    for f in flights:
        calendar.append({
            "id": f.id,
            "category": "MODO_AVIAO",
            "type": "MODO_AVIAO_DIARIO",
            "start_date": f.date,
            "end_date": f.date,
            "status": "APROVADO",
            "reason": "Reserva Automática"
        })
        
    calendar.sort(key=lambda x: x["start_date"], reverse=True)
    
    return calendar

@router.get("/blocked-dates", summary="Listar próximas datas bloqueadas")
async def get_blocked_dates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retorna as RGs e bloqueios futuros para o front-end exibir no modal."""
    # Traz apenas as datas de hoje para a frente, ordenadas da mais próxima para a mais distante
    stmt = select(BlockedDate).where(BlockedDate.date >= dt_date.today()).order_by(BlockedDate.date.asc())
    result = await db.scalars(stmt)
    return list(result.all())

@router.get("/today", summary="Direx: Quem está de licença ou home office hoje?")
async def get_out_today(
    current_admin: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.EXECUTIVO, RoleEnum.PC])),
    db: AsyncSession = Depends(get_db_session)
):
    hoje = dt_date.today()
    
    stmt_absences = select(AbsenceRequest).options(selectinload(AbsenceRequest.user)).where(
        AbsenceRequest.status == AbsenceStatusEnum.APPROVED,
        AbsenceRequest.start_date <= hoje,
        AbsenceRequest.end_date >= hoje
    )
    absences = await db.scalars(stmt_absences)

    stmt_flights = select(FlightMode).options(selectinload(FlightMode.user)).where(
        FlightMode.date == hoje
    )
    flights = await db.scalars(stmt_flights)

    out_today = []
    
    for a in absences:
        out_today.append({
            "user_name": getattr(a.user, 'name', getattr(a.user, 'nome', 'Sem Nome')),
            "type": a.type.value,
            "reason": a.reason or "Licença Aprovada"
        })
        
    for f in flights:
        out_today.append({
            "user_name": getattr(f.user, 'name', getattr(f.user, 'nome', 'Sem Nome')),
            "type": "MODO_AVIAO_DIARIO",
            "reason": "Reserva Automática"
        })

    return out_today