from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import NotificationType
from app.schemas.opportunity import OpportunitySummary


class NotificationItem(BaseModel):
    id: int
    notification_type: NotificationType
    title: str
    message: str
    is_read: bool
    reminder_lead_days: int | None = None
    opportunity: OpportunitySummary | None = None
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationItem]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total_pages: int = Field(ge=0)
    unread_count: int = Field(ge=0)


class UnreadCountResponse(BaseModel):
    unread_count: int = Field(ge=0)
