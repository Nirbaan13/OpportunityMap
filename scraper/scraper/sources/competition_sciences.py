"""Scraper for Institute of Competition Sciences (competitionsciences.org)."""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from scraper.http_client import BrowserClient
from scraper.parsers.dates import deadline_is_upcoming, format_deadline_summary, pick_notification_deadline
from scraper.parsers.field_mapping import categories_to_field_slugs
from scraper.parsers.grades import parse_grade_eligibility
from scraper.repository import ScrapedOpportunity, upsert_opportunity
from app.models.enums import OpportunityType

logger = logging.getLogger(__name__)

BASE_URL = "https://www.competitionsciences.org"
SOURCE_NAME = "competition_sciences"
LISTING_URL = f"{BASE_URL}/competitions/?ages=high_school&type&category&keyword"

ICS_TYPE_TO_OPPORTUNITY: dict[str, OpportunityType] = {
    "exam": OpportunityType.OLYMPIAD,
    "submission": OpportunityType.COMPETITION,
    "tournament": OpportunityType.COMPETITION,
    "fair": OpportunityType.COMPETITION,
    "performance": OpportunityType.COMPETITION,
    "presentation": OpportunityType.COMPETITION,
}


@dataclass
class ListingItem:
    external_id: str
    title: str
    url: str
    ages_text: str
    categories_text: str


def _external_id_from_url(url: str) -> str | None:
    path = urlparse(url).path.strip("/")
    parts = path.split("/")
    if len(parts) >= 2 and parts[0] == "competitions" and parts[1] not in ("", "page"):
        return parts[1]
    return None


def _listing_url_for_page(page: int) -> str:
    if page <= 1:
        return LISTING_URL
    return f"{BASE_URL}/competitions/page/{page}/?ages=high_school&type&category&keyword"


def _parse_listing_card(card: BeautifulSoup) -> ListingItem | None:
    link = card.select_one('h3 a[href*="/competitions/"]') or card.select_one('a[href*="/competitions/"]')
    if link is None or not link.get("href"):
        return None
    url = urljoin(BASE_URL, link["href"])
    external_id = _external_id_from_url(url)
    if external_id is None:
        return None
    title = link.get_text(strip=True)
    ages_el = card.select_one("p.ages span") or card.select_one(".ages")
    categories_el = card.select_one("p.categories span") or card.select_one(".categories")
    ages_text = ages_el.get_text(strip=True) if ages_el else ""
    categories_text = categories_el.get_text(strip=True) if categories_el else ""
    return ListingItem(
        external_id=external_id,
        title=title,
        url=url,
        ages_text=ages_text,
        categories_text=categories_text,
    )


def _parse_listing_links_fallback(soup: BeautifulSoup) -> list[ListingItem]:
    """Fallback: collect competition links if card markup is missing."""
    items: list[ListingItem] = []
    seen: set[str] = set()
    root = soup.select_one("#ics-competitions-archive") or soup.select_one("main") or soup

    for link in root.select('a[href*="/competitions/"]'):
        href = link.get("href")
        if not href:
            continue
        url = urljoin(BASE_URL, href)
        external_id = _external_id_from_url(url)
        if external_id is None or external_id in seen:
            continue
        title = link.get_text(strip=True)
        if len(title) < 3:
            continue
        seen.add(external_id)
        items.append(
            ListingItem(
                external_id=external_id,
                title=title,
                url=url,
                ages_text="",
                categories_text="",
            )
        )
    return items


def parse_listing_page(html: str) -> list[ListingItem]:
    soup = BeautifulSoup(html, "lxml")
    items: list[ListingItem] = []
    seen: set[str] = set()

    selectors = (
        ".ics-comp-results-item",
        ".ics-featured-competition",
    )
    for selector in selectors:
        for card in soup.select(selector):
            parsed = _parse_listing_card(card)
            if parsed is None or parsed.external_id in seen:
                continue
            seen.add(parsed.external_id)
            items.append(parsed)

    if not items:
        items = _parse_listing_links_fallback(soup)

    return items


def _extract_meta_value(soup: BeautifulSoup, label: str) -> str | None:
    pattern = re.compile(rf"^{re.escape(label)}\s*:?\s*(.*)$", re.IGNORECASE)
    for node in soup.select("p, li, div, span, h2, h3, h4"):
        text = node.get_text(" ", strip=True)
        match = pattern.match(text)
        if match and match.group(1):
            return match.group(1).strip()
    return None


def _main_content_text(soup: BeautifulSoup) -> str:
    main = soup.select_one("main.site-main") or soup.select_one("main") or soup.body
    return main.get_text("\n", strip=True) if main else soup.get_text("\n", strip=True)


def parse_detail_page(
    html: str,
    listing: ListingItem,
) -> ScrapedOpportunity:
    soup = BeautifulSoup(html, "lxml")
    content_text = _main_content_text(soup)

    title_el = soup.select_one("h1") or soup.select_one("h2")
    title = title_el.get_text(strip=True) if title_el else listing.title

    ages_text = _extract_meta_value(soup, "Ages") or listing.ages_text
    categories_text = _extract_meta_value(soup, "Categories") or listing.categories_text
    ics_type = (_extract_meta_value(soup, "Type") or "").lower()
    eligibility = _extract_meta_value(soup, "Eligibility")
    scope = (_extract_meta_value(soup, "Scope") or "").lower()

    grade_eligibility, grade_min, grade_max = parse_grade_eligibility(ages_text)
    field_slugs = categories_to_field_slugs(categories_text)

    deadline_at, _deadline_label = pick_notification_deadline(content_text)
    deadline_summary = format_deadline_summary(content_text)

    # Description: first substantial paragraph on the detail page.
    description_parts: list[str] = []
    for paragraph in soup.select("main p"):
        text = paragraph.get_text(" ", strip=True)
        if len(text) > 80 and "login" not in text.lower():
            description_parts.append(text)
            break
    description = description_parts[0] if description_parts else None

    eligible_countries = None
    if "united states" in content_text.lower() or scope == "national":
        eligible_countries = ["US"]

    opportunity_type = ICS_TYPE_TO_OPPORTUNITY.get(ics_type, OpportunityType.COMPETITION)

    return ScrapedOpportunity(
        external_id=listing.external_id,
        title=title,
        source_url=listing.url,
        application_url=listing.url,
        description=description,
        opportunity_type=opportunity_type,
        grade_eligibility=grade_eligibility or ages_text or None,
        grade_min=grade_min,
        grade_max=grade_max,
        eligible_countries=eligible_countries,
        experience_requirements=eligibility,
        deadline_at=deadline_at,
        deadline_summary=deadline_summary,
        field_slugs=field_slugs,
    )


def _total_pages(html: str) -> int:
    soup = BeautifulSoup(html, "lxml")
    page_numbers = []
    for link in soup.select("a.page-numbers"):
        text = link.get_text(strip=True)
        if text.isdigit():
            page_numbers.append(int(text))
    return max(page_numbers) if page_numbers else 1


def scrape_competition_sciences(
    db: Session,
    client: BrowserClient,
    *,
    max_pages: int = 2,
    delay_seconds: float = 1.0,
) -> dict[str, int]:
    """
    Scrape high-school competitions from competitionsciences.org into the database.

    max_pages: number of listing pages (0 = all pages).
    """
    stats = {
        "listed": 0,
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "skipped_no_deadline": 0,
        "skipped_past_deadline": 0,
    }

    first_html = client.fetch_html(_listing_url_for_page(1))
    total_pages = _total_pages(first_html)
    pages_to_scrape = total_pages if max_pages == 0 else min(max_pages, total_pages)

    first_page_count = len(parse_listing_page(first_html))
    if first_page_count == 0:
        soup = BeautifulSoup(first_html, "lxml")
        title = soup.title.get_text(strip=True) if soup.title else "(no title)"
        logger.error(
            "Listing page returned 0 competitions. Page title: %s. "
            "The site may have blocked the scraper or changed its layout.",
            title,
        )
        try:
            from pathlib import Path

            debug_path = Path("debug_listing.html")
            debug_path.write_text(first_html, encoding="utf-8")
            logger.error("Saved page HTML to %s for inspection", debug_path.resolve())
        except OSError:
            logger.exception("Could not write debug_listing.html")

    logger.info(
        "Scraping %s — %s listing page(s) of %s",
        SOURCE_NAME,
        pages_to_scrape,
        total_pages,
    )

    listings: list[ListingItem] = []
    seen_ids: set[str] = set()
    for page in range(1, pages_to_scrape + 1):
        html = first_html if page == 1 else client.fetch_html(_listing_url_for_page(page))
        page_items = parse_listing_page(html)
        for item in page_items:
            if item.external_id not in seen_ids:
                seen_ids.add(item.external_id)
                listings.append(item)
        logger.info("Page %s: found %s competitions", page, len(page_items))
        time.sleep(delay_seconds)

    stats["listed"] = len(listings)

    for index, listing in enumerate(listings, start=1):
        try:
            detail_html = client.fetch_html(listing.url)
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
                scraped.deadline_at.date() if scraped.deadline_at else "none",
            )
        except Exception:
            stats["skipped"] += 1
            logger.exception("Failed to scrape %s", listing.url)
        time.sleep(delay_seconds)

    return stats
