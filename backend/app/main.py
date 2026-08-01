import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.config import settings
from app.core.migrate import ensure_migrations

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Apply pending migrations on cold start (Vercel) / process boot (local).
    # Avoids relying on a manual GitHub Actions click when gh CLI is unavailable.
    try:
        ensure_migrations()
    except Exception:
        logger.exception(
            "Database migration failed on startup. "
            "Fix DATABASE_URL / schema, then redeploy or run: alembic upgrade head"
        )
        # Fail closed in production so we do not serve a broken schema.
        if settings.environment == "production":
            raise
    yield


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/api/v1")
