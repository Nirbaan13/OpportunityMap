from math import ceil

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.v1.opportunities import _to_summary
from app.core.deps import require_premium
from app.database import get_db
from app.models import User
from app.schemas.bookmark import (
    BookmarkCreate,
    BookmarkItem,
    BookmarkListResponse,
    BookmarkStatus,
    BookmarkUpdate,
)
from app.services import bookmark_service

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


def _to_item(bookmark) -> BookmarkItem:
    return BookmarkItem(
        opportunity=_to_summary(bookmark.opportunity),
        remind_me=bookmark.remind_me,
        status=bookmark.status,  # type: ignore[arg-type]
        completed_at=bookmark.completed_at,
        created_at=bookmark.created_at,
    )


@router.get("", response_model=BookmarkListResponse)
def list_my_bookmarks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: BookmarkStatus | None = Query(
        default=None,
        alias="status",
        description="Filter by saved or completed",
    ),
    current_user: User = Depends(require_premium),
    db: Session = Depends(get_db),
) -> BookmarkListResponse:
    """Saved / completed opportunities for the logged-in student."""
    rows, total = bookmark_service.list_bookmarks(
        db,
        current_user,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
    )
    total_pages = ceil(total / page_size) if total else 0
    return BookmarkListResponse(
        items=[_to_item(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=BookmarkItem, status_code=status.HTTP_201_CREATED)
def create_bookmark(
    payload: BookmarkCreate,
    current_user: User = Depends(require_premium),
    db: Session = Depends(get_db),
) -> BookmarkItem:
    bookmark = bookmark_service.create_bookmark(
        db,
        current_user,
        payload.opportunity_id,
        remind_me=payload.remind_me,
        status_value=payload.status,
    )
    return _to_item(bookmark)


@router.get("/{opportunity_id}", response_model=BookmarkItem)
def get_bookmark(
    opportunity_id: int,
    current_user: User = Depends(require_premium),
    db: Session = Depends(get_db),
) -> BookmarkItem:
    bookmark = bookmark_service.get_bookmark(db, current_user, opportunity_id)
    return _to_item(bookmark)


@router.patch("/{opportunity_id}", response_model=BookmarkItem)
def update_bookmark(
    opportunity_id: int,
    payload: BookmarkUpdate,
    current_user: User = Depends(require_premium),
    db: Session = Depends(get_db),
) -> BookmarkItem:
    """Update Remind me and/or saved vs completed status."""
    bookmark = None
    if payload.status is not None:
        bookmark = bookmark_service.set_status(
            db, current_user, opportunity_id, payload.status
        )
    if payload.remind_me is not None:
        bookmark = bookmark_service.set_remind_me(
            db, current_user, opportunity_id, payload.remind_me
        )
    if bookmark is None:
        bookmark = bookmark_service.get_bookmark(db, current_user, opportunity_id)
    return _to_item(bookmark)


@router.delete("/{opportunity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bookmark(
    opportunity_id: int,
    current_user: User = Depends(require_premium),
    db: Session = Depends(get_db),
) -> Response:
    bookmark_service.delete_bookmark(db, current_user, opportunity_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
