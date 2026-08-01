from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.bookmarks import router as bookmarks_router
from app.api.v1.matches import router as matches_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.opportunities import router as opportunities_router
from app.api.v1.payments import router as payments_router
from app.api.v1.profiles import router as profiles_router
from app.api.v1.roadmap import router as roadmap_router

router = APIRouter()

router.include_router(admin_router)
router.include_router(auth_router)
router.include_router(profiles_router)
router.include_router(opportunities_router)
router.include_router(matches_router)
router.include_router(roadmap_router)
router.include_router(bookmarks_router)
router.include_router(notifications_router)
router.include_router(payments_router)


@router.get("/health")
def health_check() -> dict[str, str]:
    """Liveness — process is up (no dependency checks)."""
    return {"status": "ok"}


@router.get("/health/ready")
def readiness_check() -> dict:
    """Readiness — database reachable + which optional integrations are configured.

    Also ensures pending Alembic migrations are applied (idempotent).
    Returns 503 when the database cannot be reached. Never exposes secret values.
    """
    from fastapi import HTTPException, status
    from sqlalchemy import text

    from app.config import settings
    from app.core.migrate import ensure_migrations
    from app.database import SessionLocal

    schema = "unknown"
    try:
        ensure_migrations()
        schema = "ok"
    except Exception:
        schema = "error"

    database = "error"
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            database = "ok"
        finally:
            db.close()
    except Exception:
        database = "error"

    payload = {
        "status": "ok" if database == "ok" and schema == "ok" else "degraded",
        "database": database,
        "schema": schema,
        "razorpay_configured": settings.razorpay_enabled,
        "polar_configured": settings.polar_enabled,
        "email_configured": settings.email_enabled,
        "admin_configured": bool(settings.admin_password.strip()),
    }
    if database != "ok" or schema != "ok":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=payload,
        )
    return payload
