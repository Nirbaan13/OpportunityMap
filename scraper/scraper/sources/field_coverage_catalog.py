"""Multi-field catalog of olympiads, research, and competitions.

Upserted on every scraper run so listings stay fresh (update check via last_scraped_at).
Covers every OpportunityMap interest field.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.enums import OpportunityType
from scraper.repository import ScrapedOpportunity, upsert_opportunity

logger = logging.getLogger(__name__)

SOURCE_NAME = "field_coverage_catalog"

OT = OpportunityType


def _item(
    *,
    external_id: str,
    title: str,
    url: str,
    description: str,
    opportunity_type: OpportunityType,
    field_slugs: list[str],
    application_url: str | None = None,
    grade_min: int = 9,
    grade_max: int = 12,
    grade_eligibility: str = "High School",
    experience: str | None = None,
    deadline_summary: str = "Deadlines vary by year and country — check the official site",
    deadline_at: datetime | None = None,
) -> ScrapedOpportunity:
    return ScrapedOpportunity(
        external_id=external_id,
        title=title,
        source_url=url,
        application_url=application_url or url,
        description=description,
        opportunity_type=opportunity_type,
        grade_eligibility=grade_eligibility,
        grade_min=grade_min,
        grade_max=grade_max,
        eligible_countries=None,
        experience_requirements=experience,
        deadline_at=deadline_at,
        deadline_summary=deadline_summary,
        field_slugs=field_slugs,
    )


# Broad automated catalog across AI, sciences, social science, writing, business, etc.
FIELD_COVERAGE: list[ScrapedOpportunity] = [
    # —— Mathematics ——
    _item(
        external_id="amc-12",
        title="AMC 12 (American Mathematics Competitions)",
        url="https://maa.org/student-programs/amc/",
        description="Leading US high-school math contest; gateway to AIME and USAMO.",
        opportunity_type=OT.COMPETITION,
        field_slugs=["mathematics"],
        experience="Usually grades 9–12; school registration",
    ),
    _item(
        external_id="aime",
        title="American Invitational Mathematics Examination (AIME)",
        url="https://maa.org/math-competitions/american-invitational-mathematics-examination-aime",
        description="Invitation-only contest after strong AMC scores; path to USAMO.",
        opportunity_type=OT.COMPETITION,
        field_slugs=["mathematics"],
        experience="Qualify via AMC 10/12",
    ),
    _item(
        external_id="usamo",
        title="USA Mathematical Olympiad (USAMO)",
        url="https://maa.org/math-competitions/usa-mathematical-olympiad-usamo",
        description="Top US proof-based olympiad; selects IMO team candidates.",
        opportunity_type=OT.OLYMPIAD,
        field_slugs=["mathematics"],
        experience="Qualify via AMC + AIME",
    ),
    _item(
        external_id="promys",
        title="PROMYS (Program in Mathematics for Young Scientists)",
        url="https://promys.org/",
        description="Six-week number theory program at Boston University for high-school students.",
        opportunity_type=OT.SUMMER_SCHOOL,
        field_slugs=["mathematics", "research"],
        deadline_summary="Applications typically due in March–April",
    ),
    _item(
        external_id="ross-mathematics",
        title="Ross Mathematics Program",
        url="https://rossprogram.org/",
        description="Intensive summer math program focused on number theory and proof.",
        opportunity_type=OT.SUMMER_SCHOOL,
        field_slugs=["mathematics"],
    ),
    _item(
        external_id="hmmtt",
        title="Harvard-MIT Mathematics Tournament (HMMT)",
        url="https://www.hmmt.org/",
        description="Major team and individual high-school math tournament hosted by Harvard/MIT students.",
        opportunity_type=OT.COMPETITION,
        field_slugs=["mathematics"],
    ),
    # —— Computer science / AI ——
    _item(
        external_id="usaco",
        title="USA Computing Olympiad (USACO)",
        url="https://usaco.org/",
        description="Online programming olympiad with Bronze–Platinum divisions; path toward IOI.",
        opportunity_type=OT.OLYMPIAD,
        field_slugs=["computer-science", "ai"],
        grade_min=6,
    ),
    _item(
        external_id="codeforces-rounds",
        title="Codeforces Contests (High School Track)",
        url="https://codeforces.com/contests",
        description="Frequent rated programming contests used by olympiad students worldwide.",
        opportunity_type=OT.COMPETITION,
        field_slugs=["computer-science"],
        grade_min=6,
        deadline_summary="Ongoing contest calendar — check Codeforces regularly",
    ),
    _item(
        external_id="google-code-jam-kickstart",
        title="Google Kick Start / Coding Competitions archive",
        url="https://codingcompetitions.withgoogle.com/",
        description="Google’s coding competition resources and practice archives for algorithmic problem solving.",
        opportunity_type=OT.COMPETITION,
        field_slugs=["computer-science", "ai"],
    ),
    _item(
        external_id="mit-primes",
        title="MIT PRIMES",
        url="https://math.mit.edu/research/highschool/primes/",
        description="Year-long research mentorship in math, computer science, and computational biology.",
        opportunity_type=OT.RESEARCH_PROGRAM,
        field_slugs=["mathematics", "computer-science", "ai", "research", "biology"],
        deadline_summary="Applications typically open in fall for the following year",
    ),
    _item(
        external_id="rsi-css",
        title="Research Science Institute (RSI)",
        url="https://www.cee.org/programs/research-science-institute",
        description="Premier free summer research program at MIT for top high-school STEM students.",
        opportunity_type=OT.RESEARCH_PROGRAM,
        field_slugs=["research", "physics", "chemistry", "biology", "mathematics", "computer-science", "ai"],
        deadline_summary="US applications typically due mid-January",
    ),
    _item(
        external_id="ai-olympiad-ioai",
        title="International Olympiad in Artificial Intelligence (IOAI)",
        url="https://ioai-official.org/",
        description="International olympiad focused on AI concepts, algorithms, and applications for secondary students.",
        opportunity_type=OT.OLYMPIAD,
        field_slugs=["ai", "computer-science"],
    ),
    # —— Physics / astronomy ——
    _item(
        external_id="uspho",
        title="USA Physics Olympiad (USAPhO)",
        url="https://www.aapt.org/physicsteam/2026/",
        description="US physics olympiad pathway toward the International Physics Olympiad.",
        opportunity_type=OT.OLYMPIAD,
        field_slugs=["physics"],
    ),
    _item(
        external_id="fma",
        title="F=ma Contest (AAPT)",
        url="https://www.aapt.org/physicsteam/",
        description="Introductory US physics olympiad exam used to qualify for USAPhO.",
        opportunity_type=OT.COMPETITION,
        field_slugs=["physics"],
    ),
    _item(
        external_id="ssp-astrophysics",
        title="Summer Science Program (SSP) — Astrophysics",
        url="https://www.summerscience.org/",
        description="Hands-on residential research program; astrophysics track includes asteroid orbit determination.",
        opportunity_type=OT.SUMMER_SCHOOL,
        field_slugs=["physics", "research", "mathematics"],
    ),
    _item(
        external_id="iau-astronomy",
        title="International Astronomy Olympiad / national pathways",
        url="https://www.iau.org/",
        description="Astronomy olympiad opportunities via national astronomy education programs.",
        opportunity_type=OT.OLYMPIAD,
        field_slugs=["physics"],
    ),
    # —— Chemistry ——
    _item(
        external_id="usnco",
        title="U.S. National Chemistry Olympiad (USNCO)",
        url="https://www.acs.org/education/olympiad.html",
        description="ACS chemistry olympiad; pathway to the International Chemistry Olympiad.",
        opportunity_type=OT.OLYMPIAD,
        field_slugs=["chemistry"],
    ),
    _item(
        external_id="ssp-biochem",
        title="Summer Science Program (SSP) — Biochemistry",
        url="https://www.summerscience.org/",
        description="Residential SSP track focused on biochemistry and genomics research skills.",
        opportunity_type=OT.SUMMER_SCHOOL,
        field_slugs=["chemistry", "biology", "research"],
    ),
    _item(
        external_id="acs-project-seed",
        title="ACS Project SEED",
        url="https://www.acs.org/education/students/highschool/seed.html",
        description="Summer chemistry research internships for economically disadvantaged high-school students.",
        opportunity_type=OT.RESEARCH_PROGRAM,
        field_slugs=["chemistry", "research"],
    ),
    # —— Biology / medicine ——
    _item(
        external_id="usabo",
        title="USA Biology Olympiad (USABO)",
        url="https://www.usabo-trc.org/",
        description="US biology olympiad pathway toward the International Biology Olympiad.",
        opportunity_type=OT.OLYMPIAD,
        field_slugs=["biology"],
    ),
    _item(
        external_id="regeneron-sts",
        title="Regeneron Science Talent Search",
        url="https://www.societyforscience.org/regeneron-sts/",
        description="Prestigious US research competition for high-school seniors with original science projects.",
        opportunity_type=OT.COMPETITION,
        field_slugs=["research", "biology", "chemistry", "physics", "engineering", "ai"],
        grade_min=12,
        grade_max=12,
        deadline_summary="Applications typically due in November for seniors",
    ),
    _item(
        external_id="simr-stanford",
        title="Stanford Institutes of Medicine Summer Research (SIMR)",
        url="https://med.stanford.edu/simr.html",
        description="Eight-week biomedical research internship for high-school students at Stanford Medicine.",
        opportunity_type=OT.RESEARCH_PROGRAM,
        field_slugs=["biology", "research", "chemistry"],
    ),
    _item(
        external_id="rockefeller-ssrp",
        title="Rockefeller University Summer Science Research Program",
        url="https://www.rockefeller.edu/education-and-training/high-school/",
        description="Summer biomedical research experience for high-school students in New York.",
        opportunity_type=OT.RESEARCH_PROGRAM,
        field_slugs=["biology", "research"],
    ),
    _item(
        external_id="nyu-arise",
        title="NYU Tandon ARISE",
        url="https://engineering.nyu.edu/research-innovation/student-research/arise",
        description="Applied research innovations program in science and engineering for NYC-area high schoolers.",
        opportunity_type=OT.RESEARCH_PROGRAM,
        field_slugs=["engineering", "research", "computer-science", "biology"],
    ),
    # —— Engineering / robotics ——
    _item(
        external_id="first-robotics",
        title="FIRST Robotics Competition",
        url="https://www.firstinspires.org/robotics/frc",
        description="Team robotics competition combining engineering design, coding, and outreach.",
        opportunity_type=OT.COMPETITION,
        field_slugs=["engineering", "computer-science", "ai"],
        grade_min=9,
        deadline_summary="Season registration typically opens in fall",
    ),
    _item(
        external_id="first-tech-challenge",
        title="FIRST Tech Challenge",
        url="https://www.firstinspires.org/robotics/ftc",
        description="Modular robotics competition for grades 7–12.",
        opportunity_type=OT.COMPETITION,
        field_slugs=["engineering", "computer-science"],
        grade_min=7,
    ),
    _item(
        external_id="science-olympiad",
        title="Science Olympiad",
        url="https://www.soinc.org/",
        description="Team STEM competition with events across biology, chemistry, physics, and engineering.",
        opportunity_type=OT.COMPETITION,
        field_slugs=["biology", "chemistry", "physics", "engineering", "research"],
        grade_min=6,
    ),
    _item(
        external_id="cyberpatriot",
        title="CyberPatriot",
        url="https://www.uscyberpatriot.org/",
        description="National youth cyber defense competition teaching cybersecurity skills.",
        opportunity_type=OT.COMPETITION,
        field_slugs=["computer-science", "engineering"],
        grade_min=6,
    ),
    # —— Economics / business ——
    _item(
        external_id="ieo",
        title="International Economics Olympiad (IEO)",
        url="https://ecolymp.org/",
        description="International olympiad in economics, finance, and business for secondary students.",
        opportunity_type=OT.OLYMPIAD,
        field_slugs=["economics", "business"],
    ),
    _item(
        external_id="nec",
        title="National Economics Challenge (CEE)",
        url="https://www.councilforeconed.org/national-economics-challenge/",
        description="US team economics competition for high-school students.",
        opportunity_type=OT.COMPETITION,
        field_slugs=["economics"],
    ),
    _item(
        external_id="deca",
        title="DECA Competitive Events",
        url="https://www.deca.org/compete",
        description="Business, marketing, finance, and hospitality competitions for high-school DECA members.",
        opportunity_type=OT.COMPETITION,
        field_slugs=["business", "economics"],
    ),
    _item(
        external_id="fbla",
        title="FBLA Competitive Events",
        url="https://www.fbla.org/compete/",
        description="Future Business Leaders of America contests across business and technology topics.",
        opportunity_type=OT.COMPETITION,
        field_slugs=["business", "computer-science"],
    ),
    _item(
        external_id="wharton-ess",
        title="Wharton Global Youth — Essentials of Entrepreneurship / Leadership",
        url="https://globalyouth.wharton.upenn.edu/",
        description="Wharton programs introducing high-school students to business, finance, and entrepreneurship.",
        opportunity_type=OT.SUMMER_SCHOOL,
        field_slugs=["business", "economics"],
    ),
    # —— Social science / humanities ——
    _item(
        external_id="ihbb",
        title="International History Bee & Bowl",
        url="https://www.historybowl.com/",
        description="International history quiz competitions for middle and high school students.",
        opportunity_type=OT.COMPETITION,
        field_slugs=["social-science"],
        grade_min=6,
    ),
    _item(
        external_id="nhsb",
        title="National History Bee & Bowl (US)",
        url="https://www.historybowl.com/",
        description="US history academic competitions leading to national championships.",
        opportunity_type=OT.COMPETITION,
        field_slugs=["social-science"],
    ),
    _item(
        external_id="ipo-philosophy",
        title="International Philosophy Olympiad (IPO)",
        url="https://www.philosophy-olympiad.org/",
        description="Essay-based international olympiad in philosophy for secondary-school students.",
        opportunity_type=OT.OLYMPIAD,
        field_slugs=["social-science", "writing"],
    ),
    _item(
        external_id="model-un",
        title="Model United Nations (global conferences)",
        url="https://www.un.org/en/mun",
        description="Debate and diplomacy simulations; many regional and international high-school conferences.",
        opportunity_type=OT.COMPETITION,
        field_slugs=["social-science", "writing"],
        deadline_summary="Conference deadlines vary — browse regional MUN calendars",
    ),
    _item(
        external_id="nsda-debate",
        title="NSDA Speech & Debate",
        url="https://www.speechanddebate.org/",
        description="National Speech & Debate Association tournaments in policy, LD, PF, and speech events.",
        opportunity_type=OT.COMPETITION,
        field_slugs=["social-science", "writing"],
    ),
    _item(
        external_id="psychology-olympiad",
        title="International Psychology Olympiad / national psychology contests",
        url="https://www.psychologyolympiad.org/",
        description="Psychology competitions introducing research methods and core psychology topics.",
        opportunity_type=OT.OLYMPIAD,
        field_slugs=["social-science", "biology", "research"],
    ),
    # —— Writing / literature ——
    _item(
        external_id="scholastic-art-writing",
        title="Scholastic Art & Writing Awards",
        url="https://www.artandwriting.org/",
        description="Major US creative writing and arts awards for teens in grades 7–12.",
        opportunity_type=OT.COMPETITION,
        field_slugs=["writing"],
        grade_min=7,
        deadline_summary="Regional deadlines typically fall/winter",
    ),
    _item(
        external_id="bennington-young-writers",
        title="Bennington Young Writers Awards",
        url="https://www.bennington.edu/center-for-the-advancement-of-public-action/young-writers-awards",
        description="Writing awards for poetry, fiction, and nonfiction by high-school students.",
        opportunity_type=OT.COMPETITION,
        field_slugs=["writing"],
    ),
    _item(
        external_id="princeton-poetry",
        title="Princeton University Poetry Contest for High School Students",
        url="https://arts.princeton.edu/",
        description="Competitive poetry contest hosted by Princeton for secondary-school writers.",
        opportunity_type=OT.COMPETITION,
        field_slugs=["writing"],
    ),
    _item(
        external_id="profile-in-courage",
        title="John F. Kennedy Profile in Courage Essay Contest",
        url="https://www.jfklibrary.org/learn/education/profile-in-courage-essay-contest",
        description="National essay contest on political courage for US high-school students.",
        opportunity_type=OT.COMPETITION,
        field_slugs=["writing", "social-science"],
    ),
    # —— Research / summer STEM (multi-field) ——
    _item(
        external_id="garcia-stony-brook",
        title="Garcia Summer Program (Stony Brook)",
        url="https://www.stonybrook.edu/commcms/garcia/",
        description="Materials science and polymer research summer program for high-school students.",
        opportunity_type=OT.RESEARCH_PROGRAM,
        field_slugs=["chemistry", "engineering", "research", "physics"],
    ),
    _item(
        external_id="clark-scholars",
        title="Clark Scholars Program (Texas Tech)",
        url="https://www.depts.ttu.edu/honors/academicsandenrichment/affiliatedandhighschool/clarks/",
        description="Intensive summer research across STEM disciplines with faculty mentors.",
        opportunity_type=OT.RESEARCH_PROGRAM,
        field_slugs=["research", "engineering", "biology", "chemistry", "physics", "computer-science"],
    ),
    _item(
        external_id="iowa-sstp",
        title="University of Iowa Secondary Student Training Program (SSTP)",
        url="https://belinblank.education.uiowa.edu/students/sstp/",
        description="Residential research program pairing high-school students with UI faculty labs.",
        opportunity_type=OT.RESEARCH_PROGRAM,
        field_slugs=["research", "biology", "chemistry", "physics", "engineering", "ai"],
    ),
    _item(
        external_id="mites",
        title="MIT MITES / MOSTEC",
        url="https://oeop.mit.edu/programs/mites",
        description="MIT outreach STEM programs for underrepresented high-school students.",
        opportunity_type=OT.SUMMER_SCHOOL,
        field_slugs=["engineering", "computer-science", "physics", "mathematics", "ai"],
    ),
    _item(
        external_id="yale-yygs",
        title="Yale Young Global Scholars (YYGS)",
        url="https://globalscholars.yale.edu/",
        description="Academic summer sessions spanning STEM, politics, literature, and social sciences.",
        opportunity_type=OT.SUMMER_SCHOOL,
        field_slugs=["social-science", "writing", "research", "economics", "biology"],
    ),
    _item(
        external_id="telluride-tass",
        title="Telluride Association Summer Seminar (TASS)",
        url="https://www.tellurideassociation.org/",
        description="Free humanities and social science summer seminars for high-school students.",
        opportunity_type=OT.SUMMER_SCHOOL,
        field_slugs=["social-science", "writing"],
    ),
    _item(
        external_id="bank-of-america-slc",
        title="Bank of America Student Leaders",
        url="https://about.bankofamerica.com/en/making-an-impact/student-leaders",
        description="Paid summer leadership internship with community nonprofits plus a Washington leadership summit.",
        opportunity_type=OT.FELLOWSHIP,
        field_slugs=["social-science", "business"],
    ),
    # —— Scholarships / fellowships with academic focus ——
    _item(
        external_id="questbridge",
        title="QuestBridge College Prep Scholars / National College Match",
        url="https://www.questbridge.org/",
        description="College access programs for high-achieving students from low-income backgrounds.",
        opportunity_type=OT.SCHOLARSHIP,
        field_slugs=["research", "social-science", "writing"],
        grade_min=11,
    ),
    _item(
        external_id="coca-cola-scholars",
        title="Coca-Cola Scholars Program",
        url="https://www.coca-colascholarsfoundation.org/",
        description="Merit scholarship for US high-school seniors with leadership and service.",
        opportunity_type=OT.SCHOLARSHIP,
        field_slugs=["social-science", "business"],
        grade_min=12,
        grade_max=12,
    ),
    _item(
        external_id="davidson-fellows",
        title="Davidson Fellows Scholarship",
        url="https://www.davidsongifted.org/fellows-scholarship/",
        description="Scholarships for students under 18 with significant projects in STEM, literature, music, or philosophy.",
        opportunity_type=OT.SCHOLARSHIP,
        field_slugs=["research", "mathematics", "physics", "chemistry", "biology", "ai", "writing", "social-science"],
        grade_min=6,
        grade_max=12,
    ),
    # —— Earth / environmental / geography ——
    _item(
        external_id="envirothon",
        title="NCF-Envirothon",
        url="https://envirothon.org/",
        description="Team environmental science competition covering soils, forestry, aquatics, wildlife, and current issues.",
        opportunity_type=OT.COMPETITION,
        field_slugs=["biology", "social-science", "research"],
    ),
    _item(
        external_id="nasa-internships-hs",
        title="NASA Internships & Fellowships (High School)",
        url="https://intern.nasa.gov/",
        description="NASA internship portal including high-school eligible STEM opportunities when posted.",
        opportunity_type=OT.RESEARCH_PROGRAM,
        field_slugs=["physics", "engineering", "computer-science", "ai", "research"],
        deadline_summary="Sessions posted year-round — check NASA intern portal",
    ),
    _item(
        external_id="noaa-hollings-prep",
        title="NOAA education & high-school STEM opportunities",
        url="https://www.noaa.gov/education",
        description="NOAA education programs, contests, and pathways into earth and ocean sciences.",
        opportunity_type=OT.RESEARCH_PROGRAM,
        field_slugs=["biology", "physics", "research"],
    ),
    # —— India / international open contests often relevant worldwide ——
    _item(
        external_id="inmo",
        title="Indian National Mathematical Olympiad (INMO) pathway",
        url="https://olympiads.hbcse.tifr.res.in/mathematical-olympiad/",
        description="India’s math olympiad pathway (IOQM → RMO → INMO) toward IMO selection.",
        opportunity_type=OT.OLYMPIAD,
        field_slugs=["mathematics"],
    ),
    _item(
        external_id="incho",
        title="Indian National Chemistry Olympiad pathway (HBCSE)",
        url="https://olympiads.hbcse.tifr.res.in/chemistry-olympiad/",
        description="India chemistry olympiad selection pathway toward IChO.",
        opportunity_type=OT.OLYMPIAD,
        field_slugs=["chemistry"],
    ),
    _item(
        external_id="inpho",
        title="Indian National Physics Olympiad pathway (HBCSE)",
        url="https://olympiads.hbcse.tifr.res.in/physics-olympiad/",
        description="India physics olympiad selection pathway toward IPhO.",
        opportunity_type=OT.OLYMPIAD,
        field_slugs=["physics"],
    ),
    _item(
        external_id="inbo",
        title="Indian National Biology Olympiad pathway (HBCSE)",
        url="https://olympiads.hbcse.tifr.res.in/biology-olympiad/",
        description="India biology olympiad selection pathway toward IBO.",
        opportunity_type=OT.OLYMPIAD,
        field_slugs=["biology"],
    ),
    _item(
        external_id="inao",
        title="Indian National Astronomy Olympiad pathway (HBCSE)",
        url="https://olympiads.hbcse.tifr.res.in/astronomy-olympiad/",
        description="India astronomy olympiad selection pathway toward IOAA.",
        opportunity_type=OT.OLYMPIAD,
        field_slugs=["physics"],
    ),
    _item(
        external_id="zco-inoi",
        title="Indian Computing Olympiad (ZCO / INOI)",
        url="https://www.iarcs.org.in/inoi",
        description="India informatics olympiad pathway toward IOI.",
        opportunity_type=OT.OLYMPIAD,
        field_slugs=["computer-science", "ai"],
    ),
]


def seed_field_coverage_catalog(db: Session) -> dict[str, int]:
    """Upsert multi-field catalog entries (automated update check each run)."""
    stats = {"listed": 0, "created": 0, "updated": 0, "skipped": 0, "no_deadline": 0}

    items = FIELD_COVERAGE
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
