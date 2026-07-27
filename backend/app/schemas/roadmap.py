from pydantic import BaseModel, Field

from app.schemas.match import MatchItem
from app.schemas.profile import FieldOption


class RoadmapFieldPlan(BaseModel):
    field: FieldOption
    yearly_target: int = Field(ge=0)
    selected_count: int = Field(ge=0)


class RoadmapStop(BaseModel):
    order: int = Field(ge=1)
    opportunity_id: int
    match: MatchItem
    has_deadline: bool
    primary_field: FieldOption
    is_strong_match: bool


class RoadmapResponse(BaseModel):
    grade_level: int
    target_per_field: int
    total_target: int
    field_plans: list[RoadmapFieldPlan]
    stops: list[RoadmapStop]
    summary: str
