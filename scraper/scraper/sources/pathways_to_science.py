"""Scraper for Pathways to Science (pathwaystoscience.org)."""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup, NavigableString, Tag
from sqlalchemy.orm import Session

from app.models.enums import OpportunityType
from scraper.curl_client import CurlClient
from scraper.parsers.dates import (
    deadline_is_upcoming,
    format_deadline_summary,
    parse_date,
    pick_notification_deadline,
)
from scraper.parsers.eligibility import is_high_school_program
from scraper.parsers.field_mapping import categories_to_field_slugs
from scraper.parsers.grades import parse_grade_eligibility
from scraper.repository import ScrapedOpportunity, upsert_opportunity

logger = logging.getLogger(__name__)

BASE_URL = "https://www.pathwaystoscience.org/"
SOURCE_NAME = "pathways_to_science"

HIGH_SCHOOL_SEARCH = (
    "programs.aspx?u=&r=&s=HighSchool&sa=either&p=either&o=either&c=either"
    "&f=&dd=&ft=&submit=y&adv=adv"
)

PREFIX_TO_TYPE: dict[str, OpportunityType] = {
    "SUM": OpportunityType.SUMMER_SCHOOL,
    "HSC": OpportunityType.RESEARCH_PROGRAM,
    "OPP": OpportunityType.SCHOLARSHIP,
    "FEL": OpportunityType.FELLOWSHIP,
    "GRD": OpportunityType.RESEARCH_PROGRAM,
    "PDC": OpportunityType.FELLOWSHIP,
    "UDG": OpportunityType.SCHOLARSHIP,
}


@dataclass
class ListingItem:
    external_id: str
    title: str
    url: str
    institution: str | None = None


def _external_id_from_url(url: str) -> str | None:
    qs = parse_qs(urlparse(url).query)
    sort_values = qs.get("sort")
    if not sort_values:
        return None
    return sort_values[0]


def _listing_url() -> str:
    return urljoin(BASE_URL, HIGH_SCHOOL_SEARCH)


def _text_until_next_label(node: Tag) -> str:
    parts: list[str] = []
    for sibling in node.next_siblings:
        if isinstance(sibling, Tag) and sibling.name == "b":
            break
        if isinstance(sibling, NavigableString):
            text = str(sibling).strip()
            if text:
                parts.append(text)
        elif isinstance(sibling, Tag):
            if sibling.name == "br":
                continue
            text = sibling.get_text(" ", strip=True)
            if text:
                parts.append(text)
    return re.sub(r"\s+", " ", " ".join(parts)).strip()


def _extract_labeled_value(soup: BeautifulSoup, label: str) -> str | None:
    target = label.rstrip(":").lower()
    for bold in soup.select("b"):
        bold_text = bold.get_text(" ", strip=True).rstrip(":").lower()
        if bold_text == target:
            value = _text_until_next_label(bold)
            return value or None
    return None


def _extract_disciplines(soup: BeautifulSoup) -> str:
    for bold in soup.select("b"):
        if "academic disciplines" in bold.get_text(" ", strip=True).lower():
            parent = bold.parent
            if parent is None:
                continue
            text = parent.get_text(" ", strip=True)
            _, _, rest = text.partition("Academic Disciplines:")
            return rest.strip()
    return ""


def _extract_application_url(soup: BeautifulSoup) -> str | None:
    for link in soup.select("a[href]"):
        text = link.get_text(" ", strip=True).lower()
        href = link.get("href", "")
        if not href or href.startswith("#"):
            continue
        if "learn more and apply" in text or "click here to learn more and apply" in text:
            return href
    for link in soup.select("a.btn-success[href], a.btn.btn-success[href]"):
        href = link.get("href", "")
        if href:
            return href
    return None


def _opportunity_type_for_external_id(external_id: str) -> OpportunityType:
    prefix = external_id.split("-", 1)[0].upper()
    return PREFIX_TO_TYPE.get(prefix, OpportunityType.RESEARCH_PROGRAM)


def parse_listing_page(html: str) -> list[ListingItem]:
    soup = BeautifulSoup(html, "lxml")
    items: list[ListingItem] = []
    seen: set[str] = set()

    for link in soup.select('a[href*="programhub.aspx"]'):
        href = link.get("href", "")
        title = link.get_text(strip=True)
        if not href or not title or title.lower().startswith("..."):
            continue
        url = urljoin(BASE_URL, href)
        external_id = _external_id_from_url(url)
        if external_id is None or external_id in seen:
            continue
        seen.add(external_id)
        institution = None
        container = link.find_parent("div", class_="progigert")
        if container is not None:
            prev = container.find_previous("div", class_="progigert")
            if prev is not None:
                institution = prev.get_text(" ", strip=True) or None
        items.append(
            ListingItem(
                external_id=external_id,
                title=title,
                url=url,
                institution=institution,
            )
        )
    return items


def parse_detail_page(html: str, listing: ListingItem) -> ScrapedOpportunity:
    soup = BeautifulSoup(html, "lxml")
    main = soup.select_one("div.col-sm-7") or soup

    title_el = main.select_one("h1")
    title = title_el.get_text(strip=True) if title_el else listing.title

    academic_level = _extract_labeled_value(main, "Academic Level") or "High School"
    description = _extract_labeled_value(main, "Description")
    deadline_text = _extract_labeled_value(main, "Application Deadline")
    disciplines = _extract_disciplines(main)
    content_text = main.get_text("\n", strip=True)

    grade_eligibility, grade_min, grade_max = parse_grade_eligibility(academic_level)

    field_slugs = categories_to_field_slugs(disciplines)
    if not field_slugs and disciplines:
        field_slugs = categories_to_field_slugs(disciplines.replace("\n", ","))

    deadline_at = parse_date(deadline_text, end_of_day=True) if deadline_text else None
    if deadline_at is None:
        deadline_at, _ = pick_notification_deadline(content_text)
    deadline_summary = format_deadline_summary(content_text)
    if deadline_text and deadline_at is not None:
        line = f"Application Deadline: {deadline_at.strftime('%B %d, %Y')}"
        deadline_summary = f"{line}\n{deadline_summary}".strip() if deadline_summary else line

    application_url = _extract_application_url(main) or listing.url
    if application_url and not application_url.startswith("http"):
        application_url = urljoin(BASE_URL, application_url)

    if listing.institution and description:
        description = f"{description}\n\nInstitution: {listing.institution}"

    return ScrapedOpportunity(
        external_id=listing.external_id,
        title=title,
        source_url=listing.url,
        application_url=application_url,
        description=description,
        opportunity_type=_opportunity_type_for_external_id(listing.external_id),
        grade_eligibility=grade_eligibility,
        grade_min=grade_min,
        grade_max=grade_max,
        eligible_countries=None,
        experience_requirements=academic_level,
        deadline_at=deadline_at,
        deadline_summary=deadline_summary,
        field_slugs=field_slugs,
    )


def scrape_pathways_to_science(
    db: Session,
    client: CurlClient,
    *,
    max_items: int = 20,
    delay_seconds: float = 1.0,
) -> dict[str, int]:
    """Scrape high-school STEM programs from pathwaystoscience.org."""
    stats = {
        "listed": 0,
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "skipped_no_deadline": 0,
        "skipped_past_deadline": 0,
        "skipped_not_high_school": 0,
    }

    listing_html = client.fetch_html(_listing_url())
    listings = parse_listing_page(listing_html)
    if max_items > 0:
        listings = listings[:max_items]

    stats["listed"] = len(listings)
    logger.info("Scraping %s — %s program(s) from high-school search", SOURCE_NAME, len(listings))

    if not listings:
        soup = BeautifulSoup(listing_html, "lxml")
        title = soup.title.get_text(strip=True) if soup.title else "(no title)"
        logger.error("Listing page returned 0 programs. Page title: %s", title)
        return stats

    for index, listing in enumerate(listings, start=1):
        try:
            detail_html = client.fetch_html(listing.url)
            scraped = parse_detail_page(detail_html, listing)
            if not is_high_school_program(
                scraped.experience_requirements,
                grade_min=scraped.grade_min,
                grade_max=scraped.grade_max,
            ):
                stats["skipped"] += 1
                stats["skipped_not_high_school"] += 1
                logger.info(
                    "[%s/%s] Skipping %s — not a high-school program (%s)",
                    index,
                    len(listings),
                    listing.title,
                    scraped.experience_requirements,
                )
                continue
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
        if delay_seconds > 0:
            time.sleep(delay_seconds)

    return stats
