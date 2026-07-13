from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.opportunity import OpportunitySummary


class BookmarkCreate(BaseModel):
    opportunity_id: int = Field(ge=1)
    remind_me: bool = False


class BookmarkUpdate(BaseModel):
    remind_me: bool


class BookmarkItem(BaseModel):
    opportunity: OpportunitySummary
    remind_me: bool
    created_at: datetime


class BookmarkListResponse(BaseModel):
    items: list[BookmarkItem]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total_pages: int = Field(ge=0)
