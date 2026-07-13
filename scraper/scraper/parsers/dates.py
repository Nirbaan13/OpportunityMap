import re
from datetime import UTC, datetime

from dateutil import parser as date_parser

# Ordered by priority for notification deadlines (registration close is most important).
DEADLINE_LABELS = [
    "registration closes",
    "application deadline",
    "submission deadline",
    "entries close",
    "deadline",
    "registration ends",
    "closes",
]

OPEN_LABELS = [
    "registration opens",
    "applications open",
    "opens",
]


def _clean_date_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" :-\u00a0")


def parse_date(value: str, *, end_of_day: bool = False) -> datetime | None:
    text = _clean_date_text(value)
    if not text:
        return None
    lowered = text.lower()
    if "ended" in lowered or "closed" in lowered and not re.search(r"\d{4}", text):
        return None
    try:
        parsed = date_parser.parse(text, fuzzy=True, default=datetime(2000, 1, 1, tzinfo=UTC))
        if end_of_day:
            parsed = parsed.replace(hour=23, minute=59, second=59, microsecond=0)
        else:
            parsed = parsed.replace(hour=0, minute=0, second=0, microsecond=0)
        return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)
    except (ValueError, OverflowError):
        return None


def extract_labeled_dates(text: str) -> dict[str, datetime]:
    """Extract dates from lines like 'Registration Closes: November 21, 2025'."""
    found: dict[str, datetime] = {}
    for raw_line in text.splitlines():
        line = _clean_date_text(raw_line)
        if ":" not in line:
            continue
        label, _, value = line.partition(":")
        label_key = label.strip().lower()
        is_close = any(token in label_key for token in ("close", "deadline", "due", "ends"))
        parsed = parse_date(value, end_of_day=is_close)
        if parsed is None:
            continue
        found[label_key] = parsed
    return found


def pick_notification_deadline(text: str) -> tuple[datetime | None, str | None]:
    """
    Return the best deadline datetime for user notifications and the label used.
    Prefers registration close over generic deadlines.
    """
    labeled = extract_labeled_dates(text)
    for label in DEADLINE_LABELS:
        for key, dt in labeled.items():
            if label in key:
                return dt, key

    for key, dt in labeled.items():
        if any(token in key for token in ("close", "deadline", "due")):
            return dt, key

    return None, None


def deadline_is_upcoming(deadline_at: datetime | None, *, now: datetime | None = None) -> bool:
    """True when a parseable deadline exists and is still in the future."""
    if deadline_at is None:
        return False
    reference = now or datetime.now(UTC)
    return deadline_at >= reference


def format_deadline_summary(text: str) -> str | None:
    """Human-readable deadline lines for storage/display."""
    labeled = extract_labeled_dates(text)
    if not labeled:
        return None
    priority_keys = []
    for label in DEADLINE_LABELS + OPEN_LABELS:
        for key in labeled:
            if label in key and key not in priority_keys:
                priority_keys.append(key)
    for key in labeled:
        if key not in priority_keys:
            priority_keys.append(key)

    lines = []
    for key in priority_keys:
        dt = labeled[key]
        lines.append(f"{key.title()}: {dt.strftime('%B %d, %Y')}")
    return "\n".join(lines)
