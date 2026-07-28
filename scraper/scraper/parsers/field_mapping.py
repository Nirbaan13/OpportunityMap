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
# Keep social-science hints academic (not "education" / "social good" / "social impact").
KEYWORD_FIELD_HINTS: list[tuple[str, str]] = [
    (r"\b(artificial intelligence|machine learning|\bai\b|\bml\b|neural|llm)\b", "ai"),
    (r"\b(biology|biomed|genetic|genome|neuroscience|medicine|health)\b", "biology"),
    (r"\b(business|entrepreneur|startup|finance|marketing|deca|fbla)\b", "business"),
    (r"\b(chemistry|chemical|biochem|icho)\b", "chemistry"),
    (
        r"\b(computer science|informatics|programming|coding|hackathon|software|"
        r"developer|devpost|usaco|ioi)\b",
        "computer-science",
    ),
    (r"\b(economics|econometrics|ieo|econ)\b", "economics"),
    (r"\b(engineering|robotics|first robotics|mechanical|electrical)\b", "engineering"),
    (r"\b(mathematics|math olympiad|imo|amc|aime|usamo)\b", "mathematics"),
    (r"\b(physics|astronomy|astrophysics|ipho|uspho)\b", "physics"),
    (r"\b(research|internship|reu|rsi|isef|sts)\b", "research"),
    (
        r"\b(social science|geography|psychology|sociology|political science|"
        r"anthropology|civics|debate|model un|mun|"
        r"history bee|history bowl|history olympiad)\b",
        "social-science",
    ),
    (r"\b(writing|essay|poetry|literature|journalism|scholastic)\b", "writing"),
]

# Academic social-science signals strong enough to keep the tag on a hackathon.
# Deliberately excludes "education", "history", "philosophy", and "social good/impact"
# which appear on many Devpost EdTech / SDG hackathons.
_STRONG_SOCIAL_SCIENCE = re.compile(
    r"\b(social science|geography|psychology|sociology|political science|"
    r"anthropology|civics|debate|model un|mun)\b",
    flags=re.IGNORECASE,
)

# Short category keys that must match as whole tokens (avoid "law" ⊂ "lawrence").
_WHOLE_TOKEN_CATEGORY_KEYS = frozenset(
    {
        "ai",
        "ml",
        "math",
        "law",
        "stem",
        "essay",
        "econ",
    }
)


def normalize_category(name: str) -> str:
    text = re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()
    return re.sub(r"\s+", " ", text)


def _partial_category_match(normalized: str, key: str) -> bool:
    """True when category key and text overlap without substring false positives."""
    if key in _WHOLE_TOKEN_CATEGORY_KEYS or len(key) <= 3:
        return bool(re.search(rf"\b{re.escape(key)}\b", normalized))
    return key in normalized or normalized in key


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
            # Partial match: "AP Biology" → biology (token-safe for short keys).
            for key, value in CATEGORY_TO_FIELD_SLUG.items():
                if _partial_category_match(normalized, key):
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


def _is_hackathon_context(opportunity_type: str | None, blob: str) -> bool:
    ot = (opportunity_type or "").strip().lower().replace("-", "_")
    if ot == "hackathon":
        return True
    return bool(re.search(r"\bhackathon\b", blob, flags=re.IGNORECASE))


def refine_field_slugs(
    slugs: list[str],
    *texts: str | None,
    opportunity_type: str | None = None,
) -> list[str]:
    """Post-process field tags so tech events are not mislabeled as Social Science.

    Hackathons (and titles containing \"hackathon\") always keep computer-science and
    only retain social-science when academic social-science signals are present —
    not Devpost \"Education\" / social-good themes.
    """
    result = merge_field_slugs(slugs)
    blob = " ".join(t for t in texts if t)
    if not _is_hackathon_context(opportunity_type, blob):
        return result

    if "computer-science" not in result:
        result.append("computer-science")

    if "social-science" in result and not _STRONG_SOCIAL_SCIENCE.search(blob):
        result = [slug for slug in result if slug != "social-science"]

    return result


def classify_field_slugs(
    *texts: str | None,
    categories_text: str | None = None,
    source_slugs: list[str] | None = None,
    opportunity_type: str | None = None,
) -> list[str]:
    """Full classify path used by scrapers and DB backfill."""
    category_slugs = categories_to_field_slugs(categories_text) if categories_text else []
    inferred = infer_field_slugs(*texts)
    merged = merge_field_slugs(source_slugs or [], category_slugs, inferred)
    return refine_field_slugs(merged, *texts, opportunity_type=opportunity_type)
