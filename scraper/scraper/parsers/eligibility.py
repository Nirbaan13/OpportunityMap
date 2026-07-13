"""Shared eligibility helpers for scrapers."""

from __future__ import annotations

import re

GRADUATE_MARKERS = (
    "postdoc",
    "post-doc",
    "ph.d",
    "phd",
    "doctorate",
    "doctoral",
    "graduate",
    "grad student",
    "early career",
    "faculty",
    "professional degree",
)

HIGH_SCHOOL_MARKERS = (
    "high school",
    "highschool",
    "secondary school",
    "pre-college",
    "precollege",
    "k-12",
    "ages 13",
    "ages 14",
    "ages 15",
    "ages 16",
    "ages 17",
)


def text_mentions_graduate_level(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in GRADUATE_MARKERS)


def text_mentions_high_school(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in HIGH_SCHOOL_MARKERS)


def is_high_school_program(
    academic_level: str | None,
    *,
    grade_min: int | None,
    grade_max: int | None,
) -> bool:
    """True when a program appears aimed at high-school students."""
    level = (academic_level or "").strip()
    if not level:
        return grade_max is not None and grade_max <= 12

    if text_mentions_graduate_level(level):
        # Allow mixed listings only when high school is explicitly included.
        if not text_mentions_high_school(level):
            return False

    if text_mentions_high_school(level):
        return True

    if grade_max is not None and grade_max <= 12:
        if grade_min is None or grade_min <= 12:
            return True

    # Undergrad-only listings are not high-school opportunities.
    if "undergraduate" in level.lower() and not text_mentions_high_school(level):
        return False

    return False


def devpost_blocks_high_schoolers(eligibility_items: list[str]) -> bool:
    """Skip Devpost hackathons that are explicitly adults-only."""
    for item in eligibility_items:
        lowered = item.lower()
        if re.search(r"ages?\s*18\+", lowered):
            return True
        if "18 and older" in lowered or "18+ only" in lowered:
            return True
    return False
