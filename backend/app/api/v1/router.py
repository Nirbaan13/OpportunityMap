from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.bookmarks import router as bookmarks_router
from app.api.v1.matches import router as matches_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.opportunities import router as opportunities_router
from app.api.v1.payments import router as payments_router
from app.api.v1.profiles import router as profiles_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(profiles_router)
router.include_router(opportunities_router)
router.include_router(matches_router)
router.include_router(bookmarks_router)
router.include_router(notifications_router)
router.include_router(payments_router)



@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
