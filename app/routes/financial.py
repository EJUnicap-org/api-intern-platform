from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.database import get_db_session
from app.models.finance import Sale, PaymentMethodEnum
from app.models.user import User
from app.utils.security import get_current_user

router = APIRouter(prefix="/sales", tags=["Finance"])

# Schema local para não precisar criar um arquivo novo agora
class RedBullPurchase(BaseModel):
    quantity: int
    receipt_url: str

@router.post("/redbull", status_code=status.HTTP_201_CREATED)
async def register_redbull_consumption(
    payload: RedBullPurchase,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    try:
        unit_price = 7.00
        total = payload.quantity * unit_price
        
        nova_venda = Sale(
            product_name="RedBull",
            quantity=payload.quantity,
            total_value=total,
            payment_method=PaymentMethodEnum.PIX,
            receipt_url=payload.receipt_url,
            registered_by_id=current_user.id
        )
        
        db.add(nova_venda)
        await db.commit()
        
        return {"detail": "Consumo registrado com sucesso", "total_charged": total}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao registrar consumo: {str(e)}"
        )
      
        
@router.get("/redbull/me", summary="Histórico de compras do membro")
async def get_my_sales(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    try:
        # Busca no banco filtrando por quem está logado, do mais recente pro mais antigo
        query = select(Sale).where(Sale.registered_by_id == current_user.id).order_by(Sale.date.desc())
        result = await db.execute(query)
        return result.scalars().all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar histórico: {str(e)}")