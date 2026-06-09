from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db_session
from app.models.tickets import Ticket, TicketStatus
from app.schemas.tickets import TicketCreate, TicketResponse

router = APIRouter(prefix="/tickets", tags=["Chamados Formais"])

@router.post("/", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    payload: TicketCreate,
    db: AsyncSession = Depends(get_db_session)
):
    # O mapeamento estrito entre o Schema (payload) e o Model (banco)
    novo_chamado = Ticket(
        author_id=payload.author_id,
        description=payload.content,
        status=TicketStatus.OPEN
    )
    
    db.add(novo_chamado)
    await db.commit()
    await db.refresh(novo_chamado)
    
    return novo_chamado