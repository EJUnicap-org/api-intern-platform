from fastapi import APIRouter, Response, Request, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from ..database import get_db_session
from ..models.user import User
from ..utils.security import get_current_user
from ..services.auth_service import login_user, logout_user
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", summary="Login For Access Token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db_session)
):
    """
    Rota adaptada para o padrão OAuth2. 
    O form_data sempre chamará o campo de 'username', mesmo que usemos um email.
    """
    # Nós pegamos o 'username' do formulário e passamos como o 'email' para a nossa função interna
    return await login_user(form_data.username, form_data.password, db)

@router.get("/me", summary="Obter dados do usuário logado")
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Rota blindada. Só chega aqui quem tem um JWT válido, não expirado,
    assinado com a nossa SECRET_KEY e pertencente a um usuário ativo no banco.
    """
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role.value,
        "is_active": current_user.is_active
    }