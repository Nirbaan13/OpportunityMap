"""Map free-text categories and titles to OpportunityMap field slugs."""

from __future__ import annotations

import re

# Keys are normalized category names from scrapers / sites.
CATEGORY_TO_FIELD_SLUG: dict[str, str] = {
    "ai": "ai",
    "artificial intelligence": "ai",
    "machine learning": "ai",
    "ml": "ai",
    "biology": "biology",
    "biomedical": "biology",
    "medicine": "biology",
    "genetics": "biology",
    "business": "business",
    "entrepreneurship": "business",
    "finance": "business",
    "chemistry": "chemistry",
    "biochemistry": "chemistry",
    "coding computer science": "computer-science",
    "computer science": "computer-science",
    "informatics": "computer-science",
    "programming": "computer-science",
    "coding": "computer-science",
    "cybersecurity": "computer-science",
    "economics": "economics",
    "econometrics": "economics",
    "engineering": "engineering",
    "robotics": "engineering",
    "mathematics": "mathematics",
    "math": "mathematics",
    "statistics": "mathematics",
    "physics": "physics",
    "astronomy": "physics",
    "astrophysics": "physics",
    "research": "research",
    "social science": "social-science",
    "social sciences": "social-science",
    "geography": "social-science",
    "history": "social-science",
    "psychology": "social-science",
    "political science": "social-science",
    "sociology": "social-science",
    "philosophy": "social-science",
    "law": "social-science",
    "writing": "writing",
    "literature": "writing",
    "poetry": "writing",
    "essay": "writing",
    "journalism": "writing",
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
    "data science": "computer-science",
    "stem": "engineering",
    "programming language": "computer-science",
    "cyber security": "computer-science",
    "technology": "computer-science",
}

# Keyword → field (checked against title + description).
KEYWORD_FIELD_HINTS: list[tuple[str, str]] = [
    (r"\b(artificial intelligence|machine learning|\bai\b|\bml\b|neural|llm)\b", "ai"),
    (r"\b(biology|biomed|genetic|genome|neuroscience|medicine|health)\b", "biology"),
    (r"\b(business|entrepreneur|startup|finance|marketing|deca|fbla)\b", "business"),
    (r"\b(chemistry|chemical|biochem|icho)\b", "chemistry"),
    (r"\b(computer science|informatics|programming|coding|hackathon|usaco|ioi)\b", "computer-science"),
    (r"\b(economics|econometrics|ieo|econ)\b", "economics"),
    (r"\b(engineering|robotics|first robotics|mechanical|electrical)\b", "engineering"),
    (r"\b(mathematics|math olympiad|imo|amc|aime|usamo)\b", "mathematics"),
    (r"\b(physics|astronomy|astrophysics|ipho|uspho)\b", "physics"),
    (r"\b(research|internship|reu|rsi|isef|sts)\b", "research"),
    (r"\b(social science|geography|history|psychology|philosophy|debate|model un)\b", "social-science"),
    (r"\b(writing|essay|poetry|literature|journalism|scholastic)\b", "writing"),
]


def normalize_category(name: str) -> str:
    text = re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()
    return re.sub(r"\s+", " ", text)


def categories_to_field_slugs(categories_text: str) -> list[str]:
    slugs: list[str] = []
    for part in re.split(r"[,;/|]", categories_text):
        normalized = normalize_category(part)
        if not normalized:
            continue
        slug = CATEGORY_TO_FIELD_SLUG.get(normalized)
        if slug and slug not in slugs:
            slugs.append(slug)
        else:
            # Partial match: "AP Biology" → biology
            for key, value in CATEGORY_TO_FIELD_SLUG.items():
                if key in normalized or normalized in key:
                    if value not in slugs:
                        slugs.append(value)
                    break
    return slugs


def infer_field_slugs(*texts: str | None) -> list[str]:
    """Infer interest fields from free text (title, description, themes)."""
    blob = " ".join(t for t in texts if t).lower()
    if not blob:
        return []
    slugs: list[str] = []
    for pattern, slug in KEYWORD_FIELD_HINTS:
        if re.search(pattern, blob, flags=re.IGNORECASE) and slug not in slugs:
            slugs.append(slug)
    return slugs


def merge_field_slugs(*groups: list[str]) -> list[str]:
    merged: list[str] = []
    for group in groups:
        for slug in group:
            if slug not in merged:
                merged.append(slug)
    return merged
