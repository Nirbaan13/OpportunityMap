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

# Sentinel year used so dateutil can fill in a missing year; we then roll it to the
# next upcoming occurrence when the source text has no explicit 4-digit year.
_SENTINEL_YEAR = 1900

# Separators used when a source expresses a window ("Nov 1 - Dec 15"); we treat the
# tail as the deadline (the date the window closes).
_RANGE_SEPARATORS = (" through ", " to ", " – ", " — ", " - ", "–", "—")

# Month names / common numeric formats, used to pull a date out of an unlabeled line.
_DATE_REGEX = re.compile(
    r"(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s*\d{4})?)"
    r"|(?:\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?(?:,?\s*\d{4})?)"
    r"|(?:\d{4}-\d{1,2}-\d{1,2})"
    r"|(?:\d{1,2}/\d{1,2}/\d{2,4})",
    re.IGNORECASE,
)

_CLOSE_TOKENS = ("close", "deadline", "due", "ends", "end")


def _clean_date_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" :-\u00a0")


def _range_end(text: str) -> str:
    """For a window like 'Nov 1 - Dec 15, 2025' return the closing side ('Dec 15, 2025')."""
    lowered = text.lower()
    for sep in _RANGE_SEPARATORS:
        idx = lowered.rfind(sep)
        if idx != -1:
            tail = text[idx + len(sep):].strip()
            if tail and re.search(r"\d", tail):
                return tail
    return text


def _has_explicit_year(text: str) -> bool:
    return re.search(r"\b\d{4}\b", text) is not None


def _roll_year_forward(parsed: datetime, *, now: datetime) -> datetime:
    """Assume a yearless date refers to its next upcoming occurrence."""
    try:
        candidate = parsed.replace(year=now.year)
    except ValueError:
        # e.g. Feb 29 on a non-leap year — nudge to Mar 1.
        candidate = parsed.replace(year=now.year, day=28)
    if candidate.date() < now.date():
        try:
            candidate = candidate.replace(year=now.year + 1)
        except ValueError:
            candidate = candidate.replace(year=now.year + 1, day=28)
    return candidate


def parse_date(
    value: str,
    *,
    end_of_day: bool = False,
    now: datetime | None = None,
) -> datetime | None:
    text = _clean_date_text(value)
    if not text:
        return None
    lowered = text.lower()
    if ("ended" in lowered or "closed" in lowered) and not _has_explicit_year(text):
        return None

    text = _range_end(text)
    explicit_year = _has_explicit_year(text)
    reference = now or datetime.now(UTC)
    try:
        parsed = date_parser.parse(
            text, fuzzy=True, default=datetime(_SENTINEL_YEAR, 1, 1, tzinfo=UTC)
        )
    except (ValueError, OverflowError):
        return None

    if not explicit_year or parsed.year == _SENTINEL_YEAR:
        parsed = _roll_year_forward(parsed, now=reference)

    if end_of_day:
        parsed = parsed.replace(hour=23, minute=59, second=59, microsecond=0)
    else:
        parsed = parsed.replace(hour=0, minute=0, second=0, microsecond=0)
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)


def _matched_label(lowered_line: str) -> str | None:
    """Return the highest-priority deadline/open label mentioned in a line, if any."""
    for label in DEADLINE_LABELS + OPEN_LABELS:
        if label in lowered_line:
            return label
    return None


def extract_labeled_dates(text: str) -> dict[str, datetime]:
    """Extract dates from lines like 'Registration Closes: November 21, 2025'.

    Also handles unlabeled-colon lines ('Application Deadline November 21, 2025')
    by pairing a deadline/open keyword with the first date found on the same line.
    """
    found: dict[str, datetime] = {}
    for raw_line in text.splitlines():
        line = _clean_date_text(raw_line)
        if not line:
            continue

        if ":" in line:
            label, _, value = line.partition(":")
            label_key = label.strip().lower()
            is_close = any(token in label_key for token in _CLOSE_TOKENS)
            parsed = parse_date(value, end_of_day=is_close)
            if parsed is not None:
                found[label_key] = parsed
                continue

        # Fallback: a keyword and a date sharing a line, without a clean "label: value".
        lowered = line.lower()
        label = _matched_label(lowered)
        if label is None:
            continue
        match = _DATE_REGEX.search(line)
        if match is None:
            continue
        is_close = any(token in label for token in _CLOSE_TOKENS)
        parsed = parse_date(match.group(0), end_of_day=is_close)
        if parsed is not None:
            found.setdefault(label, parsed)
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
