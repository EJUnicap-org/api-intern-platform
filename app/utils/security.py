import bcrypt
import logging
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy import select
from typing import Callable

from ..database import get_db_session
from ..models.user import User, RoleEnum
from ..config import SECRET_KEY 

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

async def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db_session)
) -> User:
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
            
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Token expirado. Faça login novamente."
        )
    except jwt.PyJWTError:
        raise credentials_exception
    
    stmt = select(User).where(User.email == email, User.is_active == True)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Usuário não encontrado ou inativo."
        )
        
    return user

def require_role(required_roles: list[RoleEnum]) -> Callable:
    """
    Fábrica de dependências para controle de acesso baseado em Roles (RBAC).
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in required_roles:
            logger.warning(
                f"Acesso negado: Usuário {current_user.id} ({current_user.role}) "
                f"tentou acessar recurso que exige {required_roles}."
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem privilégios suficientes para acessar este recurso."
            )
        return current_user
    
    return role_checker


async def authenticate_user(email: str, password: str, db: AsyncSession) -> User | None:
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
    stmt = select(User).where(User.email == email, User.is_active == True)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user and await verify_password(password, user.hashed_password):
        return user
    return None