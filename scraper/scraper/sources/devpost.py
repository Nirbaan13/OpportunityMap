"""Scraper for Devpost hackathons (devpost.com)."""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.models.enums import OpportunityType
from scraper.curl_client import CurlClient
from scraper.parsers.dates import deadline_is_upcoming, parse_date
from scraper.parsers.eligibility import devpost_blocks_high_schoolers
from scraper.parsers.field_mapping import categories_to_field_slugs
from scraper.repository import ScrapedOpportunity, upsert_opportunity

logger = logging.getLogger(__name__)

BASE_URL = "https://devpost.com/"
API_URL = "https://devpost.com/api/hackathons"
SOURCE_NAME = "devpost"

REQUIRED_THEME = "beginner friendly"
REQUIRED_LOCATION = "online"

THEME_TO_FIELDS: dict[str, list[str]] = {
    "machine learning/ai": ["ai", "computer-science"],
    "web": ["computer-science"],
    "mobile": ["computer-science"],
    "cybersecurity": ["computer-science"],
    "gaming": ["computer-science"],
    "blockchain": ["computer-science"],
    "health": ["biology", "research"],
    "education": ["social-science"],
    "design": ["engineering"],
}


@dataclass
class ListingItem:
    external_id: str
    title: str
    url: str
    submission_period_dates: str | None
    themes: list[str]
    location: str | None
    organization_name: str | None


def _listing_params(*, page: int) -> dict[str, str]:
    return {
        "challenge_type[]": "online",
        "themes[]": "Beginner Friendly",
        "status[]": "open",
        "page": str(page),
    }


def _themes_to_field_slugs(theme_names: list[str]) -> list[str]:
    slugs: list[str] = []
    for name in theme_names:
        mapped = THEME_TO_FIELDS.get(name.lower())
        if mapped:
            for slug in mapped:
                if slug not in slugs:
                    slugs.append(slug)
            continue
        for slug in categories_to_field_slugs(name):
            if slug not in slugs:
                slugs.append(slug)
    if not slugs:
        slugs.append("computer-science")
    return slugs


def _parse_submission_period_end(text: str | None) -> str | None:
    if not text:
        return None
    cleaned = re.sub(r"\s+", " ", text).strip()
    if " - " in cleaned:
        return cleaned.split(" - ", 1)[1].strip()
    return cleaned


def _matches_required_filters(item: dict) -> bool:
    location = (item.get("displayed_location") or {}).get("location", "")
    if location.lower() != REQUIRED_LOCATION:
        return False
    theme_names = [theme.get("name", "") for theme in item.get("themes") or []]
    return any(name.lower() == REQUIRED_THEME for name in theme_names)


def parse_api_listing(payload: dict) -> list[ListingItem]:
    items: list[ListingItem] = []
    for row in payload.get("hackathons") or []:
        if not _matches_required_filters(row):
            continue
        external_id = str(row.get("id") or "").strip()
        title = (row.get("title") or "").strip()
        url = (row.get("url") or "").strip()
        if not external_id or not title or not url:
            continue
        theme_names = [theme.get("name", "") for theme in row.get("themes") or [] if theme.get("name")]
        items.append(
            ListingItem(
                external_id=external_id,
                title=title,
                url=url,
                submission_period_dates=row.get("submission_period_dates"),
                themes=theme_names,
                location=(row.get("displayed_location") or {}).get("location"),
                organization_name=row.get("organization_name"),
            )
        )
    return items


def _extract_eligibility_items(soup: BeautifulSoup) -> list[str]:
    return [
        li.get_text(" ", strip=True)
        for li in soup.select("#eligibility-list li")
        if li.get_text(strip=True)
    ]


def _extract_description(soup: BeautifulSoup) -> str | None:
    for selector in ("#challenge-description", ".challenge-description", "meta[name='description']"):
        if selector.startswith("meta"):
            meta = soup.select_one(selector)
            if meta and meta.get("content"):
                return meta["content"].strip()
            continue
        node = soup.select_one(selector)
        if node is not None:
            text = node.get_text("\n", strip=True)
            if len(text) > 40:
                return text
    return None


def _extract_deadline_iso(soup: BeautifulSoup) -> str | None:
    node = soup.select_one("[data-iso-date]")
    if node is not None:
        value = node.get("data-iso-date")
        if value:
            return value
    for node in soup.select("[data-dates-text]"):
        text = node.get_text(" ", strip=True)
        if "deadline" in text.lower():
            match = re.search(
                r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}",
                text,
            )
            if match:
                return match.group(0)
    return None


def parse_detail_page(html: str, listing: ListingItem) -> ScrapedOpportunity:
    soup = BeautifulSoup(html, "lxml")
    title_el = soup.select_one("h1") or soup.select_one("meta[property='og:title']")
    if title_el is not None and title_el.name == "meta":
        title = title_el.get("content", listing.title).strip()
    else:
        title = title_el.get_text(strip=True) if title_el else listing.title
    if not title:
        title = listing.title

    eligibility_items = _extract_eligibility_items(soup)
    description = _extract_description(soup)
    if listing.organization_name and description:
        description = f"{description}\n\nHost: {listing.organization_name}"

    deadline_text = _extract_deadline_iso(soup) or _parse_submission_period_end(
        listing.submission_period_dates
    )
    deadline_at = parse_date(deadline_text, end_of_day=True) if deadline_text else None

    theme_text = ", ".join(listing.themes)
    if description:
        description = f"{description}\n\nTags: {theme_text}\nFormat: Online"

    experience_requirements = "; ".join(eligibility_items) if eligibility_items else "Beginner Friendly; Online"

    return ScrapedOpportunity(
        external_id=listing.external_id,
        title=title,
        source_url=listing.url,
        application_url=listing.url,
        description=description,
        opportunity_type=OpportunityType.HACKATHON,
        grade_eligibility="High School",
        grade_min=9,
        grade_max=12,
        eligible_countries=None,
        experience_requirements=experience_requirements,
        deadline_at=deadline_at,
        deadline_summary=(
            f"Submission period: {listing.submission_period_dates}"
            if listing.submission_period_dates
            else None
        ),
        field_slugs=_themes_to_field_slugs(listing.themes),
    )


def scrape_devpost(
    db: Session,
    client: CurlClient,
    *,
    max_items: int = 20,
    max_pages: int = 3,
    delay_seconds: float = 1.0,
) -> dict[str, int]:
    """Scrape online, beginner-friendly open hackathons from Devpost."""
    stats = {
        "listed": 0,
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "skipped_no_deadline": 0,
        "skipped_past_deadline": 0,
        "skipped_not_eligible": 0,
    }

    listings: list[ListingItem] = []
    seen_ids: set[str] = set()
    for page in range(1, max_pages + 1):
        response = client.fetch_json(API_URL, params=_listing_params(page=page))
        page_items = parse_api_listing(response)
        if not page_items:
            break
        for item in page_items:
            if item.external_id not in seen_ids:
                seen_ids.add(item.external_id)
                listings.append(item)
        if delay_seconds > 0:
            time.sleep(delay_seconds)

    if max_items > 0:
        listings = listings[:max_items]

    stats["listed"] = len(listings)
    logger.info(
        "Scraping %s — %s hackathon(s) (online + beginner friendly + open)",
        SOURCE_NAME,
        len(listings),
    )

    for index, listing in enumerate(listings, start=1):
        try:
            detail_html = client.fetch_html(listing.url)
            soup = BeautifulSoup(detail_html, "lxml")
            eligibility_items = _extract_eligibility_items(soup)
            if devpost_blocks_high_schoolers(eligibility_items):
                stats["skipped"] += 1
                stats["skipped_not_eligible"] += 1
                logger.info(
                    "[%s/%s] Skipping %s — adults-only eligibility",
                    index,
                    len(listings),
                    listing.title,
                )
                continue

            scraped = parse_detail_page(detail_html, listing)
            if scraped.deadline_at is None:
                stats["skipped"] += 1
                stats["skipped_no_deadline"] += 1
                logger.info(
                    "[%s/%s] Skipping %s — no parseable deadline",
                    index,
                    len(listings),
                    listing.title,
                )
                continue
            if not deadline_is_upcoming(scraped.deadline_at):
                stats["skipped"] += 1
                stats["skipped_past_deadline"] += 1
                logger.info(
                    "[%s/%s] Skipping %s — deadline passed (%s)",
                    index,
                    len(listings),
                    listing.title,
                    scraped.deadline_at.date(),
                )
                continue

            _, created = upsert_opportunity(db, scraped, source_name=SOURCE_NAME)
            if created:
                stats["created"] += 1
            else:
                stats["updated"] += 1
            logger.info(
                "[%s/%s] %s %s | deadline=%s",
                index,
                len(listings),
                "CREATED" if created else "UPDATED",
                scraped.title,
                scraped.deadline_at.date(),
            )
        except Exception:
            stats["skipped"] += 1
            logger.exception("Failed to scrape %s", listing.url)
        if delay_seconds > 0:
            time.sleep(delay_seconds)

    return stats
