"""Map Institute of Competition Sciences categories to OpportunityMap field slugs."""

from __future__ import annotations

import re

# Keys are normalized category names from the ICS site.
CATEGORY_TO_FIELD_SLUG: dict[str, str] = {
    "ai": "ai",
    "artificial intelligence": "ai",
    "biology": "biology",
    "business": "business",
    "chemistry": "chemistry",
    "coding computer science": "computer-science",
    "computer science": "computer-science",
    "economics": "economics",
    "engineering": "engineering",
    "mathematics": "mathematics",
    "math": "mathematics",
    "physics": "physics",
    "research": "research",
    "social science": "social-science",
    "writing": "writing",
    "literature": "writing",
    "poetry": "writing",
    "stem fields": "research",
    "life sciences": "biology",
    "physical sciences": "physics",
    "earth sciences": "physics",
    "geosciences": "physics",
    "ocean sciences": "biology",
    "environmental science": "biology",
    "biomedical sciences": "biology",
    "neuroscience": "biology",
    "materials science": "chemistry",
    "astronomy": "physics",
    "astrophysics": "physics",
    "statistics": "mathematics",
    "data science": "computer-science",
    "stem": "engineering",
    "robotics": "engineering",
    "programming language": "computer-science",
    "cyber security": "computer-science",
    "technology": "computer-science",
}


def normalize_category(name: str) -> str:
    text = re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()
    return re.sub(r"\s+", " ", text)


def categories_to_field_slugs(categories_text: str) -> list[str]:
    slugs: list[str] = []
    for part in categories_text.split(","):
        normalized = normalize_category(part)
        if not normalized:
            continue
        slug = CATEGORY_TO_FIELD_SLUG.get(normalized)
        if slug and slug not in slugs:
            slugs.append(slug)
    return slugs
