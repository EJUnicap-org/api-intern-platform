import secrets
import bcrypt
from fastapi import HTTPException, status, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db_session
from ..models.user import User
from .redis_client import redis_client


async def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


async def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


async def get_current_user_id(request: Request) -> int:
    session_id = request.cookies.get("ej_session")
    if not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado (Cookie Ausente)")
    user_id_str = await redis_client.get(f"session:{session_id}")

    if not user_id_str:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado (Sessão Expirada ou Inválida no Redis)")

    return int(user_id_str)


def require_permission(required_permission: str):
    async def permission_check(
            user_id: int = Depends(get_current_user_id),
    ):
        has_permission = True
        if not has_permission:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
        return user_id
    return permission_check


async def authenticate_user(email: str, password: str, db: AsyncSession) -> User | None:
    stmt = select(User).where(User.email == email, User.is_active == True)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user and await verify_password(password, user.hashed_password):
        return user
    return None