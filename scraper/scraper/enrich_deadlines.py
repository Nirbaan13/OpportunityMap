"""Fetch official program pages and fill in missing deadline_at values.

Catalog seeds intentionally leave most rows undated (dates shift yearly). This
pass visits each undated listing's official site, discovers likely deadline
pages (apply / dates / calendar links), runs the shared date parser, and writes
a concrete upcoming deadline when one is clearly labeled.
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Opportunity
from scraper.curl_client import CurlClient
from scraper.deadline_pages import DEADLINE_PAGE_OVERRIDES
from scraper.parsers.dates import (
    deadline_is_upcoming,
    format_deadline_summary,
    pick_notification_deadline,
)

logger = logging.getLogger(__name__)

CATALOG_SOURCES = (
    "field_coverage_catalog",
    "expanded_catalog",
    "solid_programs_catalog",
    "global_competitions",
)

_DEADLINE_LINK_TOKENS = (
    "deadline",
    "deadlines",
    "dates",
    "important dates",
    "key dates",
    "timeline",
    "schedule",
    "calendar",
    "apply",
    "application",
    "applications",
    "how to apply",
    "apply now",
    "registration",
    "register",
    "participate",
    "admissions",
    "admission",
    "submission",
)

# Only the highest-value path guesses (kept short — bad guesses time out).
_PATH_SUFFIXES = (
    "/apply",
    "/application",
    "/deadlines",
    "/dates",
    "/important-dates",
    "/how-to-apply",
)

_MAX_FOLLOW_LINKS = 3
_MAX_URLS_PER_ROW = 6
_FETCH_TIMEOUT = 20

_SCRIPT_STYLE = re.compile(r"<(script|style|noscript)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)


def _page_text(html: str) -> str:
    cleaned = _SCRIPT_STYLE.sub(" ", html)
    soup = BeautifulSoup(cleaned, "lxml")
    for tag in soup(["script", "style", "noscript", "svg", "nav", "footer", "header"]):
        tag.decompose()
    return soup.get_text("\n", strip=True)


def _same_site(base: str, candidate: str) -> bool:
    try:
        b = urlparse(base)
        c = urlparse(candidate)
    except ValueError:
        return False
    if not c.scheme.startswith("http"):
        return False
    return (c.netloc or "").lower().removeprefix("www.") == (b.netloc or "").lower().removeprefix("www.")


def _normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    return urlunparse((parsed.scheme, parsed.netloc, path, "", parsed.query, ""))


def _origin(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _seed_urls(row: Opportunity) -> list[str]:
    urls: list[str] = []
    # Curated deadline pages first — these are usually where dates live.
    for value in DEADLINE_PAGE_OVERRIDES.get(row.external_id or "", []):
        if value.startswith("http"):
            normalized = _normalize_url(value)
            if normalized not in urls:
                urls.append(normalized)
    for value in (row.application_url, row.source_url):
        if not value or not value.startswith("http"):
            continue
        normalized = _normalize_url(value)
        if normalized not in urls:
            urls.append(normalized)
    return urls


def _suffix_urls(seed: str) -> list[str]:
    origin = _origin(seed)
    out: list[str] = []
    for suffix in _PATH_SUFFIXES:
        candidate = _normalize_url(origin + suffix)
        if candidate not in out and candidate != _normalize_url(seed):
            out.append(candidate)
    return out


def _discover_deadline_links(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    scored: list[tuple[int, str]] = []
    seen: set[str] = set()

    for link in soup.select("a[href]"):
        href = (link.get("href") or "").strip()
        if not href or href.startswith("#") or href.lower().startswith(("mailto:", "javascript:", "tel:")):
            continue
        absolute = urljoin(base_url, href)
        if not _same_site(base_url, absolute):
            continue
        normalized = _normalize_url(absolute)
        if normalized in seen or normalized == _normalize_url(base_url):
            continue
        seen.add(normalized)

        label = f"{link.get_text(' ', strip=True)} {href}".lower()
        score = 0
        for token in _DEADLINE_LINK_TOKENS:
            if token in label:
                if token in ("deadline", "deadlines", "important dates", "key dates", "dates"):
                    score += 5
                elif token in ("apply", "application", "applications", "how to apply", "apply now"):
                    score += 4
                else:
                    score += 2
        if score <= 0:
            continue
        scored.append((score, normalized))

    scored.sort(key=lambda item: (-item[0], item[1]))
    return [url for _score, url in scored[:_MAX_FOLLOW_LINKS]]


def _append_deadline_summary(description: str | None, summary: str) -> str:
    block = f"Deadlines:\n{summary}"
    text = (description or "").strip()
    if "Deadlines:" in text:
        head, _, _rest = text.partition("Deadlines:")
        return f"{head.strip()}\n\n{block}".strip()
    return f"{text}\n\n{block}".strip() if text else block


def _fetch_html(client: CurlClient, url: str) -> str | None:
    try:
        return client.fetch_html(url, timeout=_FETCH_TIMEOUT)
    except Exception as exc:
        logger.debug("Fetch failed for %s: %s", url, exc)
        return None


def enrich_catalog_deadlines(
    db: Session,
    client: CurlClient,
    *,
    max_items: int = 0,
    delay_seconds: float = 1.0,
) -> dict[str, int]:
    """Best-effort deadline enrichment for undated catalog opportunities."""
    stats = {
        "candidates": 0,
        "fetched": 0,
        "pages_checked": 0,
        "enriched": 0,
        "no_deadline_found": 0,
        "past_deadline": 0,
        "fetch_failed": 0,
        "skipped": 0,
    }

    stmt = (
        select(Opportunity)
        .where(Opportunity.is_active.is_(True))
        .where(Opportunity.deadline_at.is_(None))
        .where(Opportunity.source_name.in_(CATALOG_SOURCES))
        .order_by(Opportunity.id.asc())
    )
    rows = list(db.scalars(stmt).all())
    if max_items > 0:
        rows = rows[:max_items]

    stats["candidates"] = len(rows)
    logger.info(
        "Enriching deadlines for %s undated catalog opportunit(ies) (deep page discovery)",
        len(rows),
    )
    _ = delay_seconds

    for index, row in enumerate(rows, start=1):
        seeds = _seed_urls(row)
        if not seeds:
            stats["skipped"] += 1
            continue

        html_by_url: dict[str, str] = {}
        queue: list[str] = []
        for seed in seeds:
            if seed not in queue:
                queue.append(seed)

        found_deadline = None
        found_label = None
        found_summary = None
        fetched_ok = False
        used_suffixes = False

        i = 0
        while i < len(queue) and i < _MAX_URLS_PER_ROW:
            url = queue[i]
            i += 1

            html = html_by_url.get(url)
            if html is None:
                html = _fetch_html(client, url)
                if html is None:
                    continue
                fetched_ok = True
                stats["fetched"] += 1
                html_by_url[url] = html

                for link in _discover_deadline_links(html, url):
                    if link not in queue and len(queue) < _MAX_URLS_PER_ROW:
                        queue.append(link)

            stats["pages_checked"] += 1
            text = _page_text(html)
            deadline_at, label = pick_notification_deadline(text)
            if deadline_at is None:
                continue
            if not deadline_is_upcoming(deadline_at):
                if found_deadline is None:
                    found_deadline = deadline_at
                    found_label = label
                    found_summary = format_deadline_summary(text)
                continue

            found_deadline = deadline_at
            found_label = label
            found_summary = format_deadline_summary(text)
            break

        # Only guess /apply /dates paths if seeds + discovered links found nothing usable.
        if (
            (found_deadline is None or not deadline_is_upcoming(found_deadline))
            and seeds
            and not used_suffixes
        ):
            used_suffixes = True
            for suffix_url in _suffix_urls(seeds[0]):
                if suffix_url in html_by_url or suffix_url in queue:
                    continue
                if len(queue) >= _MAX_URLS_PER_ROW + 3:
                    break
                html = _fetch_html(client, suffix_url)
                if html is None:
                    continue
                fetched_ok = True
                stats["fetched"] += 1
                stats["pages_checked"] += 1
                text = _page_text(html)
                deadline_at, label = pick_notification_deadline(text)
                if deadline_at is None:
                    continue
                if not deadline_is_upcoming(deadline_at):
                    continue
                found_deadline = deadline_at
                found_label = label
                found_summary = format_deadline_summary(text)
                break

        if not fetched_ok:
            stats["fetch_failed"] += 1
            logger.info("[%s/%s] Fetch failed for all URLs — %s", index, len(rows), row.title)
            continue

        if found_deadline is None:
            stats["no_deadline_found"] += 1
            logger.info("[%s/%s] No parseable deadline — %s", index, len(rows), row.title)
            continue

        if not deadline_is_upcoming(found_deadline):
            stats["past_deadline"] += 1
            logger.info(
                "[%s/%s] Only past deadline found (%s) — %s",
                index,
                len(rows),
                found_deadline.date(),
                row.title,
            )
            continue

        row.deadline_at = found_deadline
        if found_summary:
            row.description = _append_deadline_summary(row.description, found_summary)
        row.last_scraped_at = datetime.now(UTC)
        db.commit()
        stats["enriched"] += 1
        logger.info(
            "[%s/%s] ENRICHED %s | %s=%s",
            index,
            len(rows),
            row.title,
            found_label or "deadline",
            found_deadline.date(),
        )

    return stats
