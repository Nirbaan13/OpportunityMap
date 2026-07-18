from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.opportunity import OpportunitySummary

BookmarkStatus = Literal["saved", "completed"]


class BookmarkCreate(BaseModel):
    opportunity_id: int = Field(ge=1)
    remind_me: bool = False
    status: BookmarkStatus = "saved"


class BookmarkUpdate(BaseModel):
    remind_me: bool | None = None
    status: BookmarkStatus | None = None


class BookmarkItem(BaseModel):
    opportunity: OpportunitySummary
    remind_me: bool
    status: BookmarkStatus
    completed_at: datetime | None
    created_at: datetime


class BookmarkListResponse(BaseModel):
    items: list[BookmarkItem]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total_pages: int = Field(ge=0)
