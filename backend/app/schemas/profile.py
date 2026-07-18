from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class FieldOption(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class ActivityOption(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class FieldInsight(BaseModel):
    field: FieldOption
    completed_count: int
    planned_count: int
    status: str  # strong | ok | short


class ProfileWriteRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    location: str = Field(min_length=1, max_length=200)
    grade_level: int = Field(ge=6, le=12)
    country_code: str = Field(min_length=2, max_length=2)
    research_experience: str | None = Field(default=None, max_length=5000)
    olympiad_experience: str | None = Field(default=None, max_length=5000)
    interest_slugs: list[str] = Field(min_length=1)
    completed_activity_slugs: list[str] = Field(default_factory=list)
    planned_activity_slugs: list[str] = Field(default_factory=list)

    @field_validator("country_code")
    @classmethod
    def normalize_country_code(cls, value: str) -> str:
        return value.upper()

    @field_validator("interest_slugs", "completed_activity_slugs", "planned_activity_slugs")
    @classmethod
    def normalize_slugs(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(slug.strip().lower() for slug in value if slug.strip()))

    @model_validator(mode="after")
    def completed_wins_over_planned(self) -> "ProfileWriteRequest":
        completed = set(self.completed_activity_slugs)
        self.planned_activity_slugs = [
            slug for slug in self.planned_activity_slugs if slug not in completed
        ]
        return self


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    location: str
    grade_level: int
    country_code: str
    research_experience: str | None
    olympiad_experience: str | None
    interests: list[FieldOption]
    completed_activities: list[ActivityOption]
    planned_activities: list[ActivityOption]
    field_insights: list[FieldInsight]
    insight_summary: str
    created_at: datetime
    updated_at: datetime
