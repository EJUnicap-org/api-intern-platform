from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, Response

from ..models.user import User
from ..utils.security import authenticate_user, redis_client
from ..config import IS_PRODUCTION
import secrets


async def login_user(email: str, password: str, response: Response, db: AsyncSession) -> dict:
    user = await authenticate_user(email, password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")

    session_id = secrets.token_urlsafe(32)
    await redis_client.set(f"session:{session_id}", str(user.id), ex=3600)
    response.set_cookie(
        key="ej_session",
        value=session_id,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="lax",
        max_age=3600
    )
    return {"message": "Login successful"}


async def logout_user(response: Response, request, user_id: int) -> dict:
    session_id = request.cookies.get("ej_session")
    response.delete_cookie(key="ej_session", httponly=True, secure=IS_PRODUCTION, samesite="lax")

    if not session_id:
        return {"message": "Sessão já estava inativa."}

    await redis_client.delete(f"session:{session_id}")
    return {"message": "Sessão aniquilada com sucesso."}
