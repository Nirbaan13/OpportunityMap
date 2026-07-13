from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import OpportunityType
from app.schemas.profile import FieldOption


class OpportunitySort(str, Enum):
    DEADLINE_ASC = "deadline_asc"
    DEADLINE_DESC = "deadline_desc"
    NEWEST = "newest"
    TITLE = "title"


class OpportunitySummary(BaseModel):
    """Compact opportunity for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    opportunity_type: OpportunityType
    source_name: str
    source_url: str
    application_url: str | None
    deadline_at: datetime | None
    grade_eligibility: str | None
    grade_min: int | None
    grade_max: int | None
    eligible_countries: list[str] | None
    is_active: bool
    fields: list[FieldOption]


class OpportunityDetail(OpportunitySummary):
    """Full opportunity including description and experience requirements."""

    description: str | None
    experience_requirements: str | None
    external_id: str | None
    last_scraped_at: datetime | None
    created_at: datetime
    updated_at: datetime


class OpportunityListResponse(BaseModel):
    items: list[OpportunitySummary]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total_pages: int = Field(ge=0)
