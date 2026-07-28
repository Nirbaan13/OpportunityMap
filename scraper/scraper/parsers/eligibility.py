"""Shared eligibility helpers for scrapers."""

from __future__ import annotations

import re

from app.models.enums import OpportunityType

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


WORLDWIDE_MARKERS = (
    "worldwide",
    "around the world",
    "from around the world",
    "international participants",
    "open worldwide",
    "globally",
    "global applicants",
    "students worldwide",
    "global competition",
    "global olympiad",
    "global conferences",
    "international competition",
    "international olympiad",
    "international essay",
    "international history",
    "international space",
    "international online",
    "open to students from all countries",
    "open to all countries",
    "any country",
    "all countries",
        "future problem solving program international",
    "model united nations",
    "advent of code",
    "kaggle",
    "leetcode",
    "codechef",
    "robocup",
    "online physics olympiad",
)

# Longest / most specific markers first where needed. Word-ish tokens are fine;
# we search the lowercased blob, not tokenized words.
COUNTRY_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "US",
        (
            "united states",
            "u.s.a",
            "u.s.",
            " usa",
            "usa ",
            "(usa)",
            "(us)",
            "american ",
            "americans",
            "u.s.-",
            "us-only",
            "u.s only",
            "us only",
            ".edu",
            "new york",
            "california",
            "massachusetts",
            "boston",
            "stanford",
            "princeton",
            "harvard",
            "yale ",
            "mit ",
            "caltech",
            "berkeley",
            "columbia university",
            "nyu ",
            "wharton",
            "rockefeller",
            "nasa ",
            "noaa ",
            "nsf ",
            "usamo",
            "usaco",
            "usabo",
            "usapho",
            "usnco",
            "mathcounts",
            "regeneron",
            "intel isef",
            "science olympiad",
            "first robotics",
            "first tech challenge",
            "vex robotics",
            "deca ",
            "fbla",
            "promys",
            "ross mathematics",
            "rsi ",
            "ssp ",
            "summer science program",
            "pathwaystoscience.org",
            "aapt.org",
            "maa.org",
            "artofproblemsolving.com",
            "cyberpatriot",
            "project seed",
            "scholastic art",
            "nsda",
            "speech & debate",
            "telluride association",
            "hampshire college",
            "economics challenge",
            "profile in courage",
            "congressional app",
            "questbridge",
            "coca-cola scholars",
            "bank of america student",
            "clark scholars",
            "garcia summer",
            "stony brook",
            "texas tech",
            "national history bee",
            "hosa ",
            "jshs",
            "junior science and humanities",
            "astro pi",
            "cansat",
            "kick start",
        ),
    ),
    (
        "CA",
        (
            "canada",
            "canadian",
            "waterloo",
            "cemc",
            "toronto",
            "montreal",
            "vancouver",
            "ottawa",
        ),
    ),
    (
        "GB",
        (
            "united kingdom",
            "u.k.",
            " uk ",
            "(uk)",
            "britain",
            "british",
            "england",
            "scotland",
            "wales",
            "cambridge",
            "oxford",
            "ukmt",
            "foyle",
            "john locke",
            "peterhouse",
            ".ac.uk",
        ),
    ),
    (
        "AU",
        (
            "australia",
            "australian",
            "sydney",
            "melbourne",
            "canberra",
            ".edu.au",
        ),
    ),
    (
        "IN",
        (
            "india",
            "indian ",
            "iit ",
            "hbcse",
            "atal ",
            "technothlon",
            "inmo",
            "inoi",
            "kvpy",
            "ntse",
            "sof olympiad",
            "sof ",
            ".gov.in",
            ".ac.in",
            "mumbai",
            "delhi",
            "bangalore",
            "bengaluru",
            "chennai",
            "hyderabad",
        ),
    ),
    ("SG", ("singapore", "singaporean", ".edu.sg")),
    ("ZA", ("south africa", "south african")),
    ("NZ", ("new zealand", "auckland", "wellington")),
    ("IE", ("ireland", "irish", "dublin")),
    ("DE", ("germany", "german ", "berlin", "munich", ".de/")),
    ("FR", ("france", "french ", "paris", ".fr/")),
    ("JP", ("japan", "japanese", "tokyo", ".jp/")),
    ("KR", ("south korea", "korea", "korean", "seoul", ".kr/")),
    ("CN", ("china", "chinese", "beijing", "shanghai")),
    ("HK", ("hong kong",)),
    ("AE", ("united arab emirates", "u.a.e", "dubai", "abu dhabi")),
    ("BR", ("brazil", "brazilian", "sao paulo", "são paulo")),
    ("MX", ("mexico", "mexican")),
    ("NL", ("netherlands", "dutch ", "amsterdam")),
    ("SE", ("sweden", "swedish", "stockholm")),
    ("CH", ("switzerland", "swiss ", "zurich", "geneva")),
    ("IT", ("italy", "italian", "rome", "milan")),
    ("ES", ("spain", "spanish", "madrid", "barcelona")),
    ("PK", ("pakistan", "pakistani")),
    ("BD", ("bangladesh", "bangladeshi")),
    ("NG", ("nigeria", "nigerian")),
    ("KE", ("kenya", "kenyan")),
    ("PH", ("philippines", "filipino", "manila")),
    ("MY", ("malaysia", "malaysian")),
    ("ID", ("indonesia", "indonesian")),
    ("TR", ("turkey", "turkish", "ankara", "istanbul")),
    ("IL", ("israel", "israeli", "tel aviv")),
    ("RU", ("russia", "russian", "moscow")),
    ("UA", ("ukraine", "ukrainian", "kyiv", "kiev")),
    ("PL", ("poland", "polish", "warsaw")),
    ("PT", ("portugal", "portuguese", "lisbon")),
    ("RO", ("romania", "romanian")),
    ("GR", ("greece", "greek ", "athens")),
    ("EG", ("egypt", "egyptian", "cairo")),
    ("SA", ("saudi arabia", "saudi")),
    ("QA", ("qatar", "doha")),
    ("KW", ("kuwait",)),
    ("BH", ("bahrain",)),
    ("OM", ("oman",)),
    ("LK", ("sri lanka",)),
    ("NP", ("nepal", "nepalese")),
    ("TW", ("taiwan", "taiwanese", "taipei")),
    ("VN", ("vietnam", "vietnamese")),
    ("TH", ("thailand", "thai ", "bangkok")),
    ("AR", ("argentina", "argentinian", "buenos aires")),
    ("CL", ("chile", "chilean", "santiago")),
    ("CO", ("colombia", "colombian", "bogota", "bogotá")),
    ("PE", ("peru", "peruvian", "lima")),
    ("GH", ("ghana", "ghanaian")),
    ("GE", ("georgia", "tbilisi")),
    ("KZ", ("kazakhstan",)),
    ("RS", ("serbia", "serbian")),
)


def _looks_international_olympiad(
    combined: str,
    *,
    title: str | None,
    opportunity_type: OpportunityType | None,
) -> bool:
    title_l = (title or "").lower().strip()
    if title_l.startswith("international "):
        return True
    if opportunity_type == OpportunityType.OLYMPIAD and "olympiad" in title_l:
        return True
    if re.search(r"\binternational\b.{0,40}\b(olympiad|tournament|contest|competition)\b", combined):
        return True
    if re.search(r"\bworld\b.{0,20}\bolympiad\b", combined):
        return True
    return False


def infer_eligible_countries(
    *texts: str | None,
    scope: str | None = None,
    title: str | None = None,
    opportunity_type: OpportunityType | None = None,
    online_worldwide_if_unspecified: bool = False,
    default_countries: list[str] | None = None,
) -> list[str] | None:
    """
    Best-effort region inference.

    Returns:
      []     -> worldwide / global
      [..]   -> explicit eligible country codes
      None   -> country not confidently determined
    """
    parts = [text.strip() for text in texts if text and text.strip()]
    if title and title.strip():
        parts.insert(0, title.strip())
    combined = " ".join(parts).lower()
    # Pad so edge tokens like "usa" / "uk" match cleanly.
    padded = f" {combined} "
    scope_text = (scope or "").strip().lower()

    if scope_text in {"global", "international", "worldwide"}:
        return []

    if _looks_international_olympiad(
        combined, title=title, opportunity_type=opportunity_type
    ):
        return []

    if any(marker in combined for marker in WORLDWIDE_MARKERS):
        return []

    # Explicit parenthetical region tags in titles: "(US)", "(UK)", "(India)"
    paren = re.findall(r"\(([a-z]{2,3})\)", combined)
    paren_map = {"us": "US", "usa": "US", "uk": "GB", "ind": "IN", "ca": "CA", "au": "AU"}
    paren_codes = [paren_map[p] for p in paren if p in paren_map]
    if paren_codes:
        return list(dict.fromkeys(paren_codes))

    found: list[str] = []
    for code, markers in COUNTRY_PATTERNS:
        hit = False
        for marker in markers:
            marker_l = marker.lower()
            # Prefer word-boundary matches for alphabetic country names so
            # "indiana" does not count as India, etc.
            if marker_l.isalpha() or " " not in marker_l.strip():
                if re.search(rf"(?<![a-z]){re.escape(marker_l.strip())}(?![a-z])", padded):
                    hit = True
                    break
            if marker_l in padded:
                hit = True
                break
        if hit:
            found.append(code)
    if found:
        seen: set[str] = set()
        ordered: list[str] = []
        for code in found:
            if code not in seen:
                seen.add(code)
                ordered.append(code)
        return ordered

    if scope_text == "national":
        return ["US"]

    if online_worldwide_if_unspecified:
        return []

    if default_countries is not None:
        return list(default_countries)

    return None
