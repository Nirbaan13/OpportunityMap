from app.schemas.opportunity import OpportunitySummary
from app.schemas.profile import FieldOption
from pydantic import BaseModel, Field


class MatchItem(BaseModel):
    opportunity: OpportunitySummary
    score: int = Field(ge=0, description="Higher = better fit for this student")
    shared_fields: list[FieldOption]
    reasons: list[str]


class MatchListResponse(BaseModel):
    items: list[MatchItem]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total_pages: int = Field(ge=0)
