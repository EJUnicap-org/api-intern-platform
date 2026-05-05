from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
# Ajuste os imports abaixo para os caminhos reais do seu projeto
from app.database import get_db_session
from app.utils.security import require_role
from app.models.user import User, RoleEnum
# Você precisará criar esses schemas (ExpenseCreate, SaleCreate, etc)
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
    # CADEADO: Apenas Diretoria Executiva ou Admin podem queimar o dinheiro da EJ
    current_user: User = Depends(require_role([RoleEnum.EXECUTIVO, RoleEnum.ADMIN])),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Aqui entra o pagamento da Hostinger, contador, domínio, etc.
    O comprovante vai pro R2 da Cloudflare usando o mesmo fluxo de upload que já fizemos.
    """
    # Exemplo de conversão para o model (Crie o model Expense no SQLAlchemy depois)
    # new_expense = Expense(**payload.model_dump(), registered_by=current_user.id)
    # db.add(new_expense)
    # await db.commit()
    # return new_expense
    pass

@router.post(
    "/sales",
    response_model=SaleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registra venda de produtos na sede (Ex: Red Bull, Água, Camisas)"
)
async def register_headquarters_sale(
    payload: SaleCreate,
    # CADEADO: Quem pode registrar venda? Provavelmente o Financeiro, Admins ou todos? 
    # Ajuste as roles conforme a regra da EJ. Ex: RoleEnum.FINANCIAL
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
    # new_sale = Sale(**payload.model_dump(), registered_by=current_user.id)
    # db.add(new_sale)
    # await db.commit()
    # return new_sale
    pass