from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.database import engine, Base
from app.utils.redis_client import redis_client
from app.routes.auth import router as auth_router
from app.routes.leads import router as leads_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield
    await redis_client.aclose()

app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(leads_router)
