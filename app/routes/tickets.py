import asyncio
import hashlib
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession


from app.models.tickets import Ticket, TicketStatus
from app.schemas.tickets import TicketCreate, TicketResponse, TicketStatusUpdate
from app.utils.security import get_current_user
from app.database import get_db_session
from app.models.user import User, RoleEnum
from app.models.tickets import Ticket, TicketStatus
from app.utils.security import require_role
from app.services.Pc_Pdf_Service import TicketAuditPdfService


router = APIRouter(prefix="/tickets", tags=["Chamados Formais"])

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_ticket(
    payload: TicketCreate,
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.MANAGER, RoleEnum.CONSULTANT])),
    db: AsyncSession = Depends(get_db_session)
):
    """Cria um novo chamado formal no sistema."""
    new_ticket = Ticket(
        author_id=current_user.id, 
        description=payload.content, 
        status=TicketStatus.OPEN
    )
    db.add(new_ticket)
    await db.commit()
    await db.refresh(new_ticket)
    
    return new_ticket

@router.get("/", response_model=list[TicketResponse], status_code=status.HTTP_200_OK)
async def get_tickets(
    limit: int = Query(default=20, le=50, description="Máximo de chamados por página"),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Lista os chamados com isolamento de visibilidade por cargo (RBAC).
    """
    stmt = select(Ticket).order_by(Ticket.created_at.desc())
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.PC]:
        stmt = stmt.where(Ticket.author_id == current_user.id)
    stmt = stmt.limit(limit).offset(offset)
    result = await db.scalars(stmt)
    return list(result.all())

@router.patch("/{ticket_id}/status", status_code=status.HTTP_200_OK)
async def update_ticket_status(
    ticket_id: int,
    payload: TicketStatusUpdate,
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.PC])),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Atualiza o status de um chamado formal.
    Transição de estado restrita à Diretoria/Administração.
    """
    
    stmt = select(Ticket).where(Ticket.id == ticket_id)
    result = await db.execute(stmt)
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chamado não encontrado na base de dados."
        )
        
    ticket.status = payload.status
    await db.commit()
    await db.refresh(ticket)
    
    return ticket

@router.get("/audit/pdf", status_code=status.HTTP_200_OK)
async def endpoint_generate_audit_pdf(
    current_user: User = Depends(require_role([RoleEnum.MANAGER, RoleEnum.ADMIN])),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Agrega as métricas transacionais de chamados e gera o artefato PDF de auditoria.
    """
    
    # 1. Agregação de Volumetria Global (Queries Assíncronas)
    # Exemplo: Contando o total de chamados na base
    total_chamados_stmt = select(func.count(Ticket.id))
    total_chamados = (await db.execute(total_chamados_stmt)).scalar() or 0
    
    total_usuarios_stmt = select(func.count(User.id))
    total_usuarios = (await db.execute(total_usuarios_stmt)).scalar() or 0

    metricas_consolidadas = {
        "mensagens": 14320, # Substitua por um count() real na tabela de Mensagens
        "chamados": total_chamados,
        "usuarios": total_usuarios,
        "midias": 812       # Substitua por um count() real de arquivos no S3/R2 se houver
    }

    # 2. Agregação de Eficiência Operacional (GROUP BY)
    estado_stmt = select(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status)
    estado_result = await db.execute(estado_stmt)
    
    estado_chamados = []
    for status_str, volume in estado_result.all():
        perc = (volume / total_chamados * 100) if total_chamados > 0 else 0
        estado_chamados.append({
            "status": status_str.value if hasattr(status_str, 'value') else status_str,
            "volume": volume,
            "percentual": f"{perc:.1f}%"
        })

    # 3. Membros Mais Engajados (Top 3 via JOIN e GROUP BY)
    # Limitando a 3 para caber perfeitamente no layout do seu PDF
    engajados_stmt = (
        select(User.name, User.role, func.count(Ticket.id).label('volume'))
        .join(Ticket, Ticket.author_id == User.id)
        .group_by(User.id)
        .order_by(func.count(Ticket.id).desc())
        .limit(3)
    )
    engajados_result = await db.execute(engajados_stmt)
    
    membros_engajados = []
    for nome, cargo, vol in engajados_result.all():
        membros_engajados.append({
            "nome": nome,
            "cargo": cargo.value if hasattr(cargo, 'value') else cargo,
            "volume": vol
        })

    # 4. Geração do Hash de Integridade e Data
    periodo_atual = f"01/01/2026 a {datetime.now().strftime('%d/%m/%Y')}"
    # Criando um hash simulado baseado no timestamp para fingir o ledger de auditoria
    hash_referencia = hashlib.sha256(f"audit_{datetime.now().timestamp()}".encode()).hexdigest()[:16].upper()

    # 5. Orquestração Assíncrona do Serviço de CPU-Bound (PDF)
    # A tolerância a erro de concorrência é zero: to_thread é obrigatório para não travar a API.
    pdf_bytes = await asyncio.to_thread(
        TicketAuditPdfService.build_audit_pdf,
        periodo_str=periodo_atual,
        metricas=metricas_consolidadas,
        estado_chamados=estado_chamados,
        membros_engajados=membros_engajados,
        hash_referencia=hash_referencia
    )

    # 6. Retorno Estrito via Response Binário
    headers = {
        "Content-Disposition": 'attachment; filename="relatorio_auditoria_semestral.pdf"'
    }
    
    return Response(
        content=pdf_bytes, 
        media_type="application/pdf", 
        headers=headers
    )