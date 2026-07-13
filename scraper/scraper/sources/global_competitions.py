"""Curated global high-school science competitions and olympiads."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.enums import OpportunityType
from scraper.repository import ScrapedOpportunity, upsert_opportunity

logger = logging.getLogger(__name__)

SOURCE_NAME = "global_competitions"

# Well-known international olympiads and science fairs open to high-school students.
GLOBAL_COMPETITIONS: list[ScrapedOpportunity] = [
    ScrapedOpportunity(
        external_id="imo",
        title="International Mathematical Olympiad (IMO)",
        source_url="https://www.imo-official.org/",
        application_url="https://www.imo-official.org/country_info.aspx",
        description=(
            "The IMO is the premier global mathematics competition for pre-university students. "
            "Each country selects a national team (typically six students) through national olympiads."
        ),
        opportunity_type=OpportunityType.OLYMPIAD,
        grade_eligibility="High School",
        grade_min=9,
        grade_max=12,
        eligible_countries=None,
        experience_requirements="National team selection via country olympiad program",
        deadline_at=None,
        deadline_summary="Varies by country — contact your national math olympiad organization",
        field_slugs=["mathematics"],
    ),
    ScrapedOpportunity(
        external_id="ioi",
        title="International Olympiad in Informatics (IOI)",
        source_url="https://ioinformatics.org/",
        application_url="https://ioinformatics.org/page/countries/1",
        description=(
            "The IOI is the leading global programming competition for secondary-school students. "
            "Participants are selected through national computing olympiads."
        ),
        opportunity_type=OpportunityType.OLYMPIAD,
        grade_eligibility="High School",
        grade_min=9,
        grade_max=12,
        eligible_countries=None,
        experience_requirements="National team selection via country informatics olympiad",
        deadline_at=None,
        deadline_summary="Varies by country — contact your national informatics olympiad",
        field_slugs=["computer-science"],
    ),
    ScrapedOpportunity(
        external_id="ipho",
        title="International Physics Olympiad (IPhO)",
        source_url="https://www.ipho-new.org/",
        application_url="https://www.ipho-new.org/participating-countries.html",
        description=(
            "The IPhO brings together national teams of high-school students for theoretical "
            "and experimental physics competitions."
        ),
        opportunity_type=OpportunityType.OLYMPIAD,
        grade_eligibility="High School",
        grade_min=9,
        grade_max=12,
        eligible_countries=None,
        experience_requirements="National team selection via country physics olympiad",
        deadline_at=None,
        deadline_summary="Varies by country — contact your national physics olympiad",
        field_slugs=["physics"],
    ),
    ScrapedOpportunity(
        external_id="icho",
        title="International Chemistry Olympiad (IChO)",
        source_url="https://www.icho-official.org/",
        application_url="https://www.icho-official.org/participating-countries/",
        description=(
            "The IChO is a global competition for the world's most talented chemistry students "
            "at the secondary-school level."
        ),
        opportunity_type=OpportunityType.OLYMPIAD,
        grade_eligibility="High School",
        grade_min=9,
        grade_max=12,
        eligible_countries=None,
        experience_requirements="National team selection via country chemistry olympiad",
        deadline_at=None,
        deadline_summary="Varies by country — contact your national chemistry olympiad",
        field_slugs=["chemistry"],
    ),
    ScrapedOpportunity(
        external_id="ibo",
        title="International Biology Olympiad (IBO)",
        source_url="https://www.ibo-info.org/",
        application_url="https://www.ibo-info.org/en/info/participating-countries.html",
        description=(
            "The IBO challenges the world's best biology students with theoretical and practical exams."
        ),
        opportunity_type=OpportunityType.OLYMPIAD,
        grade_eligibility="High School",
        grade_min=9,
        grade_max=12,
        eligible_countries=None,
        experience_requirements="National team selection via country biology olympiad",
        deadline_at=None,
        deadline_summary="Varies by country — contact your national biology olympiad",
        field_slugs=["biology"],
    ),
    ScrapedOpportunity(
        external_id="isef",
        title="Regeneron International Science and Engineering Fair (ISEF)",
        source_url="https://www.societyforscience.org/isef/",
        application_url="https://www.societyforscience.org/isef/rules-and-guidelines/",
        description=(
            "ISEF is the world's largest international pre-college STEM competition. "
            "Students qualify through affiliated regional and national fairs worldwide."
        ),
        opportunity_type=OpportunityType.COMPETITION,
        grade_eligibility="High School",
        grade_min=9,
        grade_max=12,
        eligible_countries=None,
        experience_requirements="Qualify through an affiliated regional or national science fair",
        deadline_at=datetime(2026, 5, 10, 23, 59, 59, tzinfo=UTC),
        deadline_summary="Finals week typically May; regional fair deadlines vary by country",
        field_slugs=["research", "engineering"],
    ),
    ScrapedOpportunity(
        external_id="ioaa",
        title="International Olympiad on Astronomy and Astrophysics (IOAA)",
        source_url="https://www.ioaa.org/",
        application_url="https://www.ioaa.org/member-countries",
        description=(
            "The IOAA is a global olympiad combining theoretical, observational, and data-analysis "
            "tasks in astronomy and astrophysics."
        ),
        opportunity_type=OpportunityType.OLYMPIAD,
        grade_eligibility="High School",
        grade_min=9,
        grade_max=12,
        eligible_countries=None,
        experience_requirements="National team selection via country astronomy olympiad",
        deadline_at=None,
        deadline_summary="Varies by country — contact your national astronomy olympiad",
        field_slugs=["physics"],
    ),
    ScrapedOpportunity(
        external_id="ieeo",
        title="International Earth Science Olympiad (IESO)",
        source_url="https://www.ieso-info.org/",
        application_url="https://www.ieso-info.org/participating-countries/",
        description=(
            "The IESO is an annual competition for secondary-school students in earth sciences, "
            "including geology, oceanography, and environmental science."
        ),
        opportunity_type=OpportunityType.OLYMPIAD,
        grade_eligibility="High School",
        grade_min=9,
        grade_max=12,
        eligible_countries=None,
        experience_requirements="National team selection via country earth science olympiad",
        deadline_at=None,
        deadline_summary="Varies by country — contact your national earth science olympiad",
        field_slugs=["physics", "biology"],
    ),
    ScrapedOpportunity(
        external_id="ijso",
        title="International Junior Science Olympiad (IJSO)",
        source_url="https://www.ijso.info/",
        application_url="https://www.ijso.info/participating-countries/",
        description=(
            "The IJSO is a multidisciplinary science olympiad for students under 16, "
            "covering physics, chemistry, and biology."
        ),
        opportunity_type=OpportunityType.OLYMPIAD,
        grade_eligibility="Middle School, High School",
        grade_min=6,
        grade_max=10,
        eligible_countries=None,
        experience_requirements="Under 16 years old; national team selection required",
        deadline_at=None,
        deadline_summary="Varies by country — contact your national junior science olympiad",
        field_slugs=["physics", "chemistry", "biology"],
    ),
    ScrapedOpportunity(
        external_id="ioi-geography",
        title="International Geography Olympiad (iGeo)",
        source_url="https://www.geoolympiad.org/",
        application_url="https://www.geoolympiad.org/Participating_Countries",
        description=(
            "iGeo is the international competition for the best geography students of secondary "
            "schools from around the world."
        ),
        opportunity_type=OpportunityType.OLYMPIAD,
        grade_eligibility="High School",
        grade_min=9,
        grade_max=12,
        eligible_countries=None,
        experience_requirements="National team selection via country geography olympiad",
        deadline_at=None,
        deadline_summary="Varies by country — contact your national geography olympiad",
        field_slugs=["social-science"],
    ),
]


def seed_global_competitions(db: Session) -> dict[str, int]:
    """Upsert curated global high-school competitions (no HTTP scraping)."""
    stats = {"listed": 0, "created": 0, "updated": 0, "skipped": 0, "no_deadline": 0}

    stats["listed"] = len(GLOBAL_COMPETITIONS)
    logger.info("Seeding %s — %s global competition(s)", SOURCE_NAME, len(GLOBAL_COMPETITIONS))

    for index, item in enumerate(GLOBAL_COMPETITIONS, start=1):
        try:
            if item.deadline_at is None:
                stats["no_deadline"] += 1
            _, created = upsert_opportunity(db, item, source_name=SOURCE_NAME)
            if created:
                stats["created"] += 1
            else:
                stats["updated"] += 1
            logger.info(
                "[%s/%s] %s %s",
                index,
                len(GLOBAL_COMPETITIONS),
                "CREATED" if created else "UPDATED",
                item.title,
            )
        except Exception:
            stats["skipped"] += 1
            logger.exception("Failed to seed %s", item.external_id)

    return stats
