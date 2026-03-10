from fastapi import APIRouter, Response, Request, Depends
from pydantic import BaseModel

from ..database import get_db_session
from ..models.user import User
from ..utils.security import get_current_user
from ..services.auth_service import login_user, logout_user
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
async def login_for_access_token(
    credentials: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
):
    return await login_user(credentials.email, credentials.password, response, db)


@router.post("/logout")
async def logout_user_route(
    response: Response,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    return await logout_user(response, request, current_user.id)
