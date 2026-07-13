import re

AGE_TO_GRADES: dict[str, tuple[int | None, int | None]] = {
    "elementary school": (1, 5),
    "middle school": (6, 8),
    "high school": (9, 12),
    "highschool": (9, 12),
    "undergraduate": (13, 16),
    "graduate": (17, 20),
    "postdoc": (17, 20),
    "early career": (17, 20),
}


def parse_grade_eligibility(ages_text: str) -> tuple[str, int | None, int | None]:
    """
    Convert ICS ages text (e.g. 'High School, Undergraduate') to grade range.
    Returns (original text, grade_min, grade_max).
    """
    cleaned = re.sub(r"\s+", " ", ages_text).strip()
    if not cleaned:
        return "", None, None

    mins: list[int] = []
    maxs: list[int] = []
    lowered = cleaned.lower()
    for label, (grade_min, grade_max) in AGE_TO_GRADES.items():
        if label in lowered:
            if grade_min is not None:
                mins.append(grade_min)
            if grade_max is not None:
                maxs.append(grade_max)

    if not mins or not maxs:
        return cleaned, None, None
    return cleaned, min(mins), max(maxs)
