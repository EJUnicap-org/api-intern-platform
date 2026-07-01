from fastapi import APIRouter, Response, Request, Depends
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from ..database import get_db_session
from ..models.user import User
from ..utils.security import get_current_user
from ..services.auth_service import login_user, logout_user
from ..models.task import Task
from ..models.user import User
from ..utils.security import verify_password, hash_password

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/auth", tags=["Authentication"])

class PasswordUpdate(BaseModel):
    old_password:str
    new_password:str


@router.post("/login", summary="Login For Access Token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db_session)
):
    """
    Rota adaptada para o padrão OAuth2. 
    O form_data sempre chamará o campo de 'username', mesmo que usemos um email.
    """
    return await login_user(form_data.username, form_data.password, db)


@router.get("/me")
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    stmt = (
        select(User)
        .options(
            selectinload(User.tasks).selectinload(Task.project)
        )
        .where(User.id == current_user.id)
    )
    result = await db.execute(stmt)
    user_db = result.scalar_one_or_none()

    if not user_db:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    tarefas_formatadas = []
    for t in user_db.tasks:
        tarefas_formatadas.append({
            "id": t.id,
            "title": t.title,
            "status": t.status.value if hasattr(t.status, 'value') else t.status,
            "projeto_nome": t.project.title if t.project else "Interno"
        })

    return {
        "id": user_db.id,
        "nome": user_db.name, 
        "email": user_db.email,
        "horas_semanais": getattr(user_db, 'horas_semanais', 0), 
        "tarefas": tarefas_formatadas
    }
    
    
@router.patch("/me/password", summary="Alterar própria senha")
async def change_my_password(
    payload: PasswordUpdate, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db_session)
):
    if not await verify_password(payload.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A senha atual está incorreta."
        )
    
    current_user.hashed_password = await hash_password(payload.new_password)
    
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Falha crítica ao gravar no banco de dados."
        )

    return {"detail": "Senha atualizada com segurança."}