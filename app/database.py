from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from .config import DATABASE_URL

Base = declarative_base()

engine = create_async_engine(DATABASE_URL, echo=False, pool_size = 5, max_overflow = 0, pool_recycle = 3600)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session

        
from .models.user import User
from .models.project import Project
from .models.time_record import ClockIn
from .models.reimbursement import Reimbursement
from .models.organization import Organization

