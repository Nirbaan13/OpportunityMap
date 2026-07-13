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
    BookmarkUpdate,
)
from app.services import bookmark_service

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


def _to_item(bookmark) -> BookmarkItem:
    return BookmarkItem(
        opportunity=_to_summary(bookmark.opportunity),
        remind_me=bookmark.remind_me,
        created_at=bookmark.created_at,
    )


@router.get("", response_model=BookmarkListResponse)
def list_my_bookmarks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_premium),
    db: Session = Depends(get_db),
) -> BookmarkListResponse:
    """Saved opportunities for the logged-in student."""
    rows, total = bookmark_service.list_bookmarks(
        db, current_user, page=page, page_size=page_size
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
    """Set Remind me (creates a saved bookmark if turning on and none exists)."""
    bookmark = bookmark_service.set_remind_me(
        db, current_user, opportunity_id, payload.remind_me
    )
    return _to_item(bookmark)


@router.delete("/{opportunity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bookmark(
    opportunity_id: int,
    current_user: User = Depends(require_premium),
    db: Session = Depends(get_db),
) -> Response:
    bookmark_service.delete_bookmark(db, current_user, opportunity_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
