"""Fetch official program pages and fill in missing deadline_at values.

Catalog seeds intentionally leave most rows undated (dates shift yearly). This
pass visits each undated listing's source_url, runs the shared date parser, and
writes a concrete upcoming deadline when one is clearly labeled on the page.
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime

from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Opportunity
from scraper.curl_client import CurlClient
from scraper.parsers.dates import (
    deadline_is_upcoming,
    format_deadline_summary,
    pick_notification_deadline,
)

logger = logging.getLogger(__name__)

# Static catalogs whose dates we try to recover from official pages.
CATALOG_SOURCES = (
    "field_coverage_catalog",
    "expanded_catalog",
    "global_competitions",
)

_SCRIPT_STYLE = re.compile(r"<(script|style|noscript)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)


def _page_text(html: str) -> str:
    cleaned = _SCRIPT_STYLE.sub(" ", html)
    soup = BeautifulSoup(cleaned, "lxml")
    for tag in soup(["script", "style", "noscript", "svg", "nav", "footer", "header"]):
        tag.decompose()
    return soup.get_text("\n", strip=True)


def _candidate_urls(row: Opportunity) -> list[str]:
    urls: list[str] = []
    for value in (row.source_url, row.application_url):
        if not value:
            continue
        if not value.startswith("http"):
            continue
        if value not in urls:
            urls.append(value)
    return urls


def _append_deadline_summary(description: str | None, summary: str) -> str:
    block = f"Deadlines:\n{summary}"
    text = (description or "").strip()
    if "Deadlines:" in text:
        # Replace the existing Deadlines block so we don't stack duplicates.
        head, _, _rest = text.partition("Deadlines:")
        return f"{head.strip()}\n\n{block}".strip()
    return f"{text}\n\n{block}".strip() if text else block


def enrich_catalog_deadlines(
    db: Session,
    client: CurlClient,
    *,
    max_items: int = 0,
    delay_seconds: float = 1.0,
) -> dict[str, int]:
    """Best-effort deadline enrichment for undated catalog opportunities.

    max_items: 0 = all undated catalog rows; otherwise cap the batch size.
    """
    stats = {
        "candidates": 0,
        "fetched": 0,
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
        "Enriching deadlines for %s undated catalog opportunit(ies)",
        len(rows),
    )

    # CurlClient already sleeps after each fetch; keep a local reference for logs.
    _ = delay_seconds

    for index, row in enumerate(rows, start=1):
        urls = _candidate_urls(row)
        if not urls:
            stats["skipped"] += 1
            continue

        found_deadline = None
        found_label = None
        found_summary = None
        fetched_ok = False

        for url in urls:
            try:
                html = client.fetch_html(url)
                fetched_ok = True
                stats["fetched"] += 1
            except Exception as exc:
                logger.info(
                    "[%s/%s] Fetch failed for %s (%s): %s",
                    index,
                    len(rows),
                    row.title,
                    url,
                    exc,
                )
                continue

            text = _page_text(html)
            deadline_at, label = pick_notification_deadline(text)
            summary = format_deadline_summary(text)
            if deadline_at is None:
                continue
            found_deadline = deadline_at
            found_label = label
            found_summary = summary
            break

        if not fetched_ok:
            stats["fetch_failed"] += 1
            continue

        if found_deadline is None:
            stats["no_deadline_found"] += 1
            logger.info(
                "[%s/%s] No parseable deadline on page — %s",
                index,
                len(rows),
                row.title,
            )
            continue

        if not deadline_is_upcoming(found_deadline):
            stats["past_deadline"] += 1
            logger.info(
                "[%s/%s] Past deadline on page (%s) — %s",
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
