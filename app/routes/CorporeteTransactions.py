from app.models.finance import Sale
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


from app.database import get_db_session
from app.utils.security import require_role
from app.models.user import User, RoleEnum
from app.schemas.finance import ExpenseCreate, ExpenseResponse, SaleCreate, SaleResponse

router = APIRouter(prefix="/finance", tags=["Financeiro Corporativo"])

@router.post(
    "/expenses",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registra despesa corporativa (Exclusivo Executivo/Admin)"
)
async def create_corporate_expense(
    payload: ExpenseCreate,
    current_user: User = Depends(require_role([RoleEnum.EXECUTIVO, RoleEnum.ADMIN])),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Aqui entra o pagamento da Hostinger, contador, domínio, etc.
    O comprovante vai pro R2 da Cloudflare usando o mesmo fluxo de upload que já fizemos.
    """
    
    pass

@router.post(
    "/sales",
    response_model=SaleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registra venda de produtos na sede (Ex: Red Bull, Água, Camisas)"
)
async def register_headquarters_sale(
    payload: SaleCreate,
    current_user: User = Depends(require_role([RoleEnum.EXECUTIVO, RoleEnum.ADMIN])),
    db: AsyncSession = Depends(get_db_session)
):
    """
    O seu front-end vai enviar um JSON assim para cá:
    {
       "product_name": "Red Bull",
       "quantity": 2,
       "total_value": 20.00,
       "payment_method": "PIX",
       "receipt_url": "https://pub-xyz.r2.dev/comprovante_pix.pdf"
    }
    """
    try:
        # Transforma o JSON (payload) no objeto do banco de dados
        nova_venda = Sale(
            product_name=payload.product_name,
            quantity=payload.quantity,
            total_value=payload.total_value,
            payment_method=payload.payment_method,
            receipt_url=payload.receipt_url,
            registered_by_id=current_user.id
        )
        
        db.add(nova_venda)
        await db.commit()
        
        # Recarrega o objeto para pegar o ID gerado pelo banco e a data
        await db.refresh(nova_venda)
        
        # O retorno abaixo satisfaz o response_model=SaleResponse
        return nova_venda
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro crítico ao persistir a venda no banco: {str(e)}"
        )