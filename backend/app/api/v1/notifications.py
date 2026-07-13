from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.v1.opportunities import _to_summary
from app.core.deps import require_premium
from app.database import get_db
from app.models import Notification, Opportunity, User
from app.schemas.notification import (
    NotificationItem,
    NotificationListResponse,
    UnreadCountResponse,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _to_item(notification: Notification) -> NotificationItem:
    opportunity = None
    if notification.opportunity is not None:
        opportunity = _to_summary(notification.opportunity)
    return NotificationItem(
        id=notification.id,
        notification_type=notification.notification_type,
        title=notification.title,
        message=notification.message,
        is_read=notification.is_read,
        reminder_lead_days=notification.reminder_lead_days,
        opportunity=opportunity,
        created_at=notification.created_at,
    )


def _base_query(user_id: int):
    return (
        select(Notification)
        .options(
            joinedload(Notification.opportunity).joinedload(Opportunity.fields),
        )
        .where(Notification.user_id == user_id)
    )


@router.get("", response_model=NotificationListResponse)
def list_my_notifications(
    unread_only: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_premium),
    db: Session = Depends(get_db),
) -> NotificationListResponse:
    filters = [Notification.user_id == current_user.id]
    if unread_only:
        filters.append(Notification.is_read.is_(False))

    total = (
        db.scalar(select(func.count()).select_from(Notification).where(*filters)) or 0
    )
    unread_count = (
        db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == current_user.id,
                Notification.is_read.is_(False),
            )
        )
        or 0
    )

    query = _base_query(current_user.id)
    if unread_only:
        query = query.where(Notification.is_read.is_(False))

    rows = list(
        db.scalars(
            query.order_by(Notification.created_at.desc(), Notification.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .unique()
        .all()
    )
    total_pages = ceil(total / page_size) if total else 0
    return NotificationListResponse(
        items=[_to_item(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        unread_count=unread_count,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
def unread_count(
    current_user: User = Depends(require_premium),
    db: Session = Depends(get_db),
) -> UnreadCountResponse:
    count = (
        db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == current_user.id,
                Notification.is_read.is_(False),
            )
        )
        or 0
    )
    return UnreadCountResponse(unread_count=count)


@router.post("/{notification_id}/read", response_model=NotificationItem)
def mark_read(
    notification_id: int,
    current_user: User = Depends(require_premium),
    db: Session = Depends(get_db),
) -> NotificationItem:
    notification = db.scalar(
        _base_query(current_user.id).where(Notification.id == notification_id)
    )
    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    notification.is_read = True
    db.commit()
    notification = db.scalar(
        _base_query(current_user.id).where(Notification.id == notification_id)
    )
    assert notification is not None
    return _to_item(notification)


@router.post("/read-all", response_model=UnreadCountResponse)
def mark_all_read(
    current_user: User = Depends(require_premium),
    db: Session = Depends(get_db),
) -> UnreadCountResponse:
    rows = list(
        db.scalars(
            select(Notification).where(
                Notification.user_id == current_user.id,
                Notification.is_read.is_(False),
            )
        ).all()
    )
    for row in rows:
        row.is_read = True
    db.commit()
    return UnreadCountResponse(unread_count=0)
