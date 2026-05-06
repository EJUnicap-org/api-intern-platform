import asyncio
from fastapi import APIRouter, HTTPException, status, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db_session
from app.utils.security import require_role
from app.models.user import User, RoleEnum
from app.models.organization import Organization
from app.services.pdf_service import PdfService
from ..schemas.pricing import  PricingRequest, PricingResponse, PricingExportRequest


router = APIRouter(prefix="/pricing", tags=["(Re)Precificar projetos"])

@router.post("/calculate", response_model=PricingResponse)
async def calculate_project_price(
        payload: PricingRequest,
        current_admin: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.MANAGER])),
        db: AsyncSession = Depends(get_db_session)
    ):
    total_cost = sum(item.quantity * item.unit_value for item in payload.personnel_costs)
    total_cost += sum(item.quantity * item.unit_value for item in payload.direct_costs)
    total_cost += sum(item.quantity * item.unit_value for item in payload.outsourced_costs)
    total_cost += payload.fixed_cost_allocation
    divisor = 1 - payload.tax_percent - payload.margin_percent
    
    if divisor <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Matemática de precificação inválida: a soma de impostos e margem deve ser menor que 100%."
        )
        
    final_price = total_cost / divisor
    
    return PricingResponse(
        total_direct_cost=round(total_cost, 2),
        tax_value=round(final_price * payload.tax_percent, 2),
        margin_value=round(final_price * payload.margin_percent, 2),
        final_project_value=round(final_price, 2)
    )
    
@router.post("/export-pdf", status_code=status.HTTP_200_OK)
async def export_pricing_pdf(
    payload: PricingExportRequest,
    current_admin: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.MANAGER])),
    db: AsyncSession = Depends(get_db_session)
):
    stmt = select(Organization).where(Organization.id == payload.lead_id)
    result = await db.execute(stmt)
    lead = result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Organização/Lead não encontrado no sistema."
        )

    total_cost = sum(item.quantity * item.unit_value for item in payload.personnel_costs)
    total_cost += sum(item.quantity * item.unit_value for item in payload.direct_costs)
    total_cost += sum(item.quantity * item.unit_value for item in payload.outsourced_costs)
    total_cost += payload.fixed_cost_allocation
    
    divisor = 1 - payload.tax_percent - payload.margin_percent
    if divisor <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Matemática inválida."
        )
        
    final_price = total_cost / divisor
    tax_value = final_price * payload.tax_percent

    orcamento_dados = {
        "cliente": lead.name,
        "cnpj": lead.cnpj if lead.cnpj else "Não cadastrado", 
        "custo_total": total_cost,
        "imposto": tax_value,
        "preco_venda": final_price,

        "insumos_pessoal": [item.model_dump() for item in payload.personnel_costs]
    }
    
    try:
        pdf_bytes = await asyncio.to_thread(
            PdfService.build_orcamento_pdf,
            orcamento_dados
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha na renderização do PDF: {str(e)}"
        )

    safe_filename = lead.name.replace(" ", "_").replace("/", "-")
    headers = {
        "Content-Disposition": f'attachment; filename="Proposta_Comercial_{safe_filename}.pdf"'
    }
    
    return Response(
        content=pdf_bytes, 
        media_type="application/pdf", 
        headers=headers
    )