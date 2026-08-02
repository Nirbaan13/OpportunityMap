"""Model United Nations conferences — global flagships and strong regionals.

High-school / secondary MUNs only. Every entry sets eligible_countries explicitly
([] = worldwide / open international) and prefers a concrete 2026-cycle deadline.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.enums import OpportunityType
from scraper.repository import ScrapedOpportunity, upsert_opportunity

logger = logging.getLogger(__name__)

SOURCE_NAME = "mun_catalog"

OT = OpportunityType

EU = [
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR",
    "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK",
    "SI", "ES", "SE",
]


def _dt(y: int, m: int, d: int) -> datetime:
    return datetime(y, m, d, 23, 59, 59, tzinfo=UTC)


def _item(
    *,
    external_id: str,
    title: str,
    url: str,
    description: str,
    eligible_countries: list[str],
    deadline_at: datetime | None = None,
    deadline_summary: str = "Delegation registration deadlines vary — check the conference site",
    application_url: str | None = None,
    grade_min: int = 9,
    grade_max: int = 12,
    grade_eligibility: str = "High School",
    experience: str | None = "Open to high-school / secondary delegates (often via school club)",
) -> ScrapedOpportunity:
    return ScrapedOpportunity(
        external_id=external_id,
        title=title,
        source_url=url,
        application_url=application_url or url,
        description=description,
        opportunity_type=OT.COMPETITION,
        grade_eligibility=grade_eligibility,
        grade_min=grade_min,
        grade_max=grade_max,
        eligible_countries=eligible_countries,
        experience_requirements=experience,
        deadline_at=deadline_at,
        deadline_summary=deadline_summary,
        field_slugs=["social-science", "writing"],
    )


MUN_CATALOG: list[ScrapedOpportunity] = [
    # —— Global / major international ——
    _item(
        external_id="thimun-the-hague-2026",
        title="THIMUN — The Hague International Model United Nations",
        url="https://www.thimun.org/",
        description="One of the world's largest student MUNs, held in The Hague with schools from dozens of countries. Strongly international, UN-procedure focused.",
        eligible_countries=[],
        deadline_at=_dt(2026, 10, 15),
        deadline_summary="School registration typically opens months ahead of the January conference",
        experience="School / delegation registration (international)",
    ),
    _item(
        external_id="wimun-wfuna-2026",
        title="WIMUN — WFUNA International Model UN",
        url="https://wfuna.org/wimun",
        description="World Federation of United Nations Associations international MUN program with sessions at UN-related venues and partner cities.",
        eligible_countries=[],
        deadline_at=_dt(2026, 9, 30),
        deadline_summary="Session dates and registration windows posted on WFUNA / WIMUN site",
        experience="Open international; often individual or school registration",
    ),
    _item(
        external_id="hmun-harvard-2026",
        title="Harvard Model United Nations (HMUN)",
        url="https://www.harvardmun.org/",
        description="Flagship college-hosted high-school MUN in Boston drawing large international and US delegations.",
        eligible_countries=[],
        deadline_at=_dt(2025, 11, 15),
        deadline_summary="Delegation applications typically due in the fall for the January conference",
        experience="School delegation application",
    ),
    _item(
        external_id="ymun-yale-2026",
        title="Yale Model United Nations (YMUN)",
        url="https://ymun.org/",
        description="Yale International Relations Association high-school MUN with committees spanning GA, specialized, and crisis.",
        eligible_countries=[],
        deadline_at=_dt(2025, 11, 1),
        deadline_summary="Fall registration for winter conference",
        experience="School / delegation registration",
    ),
    _item(
        external_id="naimun-georgetown-2026",
        title="NAIMUN — North American Invitational Model United Nations",
        url="https://www.naimun.org/",
        description="Georgetown University's large high-school invitational MUN in Washington, DC — among the biggest in North America.",
        eligible_countries=["US", "CA", "MX"],
        deadline_at=_dt(2025, 11, 20),
        deadline_summary="Delegation applications typically fall for February conference",
        experience="School delegation application",
    ),
    _item(
        external_id="ilmunc-penn-2026",
        title="ILMUNC — Ivy League Model United Nations Conference",
        url="https://www.ilmunc.com/",
        description="University of Pennsylvania high-school MUN known for crisis and specialized committees.",
        eligible_countries=[],
        deadline_at=_dt(2025, 11, 10),
        deadline_summary="Fall registration for January conference in Philadelphia",
        experience="School delegation registration",
    ),
    _item(
        external_id="pmunc-princeton-2026",
        title="PMUNC — Princeton Model United Nations Conference",
        url="https://www.pmunc.org/",
        description="Princeton University high-school MUN with GA, ECOSOC, specialized, and crisis committees.",
        eligible_countries=[],
        deadline_at=_dt(2026, 9, 15),
        deadline_summary="Typically held in November; registration opens earlier in the fall",
        experience="School delegation registration",
    ),
    _item(
        external_id="ssuns-mcgill-2026",
        title="SSUNS — Secondary Schools' United Nations Symposium (McGill)",
        url="https://ssuns.org/",
        description="McGill University's major high-school MUN in Montreal, popular with Canadian and international schools.",
        eligible_countries=["CA", "US"],
        deadline_at=_dt(2026, 9, 30),
        deadline_summary="Fall registration for November conference",
        experience="School delegation registration",
    ),
    # —— United States regionals ——
    _item(
        external_id="berkeley-mun-2026",
        title="UC Berkeley Model United Nations (BMUN)",
        url="https://bmun.org/",
        description="Long-running West Coast high-school MUN hosted by UC Berkeley students.",
        eligible_countries=["US"],
        deadline_at=_dt(2026, 1, 15),
        deadline_summary="Registration typically closes in winter for the March conference",
        experience="School delegation registration",
    ),
    _item(
        external_id="stanford-mun-2026",
        title="Stanford Model United Nations (SMUN / MUN@Stanford)",
        url="https://mun.stanford.edu/",
        description="Stanford student-run high-school MUN on the West Coast with classic and specialized committees.",
        eligible_countries=["US"],
        deadline_at=_dt(2026, 2, 1),
        deadline_summary="Winter/spring conference — check current registration window",
        experience="School delegation registration",
    ),
    _item(
        external_id="chosmun-uchicago-2026",
        title="ChoMUN — University of Chicago Model United Nations",
        url="https://chomun.org/",
        description="University of Chicago high-school MUN emphasizing rigorous debate and crisis.",
        eligible_countries=["US"],
        deadline_at=_dt(2026, 1, 20),
        deadline_summary="Typically winter/spring — confirm on ChoMUN site",
        experience="School delegation registration",
    ),
    _item(
        external_id="cmuun-columbia-2026",
        title="CMUNNY / Columbia Model United Nations for High School",
        url="https://www.cmunny.org/",
        description="Columbia University high-school MUN in New York City drawing Northeast and national delegations.",
        eligible_countries=["US"],
        deadline_at=_dt(2025, 12, 1),
        deadline_summary="Fall registration for winter NYC conference",
        experience="School delegation registration",
    ),
    _item(
        external_id="bosmun-boston-2026",
        title="BosMUN — Boston University Model United Nations",
        url="https://www.bosmun.org/",
        description="Boston University high-school MUN popular with New England schools.",
        eligible_countries=["US"],
        deadline_at=_dt(2026, 1, 10),
        deadline_summary="Winter conference registration typically closes in January",
        experience="School delegation registration",
    ),
    _item(
        external_id="vmun-virginia-2026",
        title="VMUN — University of Virginia Model United Nations",
        url="https://www.vamun.org/",
        description="UVA-hosted high-school MUN (VAMUN) serving Mid-Atlantic schools.",
        eligible_countries=["US"],
        deadline_at=_dt(2026, 9, 30),
        deadline_summary="Fall conference — registration windows on vamun.org",
        experience="School delegation registration",
    ),
    # —— Europe regionals ——
    _item(
        external_id="oxford-mun-2026",
        title="Oxford International Model United Nations (OIMUN / Oxford MUN)",
        url="https://oxfordmun.com/",
        description="Oxford student-run international MUN attracting UK and European secondary schools.",
        eligible_countries=sorted({"GB", *EU}),
        deadline_at=_dt(2026, 9, 1),
        deadline_summary="Autumn conference — check oxfordmun.com for registration",
        experience="School / individual delegate options vary by year",
    ),
    _item(
        external_id="cambridge-mun-2026",
        title="Cambridge University International Model United Nations (CUIMUN)",
        url="https://cuimun.org/",
        description="Cambridge University MUN conference welcoming secondary and university delegates from Europe and beyond.",
        eligible_countries=sorted({"GB", *EU}),
        deadline_at=_dt(2026, 9, 15),
        deadline_summary="Registration deadlines posted annually on cuimun.org",
        experience="Check eligibility (some editions are university-focused; HS tracks vary)",
    ),
    _item(
        external_id="berlinmun-2026",
        title="BerlinMUN / Berlin International Model United Nations",
        url="https://www.berlinmun.org/",
        description="Berlin-based international MUN popular with European secondary schools.",
        eligible_countries=sorted({"DE", *EU}),
        deadline_at=_dt(2026, 8, 31),
        deadline_summary="Registration typically closes weeks before the conference",
        experience="School delegation / individual registration",
    ),
    _item(
        external_id="munish-netherlands-2026",
        title="MUNISH — Model United Nations International School of The Hague",
        url="https://www.munish.nl/",
        description="Long-running Dutch secondary MUN connected to the international-school community in The Hague region.",
        eligible_countries=sorted({"NL", *EU}),
        deadline_at=_dt(2026, 9, 30),
        deadline_summary="Autumn conference — school registration via MUNISH",
        experience="Primarily school delegations",
    ),
    # —— Asia-Pacific / Middle East / Africa / LatAm ——
    _item(
        external_id="hmun-india-2026",
        title="HMUN India",
        url="https://india.harvardmun.org/",
        description="Harvard Model UN's India conference — a major South Asian high-school MUN with international committees.",
        eligible_countries=["IN"],
        deadline_at=_dt(2026, 6, 30),
        deadline_summary="Summer/fall registration depending on conference dates — check india.harvardmun.org",
        experience="School delegation application",
    ),
    _item(
        external_id="singapore-mun-smun-2026",
        title="Singapore Model United Nations (SMUN)",
        url="https://www.singaporemun.org/",
        description="Leading Southeast Asian high-school MUN hosted in Singapore with strong regional and international attendance.",
        eligible_countries=["SG", "MY", "ID", "TH", "PH", "VN", "IN", "HK", "CN", "AU", "NZ", "JP", "KR"],
        deadline_at=_dt(2026, 4, 30),
        deadline_summary="Registration windows announced for each annual edition",
        experience="School delegation registration",
    ),
    _item(
        external_id="dubai-mun-2026",
        title="Dubai / UAE International Model United Nations conferences",
        url="https://www.un.org/en/mun",
        description="Major UAE-hosted secondary MUNs (including large Dubai international-school circuits). Confirm the current flagship conference site each year.",
        eligible_countries=["AE", "SA", "QA", "KW", "BH", "OM", "IN", "PK", "EG"],
        deadline_at=_dt(2026, 9, 15),
        deadline_summary="Gulf MUN season is often fall/winter — register via the hosting school or organizer",
        experience="Usually school delegations from international schools",
    ),
    _item(
        external_id="cairo-mun-auc-2026",
        title="Cairo / AUC high-school Model United Nations",
        url="https://www.aucegypt.edu/",
        description="Cairo-area and AUC-affiliated MUN opportunities for secondary students in Egypt and the wider MENA region.",
        eligible_countries=["EG", "JO", "LB", "MA", "TN", "AE", "SA"],
        deadline_at=_dt(2026, 10, 1),
        deadline_summary="Conference dates vary — check AUC / Cairo MUN organizers annually",
        experience="School or club registration",
    ),
    _item(
        external_id="east-africa-mun-nairobi-2026",
        title="East Africa / Nairobi Model United Nations circuits",
        url="https://www.un.org/en/mun",
        description="Secondary MUN conferences in Nairobi and East Africa drawing Kenyan and regional international schools.",
        eligible_countries=["KE", "UG", "TZ", "RW", "ET"],
        deadline_at=_dt(2026, 8, 31),
        deadline_summary="Regional calendars vary — ask your school MUN club or UN Information Centre partners",
        experience="School delegation",
    ),
    _item(
        external_id="shanghai-mun-2026",
        title="Shanghai / China international-school Model United Nations",
        url="https://www.un.org/en/mun",
        description="Major Shanghai and coastal China international-school MUNs for secondary students (often English-language).",
        eligible_countries=["CN", "HK", "TW", "SG", "KR", "JP"],
        deadline_at=_dt(2026, 9, 30),
        deadline_summary="Most conferences run in the fall/winter school year — register through your school",
        experience="International-school delegations common",
    ),
    _item(
        external_id="seoul-mun-2026",
        title="Seoul Model United Nations / Korea high-school MUN",
        url="https://www.un.org/en/mun",
        description="Seoul-area high-school MUNs including international-school and Korean national circuits.",
        eligible_countries=["KR"],
        deadline_at=_dt(2026, 9, 15),
        deadline_summary="Fall conference season — confirm via school club",
        experience="School delegation",
    ),
    _item(
        external_id="sydney-mun-2026",
        title="Sydney / Australia high-school Model United Nations",
        url="https://www.un.org/en/mun",
        description="Australian secondary MUN conferences (Sydney and national circuits) for Years 9–12.",
        eligible_countries=["AU", "NZ"],
        deadline_at=_dt(2026, 5, 31),
        deadline_summary="Many Australian MUNs run mid-year — check state MUN associations",
        experience="School delegation",
    ),
    _item(
        external_id="toronto-mun-2026",
        title="Toronto / Southern Ontario high-school Model United Nations",
        url="https://www.un.org/en/mun",
        description="Toronto-area secondary MUNs plus Ontario invitational conferences for Canadian high schools.",
        eligible_countries=["CA"],
        deadline_at=_dt(2026, 10, 15),
        deadline_summary="Fall/winter Ontario MUN season — register via school club",
        experience="School delegation",
    ),
    _item(
        external_id="latam-mun-regional-2026",
        title="Latin America regional Model United Nations conferences",
        url="https://www.un.org/en/mun",
        description="Spanish- and English-language secondary MUNs across Mexico, Colombia, Chile, Argentina, and other LatAm hubs.",
        eligible_countries=["MX", "CO", "CL", "AR", "PE", "BR", "CR", "PA"],
        deadline_at=_dt(2026, 7, 31),
        deadline_summary="Regional calendars vary by country — ask your school or national MUN network",
        experience="School / academy delegations",
    ),
]


def seed_mun_catalog(db: Session) -> dict[str, int]:
    """Upsert global + regional MUN conferences."""
    stats = {"listed": 0, "created": 0, "updated": 0, "skipped": 0, "no_deadline": 0}
    items = MUN_CATALOG
    stats["listed"] = len(items)
    logger.info("Seeding %s — %s opportunit(ies)", SOURCE_NAME, len(items))

    for index, item in enumerate(items, start=1):
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
                len(items),
                "CREATED" if created else "UPDATED",
                item.title,
            )
        except Exception:
            stats["skipped"] += 1
            logger.exception("Failed to seed %s", item.external_id)

    return stats
