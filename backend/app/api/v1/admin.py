import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.schemas.admin import (
    AdminCountRow,
    AdminOverviewResponse,
    AdminPaymentRow,
    AdminTotals,
    AdminUserRow,
)
from app.services.admin_service import build_admin_overview

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(x_admin_password: str | None = Header(default=None)) -> None:
    configured = settings.admin_password.strip()
    if not configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin is not configured. Set ADMIN_PASSWORD on the API.",
        )
    provided = (x_admin_password or "").strip()
    if not provided or not secrets.compare_digest(provided, configured):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin password",
        )


@router.get("/overview", response_model=AdminOverviewResponse)
def admin_overview(
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminOverviewResponse:
    """Founder dashboard: users, premium, payments, listings."""
    data = build_admin_overview(db)
    return AdminOverviewResponse(
        totals=AdminTotals(**data["totals"]),
        payments_by_status=[AdminCountRow(**row) for row in data["payments_by_status"]],
        payments_by_provider=[AdminCountRow(**row) for row in data["payments_by_provider"]],
        recent_users=[AdminUserRow(**row) for row in data["recent_users"]],
        recent_payments=[AdminPaymentRow(**row) for row in data["recent_payments"]],
    )
