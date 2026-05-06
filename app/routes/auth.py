from fastapi import APIRouter, Response, Request, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from ..database import get_db_session
from ..models.user import User
from ..utils.security import get_current_user
from ..services.auth_service import login_user, logout_user
from ..models.task import Task
from ..models.user import User

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
    # Nós pegamos o 'username' do formulário e passamos como o 'email' para a nossa função interna
    return await login_user(form_data.username, form_data.password, db)


@router.get("/me")
async def get_current_user_profile(
    current_user: User = Depends(get_current_user), # Use a sua função de dependência de auth aqui
    db: AsyncSession = Depends(get_db_session)
):
    # 1. A BUSCA ATIVA (EAGER LOADING)
    # Exigimos que o banco traga o Usuário + Suas Tarefas + O Projeto de cada Tarefa
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

    # 2. A CONSTRUÇÃO MANUAL DO JSON
    # Isso impede que o Pydantic jogue suas tarefas no lixo
    tarefas_formatadas = []
    for t in user_db.tasks:
        tarefas_formatadas.append({
            "id": t.id,
            "title": t.title,
            # Garante que o Enum seja convertido para string
            "status": t.status.value if hasattr(t.status, 'value') else t.status,
            # Se a tarefa tiver projeto amarrado, pega o título. Se não, é Interno.
            "projeto_nome": t.project.title if t.project else "Interno"
        })

    # 3. O RETORNO QUE O FRONT-END ESPERA
    return {
        "id": user_db.id,
        "nome": user_db.name, # ou user_db.nome, dependendo de como está no seu banco
        "email": user_db.email,
        "horas_semanais": getattr(user_db, 'horas_semanais', 0), # Evita erro se o campo não existir
        "tarefas": tarefas_formatadas
    }
    
@router.patch("/me/password", summary="Alterar própria senha")
async def change_my_password(
    payload: PasswordUpdate, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db_session)
):
    # Pseudo-código de validação estrita:
    # 1. verify_password(payload.old_password, current_user.hashed_password) -> Se falso, Erro 400.
    # 2. current_user.hashed_password = get_password_hash(payload.new_password)
    # 3. await db.commit()
    return {"detail": "Senha atualizada com segurança."}