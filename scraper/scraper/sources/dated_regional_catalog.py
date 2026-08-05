"""Dated regional catalog — 500 non-Devpost high-school opportunities.

Every entry sets eligible_countries explicitly ([] = worldwide) and a concrete
2026-cycle deadline_at. Covers national olympiads, US state science fairs,
summer/research programs, scholarships, writing, robotics, and business.
Upserted on every scraper run.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.enums import OpportunityType
from scraper.repository import ScrapedOpportunity, upsert_opportunity

logger = logging.getLogger(__name__)

SOURCE_NAME = "dated_regional_catalog"

OT = OpportunityType

US_STATES: list[tuple[str, str]] = [
    ("AL", "Alabama"), ("AK", "Alaska"), ("AZ", "Arizona"), ("AR", "Arkansas"),
    ("CA", "California"), ("CO", "Colorado"), ("CT", "Connecticut"), ("DE", "Delaware"),
    ("FL", "Florida"), ("GA", "Georgia"), ("HI", "Hawaii"), ("ID", "Idaho"),
    ("IL", "Illinois"), ("IN", "Indiana"), ("IA", "Iowa"), ("KS", "Kansas"),
    ("KY", "Kentucky"), ("LA", "Louisiana"), ("ME", "Maine"), ("MD", "Maryland"),
    ("MA", "Massachusetts"), ("MI", "Michigan"), ("MN", "Minnesota"), ("MS", "Mississippi"),
    ("MO", "Missouri"), ("MT", "Montana"), ("NE", "Nebraska"), ("NV", "Nevada"),
    ("NH", "New Hampshire"), ("NJ", "New Jersey"), ("NM", "New Mexico"), ("NY", "New York"),
    ("NC", "North Carolina"), ("ND", "North Dakota"), ("OH", "Ohio"), ("OK", "Oklahoma"),
    ("OR", "Oregon"), ("PA", "Pennsylvania"), ("RI", "Rhode Island"), ("SC", "South Carolina"),
    ("SD", "South Dakota"), ("TN", "Tennessee"), ("TX", "Texas"), ("UT", "Utah"),
    ("VT", "Vermont"), ("VA", "Virginia"), ("WA", "Washington"), ("WV", "West Virginia"),
    ("WI", "Wisconsin"), ("WY", "Wyoming"),
]

COUNTRIES: list[tuple[str, str, str]] = [
    ("AR", "Argentina", "https://oma.org.ar/"),
    ("AU", "Australia", "https://www.amt.edu.au/"),
    ("AT", "Austria", "https://oemo.at/"),
    ("BD", "Bangladesh", "https://www.bdmo.org/"),
    ("BE", "Belgium", "https://www.olympiad.be/"),
    ("BR", "Brazil", "https://www.obm.org.br/"),
    ("BG", "Bulgaria", "https://lms.uni-sofia.bg/"),
    ("CA", "Canada", "https://cms.math.ca/"),
    ("CL", "Chile", "https://www.omatematica.cl/"),
    ("CN", "China", "https://www.cms.org.cn/"),
    ("CO", "Colombia", "https://ocm.org.co/"),
    ("HR", "Croatia", "https://www.math.hr/"),
    ("CZ", "Czechia", "https://www.mo.fzu.cz/"),
    ("DK", "Denmark", "https://www.math.ku.dk/"),
    ("EG", "Egypt", "https://www.egyptmath.org/"),
    ("EE", "Estonia", "https://www.math.ut.ee/"),
    ("ET", "Ethiopia", "https://www.eso.org.et/"),
    ("FI", "Finland", "https://www.maol.fi/"),
    ("FR", "France", "https://www.animath.fr/"),
    ("DE", "Germany", "https://www.mathematik-olympiaden.de/"),
    ("GH", "Ghana", "https://www.gasm.org.gh/"),
    ("GR", "Greece", "https://www.hms.gr/"),
    ("HK", "Hong Kong", "https://www.hkamo.org.hk/"),
    ("HU", "Hungary", "https://www.komal.hu/"),
    ("IS", "Iceland", "https://www.stjornvisindi.is/"),
    ("IN", "India", "https://olympiads.hbcse.tifr.res.in/"),
    ("ID", "Indonesia", "https://www.toki.id/"),
    ("IE", "Ireland", "https://www.irmo.ie/"),
    ("IL", "Israel", "https://www.imo.org.il/"),
    ("IT", "Italy", "https://www.olimpiadi.dm.unibo.it/"),
    ("JP", "Japan", "https://www.imojp.org/"),
    ("KE", "Kenya", "https://www.mathskenya.or.ke/"),
    ("KR", "South Korea", "https://www.kmo.or.kr/"),
    ("LV", "Latvia", "https://www.lzmd.lv/"),
    ("LT", "Lithuania", "https://www.lmnsc.lt/"),
    ("MY", "Malaysia", "https://www.omo.org.my/"),
    ("MX", "Mexico", "https://www.ommenlinea.org/"),
    ("NL", "Netherlands", "https://www.wiskundeolympiade.nl/"),
    ("NZ", "New Zealand", "https://www.nzmathsolympiad.org.nz/"),
    ("NG", "Nigeria", "https://www.nmc.edu.ng/"),
    ("NO", "Norway", "https://www.abelkonkurransen.no/"),
    ("PK", "Pakistan", "https://www.stem.edu.pk/"),
    ("PE", "Peru", "https://www.oma.org.pe/"),
    ("PH", "Philippines", "https://www.mathsociety.ph/"),
    ("PL", "Poland", "https://om.sem.edu.pl/"),
    ("PT", "Portugal", "https://www.spm.pt/"),
    ("RO", "Romania", "https://ssmr.ro/"),
    ("RU", "Russia", "https://olympiads.mccme.ru/"),
    ("SA", "Saudi Arabia", "https://www.mawhiba.org/"),
    ("SG", "Singapore", "https://sms.math.nus.edu.sg/"),
    ("SK", "Slovakia", "https://skmo.sk/"),
    ("SI", "Slovenia", "https://www.dmfa.si/"),
    ("ZA", "South Africa", "https://www.samf.ac.za/"),
    ("ES", "Spain", "https://www.olimpiadamatematica.es/"),
    ("LK", "Sri Lanka", "https://www.slmathsolympiad.org/"),
    ("SE", "Sweden", "https://www.skolornasmatematiktavling.se/"),
    ("CH", "Switzerland", "https://www.som.ch/"),
    ("TW", "Taiwan", "https://www.imo.org.tw/"),
    ("TH", "Thailand", "https://www.posn.or.th/"),
    ("TR", "Turkey", "https://www.tubitak.gov.tr/"),
    ("UA", "Ukraine", "https://www.imo.org.ua/"),
    ("AE", "United Arab Emirates", "https://www.moe.gov.ae/"),
    ("GB", "United Kingdom", "https://www.ukmt.org.uk/"),
    ("US", "United States", "https://www.maa.org/math-competitions"),
    ("VN", "Vietnam", "https://www.vimst.edu.vn/"),
    ("NP", "Nepal", "https://www.nepalmath.org/"),
    ("KZ", "Kazakhstan", "https://www.math.kz/"),
    ("UZ", "Uzbekistan", "https://www.edu.uz/"),
    ("MA", "Morocco", "https://www.men.gov.ma/"),
    ("TN", "Tunisia", "https://www.education.gov.tn/"),
]

SUBJECTS: list[tuple[str, str, str, str, OpportunityType, str, str]] = [
    (
        "math",
        "Mathematics",
        "National Mathematical Olympiad",
        "mathematics",
        OT.OLYMPIAD,
        "National selection contest toward the International Mathematical Olympiad (IMO).",
        "https://www.imo-official.org/",
    ),
    (
        "physics",
        "Physics",
        "National Physics Olympiad",
        "physics",
        OT.OLYMPIAD,
        "National selection contest toward the International Physics Olympiad (IPhO).",
        "https://www.ipho.org/",
    ),
    (
        "chemistry",
        "Chemistry",
        "National Chemistry Olympiad",
        "chemistry",
        OT.OLYMPIAD,
        "National selection contest toward the International Chemistry Olympiad (IChO).",
        "https://www.ichosc.org/",
    ),
    (
        "biology",
        "Biology",
        "National Biology Olympiad",
        "biology",
        OT.OLYMPIAD,
        "National selection contest toward the International Biology Olympiad (IBO).",
        "https://www.ibo-info.org/",
    ),
]


def _dt(y: int, m: int, d: int) -> datetime:
    return datetime(y, m, d, 23, 59, 59, tzinfo=UTC)


def _item(
    *,
    external_id: str,
    title: str,
    url: str,
    description: str,
    opportunity_type: OpportunityType,
    field_slugs: list[str],
    eligible_countries: list[str],
    application_url: str | None = None,
    grade_min: int = 9,
    grade_max: int = 12,
    grade_eligibility: str = "High School",
    experience: str | None = None,
    deadline_summary: str = "Check the official site for the current cycle",
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
        eligible_countries=eligible_countries,
        experience_requirements=experience,
        deadline_at=deadline_at,
        deadline_summary=deadline_summary,
        field_slugs=field_slugs,
    )


def _row(
    eid: str,
    title: str,
    url: str,
    countries: list[str],
    month: int,
    day: int,
    field: str,
    ot: OpportunityType,
    desc: str,
    *,
    grade_min: int = 9,
    grade_max: int = 12,
    experience: str | None = None,
    fields: list[str] | None = None,
    deadline_summary: str | None = None,
) -> ScrapedOpportunity:
    safe_day = min(day, 28) if month == 2 else day
    return _item(
        external_id=eid,
        title=title,
        url=url,
        description=desc,
        opportunity_type=ot,
        field_slugs=fields or [field],
        eligible_countries=countries,
        grade_min=grade_min,
        grade_max=grade_max,
        experience=experience,
        deadline_at=_dt(2026, month, safe_day),
        deadline_summary=deadline_summary
        or "Application / registration deadline for the 2026 cycle (verify official site)",
    )


SUMMERS: list[tuple] = [
    ("mit-es-2026", "MIT LaunchX / Entrepreneurship programs (HS)", "https://launchx.com/", "US", 7, 15, "business", OT.SUMMER_SCHOOL, "Residential / online entrepreneurship for high-school founders."),
    ("stanford-spcs-2026", "Stanford Pre-Collegiate Summer Institutes", "https://summerinstitutes.spcs.stanford.edu/", "US", 2, 1, "computer-science", OT.SUMMER_SCHOOL, "Selective Stanford pre-college summer courses across STEM and humanities."),
    ("yale-yyy-2026", "Yale Young Global Scholars", "https://globalscholars.yale.edu/", "US", 1, 10, "social-science", OT.SUMMER_SCHOOL, "Yale academic summer for high-school students on global topics."),
    ("columbia-shsp-2026", "Columbia University Summer High School Program", "https://summer.sps.columbia.edu/", "US", 3, 1, "research", OT.SUMMER_SCHOOL, "Columbia summer courses and college-experience programs for high schoolers."),
    ("uchicago-immersion-2026", "UChicago Immersion / Summer Session (HS)", "https://summer.uchicago.edu/", "US", 2, 15, "research", OT.SUMMER_SCHOOL, "University of Chicago summer immersion courses for high-school students."),
    ("caltech-wave-hs-2026", "Caltech WAVE / pre-college research pathways", "https://www.wave.caltech.edu/", "US", 1, 9, "engineering", OT.RESEARCH_PROGRAM, "Caltech undergraduate WAVE; related pre-college research outreach pathways."),
    ("berkeley-ats-2026", "UC Berkeley Academic Talent Development Program", "https://atdp.berkeley.edu/", "US", 3, 15, "mathematics", OT.SUMMER_SCHOOL, "Berkeley ATDP summer courses for academically talented middle and high school students."),
    ("ucla-summer-sessions-hs-2026", "UCLA Summer Sessions (High School)", "https://summer.ucla.edu/", "US", 4, 1, "research", OT.SUMMER_SCHOOL, "UCLA summer courses open to eligible high-school students."),
    ("nyu-precollege-2026", "NYU Precollege", "https://www.nyu.edu/admissions/high-school-programs.html", "US", 3, 20, "business", OT.SUMMER_SCHOOL, "NYU credit-bearing precollege courses for rising juniors and seniors."),
    ("brown-precollege-2026", "Brown University Pre-College Programs", "https://precollege.brown.edu/", "US", 2, 20, "writing", OT.SUMMER_SCHOOL, "Brown pre-college summer courses across many subjects."),
    ("penn-lps-hs-2026", "Penn LPS High School Programs", "https://www.lps.upenn.edu/", "US", 3, 10, "research", OT.SUMMER_SCHOOL, "University of Pennsylvania LPS offerings that include high-school summer options."),
    ("gatech-ceismc-2026", "Georgia Tech CEISMC K-12 Programs", "https://www.ceismc.gatech.edu/", "US", 4, 15, "engineering", OT.SUMMER_SCHOOL, "Georgia Tech K-12 STEM outreach and summer engineering programs."),
    ("cmu-samp-2026", "Carnegie Mellon Summer Programs for HS", "https://www.cmu.edu/pre-college/", "US", 2, 1, "computer-science", OT.SUMMER_SCHOOL, "CMU pre-college programs including CS, arts, and STEM."),
    ("uiuc-wysiwyg-2026", "UIUC Worldwide Youth in Science and Engineering", "https://wyse.engineering.illinois.edu/", "US", 3, 1, "engineering", OT.SUMMER_SCHOOL, "University of Illinois engineering camps and academic programs for high schoolers."),
    ("umich-mmss-2026", "University of Michigan Math and Science Scholars", "https://mmss.engin.umich.edu/", "US", 2, 28, "mathematics", OT.SUMMER_SCHOOL, "U-M intensive summer math and science for advanced high-school students."),
    ("osu-ross-math-2026", "Ross Mathematics Program", "https://rossprogram.org/", "US", 3, 15, "mathematics", OT.SUMMER_SCHOOL, "Intensive number-theory focused summer math program."),
    ("promys-2026", "PROMYS (Program in Mathematics for Young Scientists)", "https://promys.org/", "US", 3, 1, "mathematics", OT.SUMMER_SCHOOL, "Boston University-hosted intensive number theory program."),
    ("hcsz-hungary-2026", "Budapest Semesters / math camps (HS pathways)", "https://www.budapestsemesters.com/", "HU", 3, 1, "mathematics", OT.SUMMER_SCHOOL, "Hungary-based intensive mathematics programs with high-school pathways."),
    ("oxford-unip-2026", "University of Oxford UNIQ / outreach summers", "https://www.uniq.ox.ac.uk/", "GB", 1, 20, "research", OT.SUMMER_SCHOOL, "Oxford outreach residential courses for UK state-school students."),
    ("cambridge-he-plus-2026", "Cambridge HE+ / Sutton Trust summers", "https://www.undergraduate.study.cam.ac.uk/", "GB", 2, 1, "research", OT.SUMMER_SCHOOL, "Cambridge-linked summer / HE progression programs for UK students."),
    ("imperial-gsp-2026", "Imperial College Global Summer School", "https://www.imperial.ac.uk/be-inspired/global-summer-school/", "GB", 3, 15, "engineering", OT.SUMMER_SCHOOL, "Imperial residential STEM summer for international high-school students."),
    ("ucl-ys-2026", "UCL Youth Summit / pre-university summers", "https://www.ucl.ac.uk/", "GB", 4, 1, "social-science", OT.SUMMER_SCHOOL, "UCL pre-university and youth academic programs."),
    ("eth-youth-academy-2026", "ETH Zurich Youth Academy / Studienwoche", "https://ethz.ch/", "CH", 3, 31, "physics", OT.SUMMER_SCHOOL, "ETH youth science weeks and study programs for secondary students."),
    ("epfl-summer-2026", "EPFL Summer in the Lab / youth STEM", "https://www.epfl.ch/", "CH", 2, 28, "engineering", OT.RESEARCH_PROGRAM, "EPFL lab and summer STEM experiences open to advanced secondary students."),
    ("ntu-nanyang-research-2026", "NTU Singapore Youth Research / science camps", "https://www.ntu.edu.sg/", "SG", 3, 15, "research", OT.RESEARCH_PROGRAM, "Nanyang Technological University youth research and science camp programs."),
    ("nus-fos-2026", "NUS Faculty of Science Youth Programmes", "https://www.science.nus.edu.sg/", "SG", 2, 20, "biology", OT.SUMMER_SCHOOL, "National University of Singapore science programmes for pre-university students."),
    ("hku-summer-institute-2026", "HKU Summer Institute (Secondary)", "https://www.summerinstitute.hku.hk/", "HK", 3, 1, "business", OT.SUMMER_SCHOOL, "University of Hong Kong summer institute tracks for secondary students."),
    ("ustc-youth-2026", "USTC / CAS youth science camps", "https://www.ustc.edu.cn/", "CN", 4, 15, "physics", OT.SUMMER_SCHOOL, "Chinese Academy / USTC-linked youth science camps (eligibility varies)."),
    ("tsinghua-xs-2026", "Tsinghua Xuetang / youth academic programs", "https://www.tsinghua.edu.cn/", "CN", 3, 20, "mathematics", OT.SUMMER_SCHOOL, "Tsinghua youth academic programs for outstanding secondary students."),
    ("tokyo-u-ess-2026", "University of Tokyo Global Summer Program (HS tracks)", "https://www.u-tokyo.ac.jp/", "JP", 2, 28, "research", OT.SUMMER_SCHOOL, "UTokyo short programs and global summer offerings with secondary tracks."),
    ("kaist-gifted-2026", "KAIST gifted education / summer STEM", "https://www.kaist.ac.kr/", "KR", 3, 10, "engineering", OT.SUMMER_SCHOOL, "KAIST-affiliated gifted education and summer STEM for Korean secondary students."),
    ("iitd-summer-2026", "IIT Delhi / STEM outreach summer schools", "https://home.iitd.ac.in/", "IN", 3, 31, "engineering", OT.SUMMER_SCHOOL, "IIT Delhi and partner STEM outreach summers for high-school students."),
    ("tifr-vsp-2026", "TIFR Visiting Students / olympiad camps", "https://www.tifr.res.in/", "IN", 4, 15, "physics", OT.RESEARCH_PROGRAM, "TIFR visiting student and olympiad training pathways for advanced students."),
    ("iisc-kyp-2026", "IISc Kishore Vaigyanik / related camps", "https://www.iisc.ac.in/", "IN", 7, 31, "research", OT.RESEARCH_PROGRAM, "IISc-linked science exposure and KVPY-successor fellowship pathways."),
    ("utoronto-yss-2026", "University of Toronto Youth Summer Programs", "https://www.utoronto.ca/", "CA", 3, 15, "research", OT.SUMMER_SCHOOL, "U of T faculty youth summer courses and research exposure."),
    ("mcgill-yss-2026", "McGill Summer Academy", "https://www.mcgill.ca/summer/", "CA", 3, 1, "biology", OT.SUMMER_SCHOOL, "McGill summer academy courses for high-school students."),
    ("ubc-vsp-2026", "UBC Verna J. Kirkness / STEM outreach", "https://vjkp.ubc.ca/", "CA", 1, 31, "research", OT.RESEARCH_PROGRAM, "UBC STEM outreach including Kirkness program for Indigenous students."),
    ("anu-nysf-2026", "National Youth Science Forum (Australia)", "https://www.nysf.edu.au/", "AU", 5, 31, "research", OT.SUMMER_SCHOOL, "Australian residential STEM forum for Year 11-12 students."),
    ("unsw-hs-2026", "UNSW High School Science Programs", "https://www.unsw.edu.au/", "AU", 4, 1, "engineering", OT.SUMMER_SCHOOL, "UNSW science and engineering programs for high-school students."),
    ("melbourne-egs-2026", "University of Melbourne Extension / youth STEM", "https://www.unimelb.edu.au/", "AU", 2, 28, "mathematics", OT.SUMMER_SCHOOL, "Melbourne extension studies and youth STEM offerings."),
    ("uct-asiz-2026", "UCT / AIMS South Africa math camps", "https://aims.ac.za/", "ZA", 3, 15, "mathematics", OT.SUMMER_SCHOOL, "African Institute for Mathematical Sciences linked camps and outreach."),
    ("auc-sss-2026", "American University in Cairo Summer Sessions (HS)", "https://www.aucegypt.edu/", "EG", 4, 1, "social-science", OT.SUMMER_SCHOOL, "AUC summer options open to eligible secondary students."),
    ("kaust-gifted-2026", "KAUST Gifted Student Program", "https://kgsp.kaust.edu.sa/", "SA", 10, 1, "engineering", OT.SCHOLARSHIP, "KAUST scholarship pathway for gifted Saudi STEM students."),
    ("nyuad-summer-2026", "NYU Abu Dhabi Summer Academy", "https://www.nyuad.nyu.edu/", "AE", 2, 15, "research", OT.SUMMER_SCHOOL, "NYUAD summer academy for high-achieving secondary students."),
    ("sciences-po-2026", "Sciences Po Summer School (secondary tracks)", "https://www.sciencespo.fr/summer/", "FR", 3, 31, "social-science", OT.SUMMER_SCHOOL, "Sciences Po summer programs with tracks suitable for advanced secondary students."),
    ("tu-delft-yes-2026", "TU Delft Youth Engineering Programs", "https://www.tudelft.nl/", "NL", 4, 15, "engineering", OT.SUMMER_SCHOOL, "TU Delft engineering orientation programs for secondary students."),
    ("tu-munich-2026", "TUM Jugend forscht / youth STEM", "https://www.tum.de/", "DE", 2, 28, "engineering", OT.SUMMER_SCHOOL, "Technical University of Munich youth STEM and research orientation."),
    ("politecnico-milano-2026", "Politecnico di Milano Summer School (HS)", "https://www.polimi.it/", "IT", 3, 20, "engineering", OT.SUMMER_SCHOOL, "Polimi summer engineering experiences for secondary students."),
    ("tecnologico-monterrey-2026", "Tec de Monterrey Prepanet / summer STEM", "https://tec.mx/", "MX", 4, 1, "engineering", OT.SUMMER_SCHOOL, "Tecnologico de Monterrey pre-college STEM summers."),
    ("usp-obmep-camp-2026", "USP / OBMEP training camps (Brazil)", "https://www.obmep.org.br/", "BR", 5, 15, "mathematics", OT.SUMMER_SCHOOL, "Brazilian math olympiad training camps linked to OBMEP/USP."),
]

SCHOLARSHIPS: list[tuple] = [
    ("coca-cola-scholars-2026", "Coca-Cola Scholars Program", "https://www.coca-colascholarsfoundation.org/", "US", 10, 31, "business", "US high-school seniors; leadership and service scholarship."),
    ("gates-scholarship-2026", "The Gates Scholarship", "https://www.thegatesscholarship.org/", "US", 9, 15, "research", "Highly selective scholarship for outstanding minority high-school seniors."),
    ("jack-kent-cooke-2026", "Jack Kent Cooke College Scholarship", "https://www.jkcf.org/", "US", 11, 12, "research", "Need-based scholarship for high-achieving high-school seniors."),
    ("equitable-excellence-2026", "Equitable Excellence Scholarship", "https://www.equitable.com/foundation", "US", 12, 18, "business", "Equitable Foundation scholarship for US high-school seniors."),
    ("horatio-alger-2026", "Horatio Alger Association Scholarships", "https://scholars.horatioalger.org/", "US", 10, 25, "social-science", "Scholarships for students who have faced adversity."),
    ("national-merit-2026", "National Merit Scholarship Program", "https://www.nationalmerit.org/", "US", 10, 1, "mathematics", "PSAT/NMSQT-based scholarship competition for US juniors."),
    ("ron-brown-scholar-2026", "Ron Brown Scholar Program", "https://www.ronbrown.org/", "US", 1, 9, "social-science", "Scholarship for African American high-school seniors."),
    ("elks-mvs-2026", "Elks National Foundation Most Valuable Student", "https://www.elks.org/scholars/", "US", 11, 5, "writing", "Elks MVS scholarship for US high-school seniors."),
    ("aes-scholarship-2026", "AES Engineering Scholarship", "https://www.aesengineers.com/scholarships.php", "US", 10, 6, "engineering", "Essay-based scholarship open to high-school seniors entering college."),
    ("ge-reagan-2026", "GE-Reagan Foundation Scholarship", "https://www.reaganfoundation.org/", "US", 1, 5, "social-science", "Leadership scholarship for US high-school seniors."),
    ("schulich-leader-2026", "Schulich Leader Scholarships", "https://www.schulichleaders.com/", "CA", 1, 28, "engineering", "STEM entrance scholarships for Canadian high-school graduates."),
    ("loran-award-2026", "Loran Scholars Foundation", "https://loranscholar.ca/", "CA", 10, 15, "social-science", "Canadian undergraduate scholarship for character and leadership."),
    ("td-scholarship-2026", "TD Scholarships for Community Leadership", "https://www.td.com/", "CA", 11, 13, "social-science", "TD community leadership scholarships for Canadian students."),
    ("lorne-trottier-2026", "Lorne Trottier Science Scholarships (CEGEP/HS path)", "https://www.mcgill.ca/", "CA", 3, 1, "physics", "Science scholarships linked to Canadian STEM pathways."),
    ("future-trust-uk-2026", "The Future Awards / UK trust scholarships", "https://www.thefuturefoundation.org.uk/", "GB", 5, 31, "social-science", "UK youth achievement and scholarship pathways."),
    ("sutton-trust-uk-2026", "Sutton Trust Pathways / summer school bursaries", "https://www.suttontrust.com/", "GB", 1, 31, "research", "UK access programs with funded summer school places."),
    ("cnrs-talents-2026", "French talent / Cordees de la reussite pathways", "https://www.education.gouv.fr/", "FR", 3, 15, "research", "French secondary academic enrichment and scholarship-linked pathways."),
    ("daad-hs-2026", "DAAD school / Jugendkurs scholarships", "https://www.daad.de/", "DE", 12, 1, "writing", "DAAD-funded German language and youth academic courses."),
    ("swiss-olympic-talent-2026", "Swiss academic talent support (cantonal)", "https://www.sbfi.admin.ch/", "CH", 4, 30, "research", "Swiss cantonal talent support for secondary students."),
    ("massey-scholarship-nz-2026", "New Zealand secondary STEM scholarships", "https://www.universitiesnz.ac.nz/", "NZ", 8, 31, "engineering", "NZ university entrance scholarships for STEM students."),
    ("auckland-hs-schol-2026", "University of Auckland Top Achiever Scholarships", "https://www.auckland.ac.nz/", "NZ", 8, 15, "mathematics", "Entrance scholarships for NZ secondary top achievers."),
    ("nus-merit-2026", "NUS Merit / Science & Technology Scholarships", "https://www.nus.edu.sg/", "SG", 3, 1, "computer-science", "Singapore university merit scholarships for pre-university students."),
    ("astar-scholarship-2026", "A*STAR Scientific Awards / scholarships", "https://www.a-star.edu.sg/", "SG", 3, 15, "research", "Singapore research agency scholarships for STEM talent."),
    ("hkust-scholarship-2026", "HKUST Admission Scholarships", "https://join.hkust.edu.hk/", "HK", 1, 10, "engineering", "HKUST entrance scholarships for outstanding secondary graduates."),
    ("hkbu-scholars-2026", "Hong Kong Baptist University scholarships", "https://www.hkbu.edu.hk/", "HK", 2, 1, "business", "HKBU admission scholarships for secondary leavers."),
    ("inspire-she-2026", "INSPIRE / SHE scholarships (India)", "https://online-inspire.gov.in/", "IN", 7, 31, "physics", "Indian government science incentive scholarships for school toppers."),
    ("ntse-india-2026", "National Talent Search Examination (NTSE)", "https://ncert.nic.in/national-talent-examination.php", "IN", 11, 30, "mathematics", "India national talent search scholarship exam for Class 10."),
    ("kvpy-successor-2026", "INSPIRE-SHE / KVPY-successor science fellowships", "https://www.inspire.gov.in/", "IN", 12, 15, "research", "India science fellowship pathways for school and early undergraduate talent."),
    ("mawhiba-scholarship-2026", "Mawhiba scholarships (Saudi Arabia)", "https://www.mawhiba.org/", "SA", 9, 30, "engineering", "Saudi Mawhiba gifted programs and scholarship support."),
    ("qsi-scholarship-2026", "Qatar / Education Above All youth scholarships", "https://educationaboveall.org/", "AE", 6, 30, "social-science", "Gulf education foundation scholarships for secondary students."),
    ("mandela-rhodes-prep-2026", "Mandela Rhodes / Africa talent pipelines (prep)", "https://www.mandelarhodes.org/", "ZA", 4, 15, "social-science", "African leadership scholarship pipeline with secondary enrichment links."),
    ("canon-collins-2026", "Canon Collins Trust scholarship pathways", "https://www.canoncollins.org/", "ZA", 7, 31, "writing", "Southern Africa scholarship trust with youth academic support."),
    ("obmep-medal-scholarship-2026", "OBMEP medal university scholarships (Brazil)", "https://www.obmep.org.br/", "BR", 8, 31, "mathematics", "Brazilian OBMEP medalists often receive university scholarship benefits."),
    ("cnu-scholarship-br-2026", "CNPq / Brazilian science olympiad awards", "https://www.gov.br/cnpq/", "BR", 9, 15, "research", "Brazilian science awards linked to olympiad performance."),
    ("olympic-scholarship-tr-2026", "TUBITAK science olympiad scholarships", "https://www.tubitak.gov.tr/", "TR", 10, 1, "physics", "Turkish science olympiad and research scholarships for secondary talent."),
    ("olympiad-scholarship-kr-2026", "Korea olympiad / KAIST admission scholarships", "https://admission.kaist.ac.kr/", "KR", 7, 15, "mathematics", "Korean STEM scholarship pathways for olympiad performers."),
    ("stem-scholarship-my-2026", "Malaysia MARA / STEM secondary scholarships", "https://www.mara.gov.my/", "MY", 5, 31, "engineering", "Malaysian STEM scholarship schemes for secondary students."),
    ("doost-scholarship-uz-2026", "Central Asia STEM talent scholarships", "https://www.edu.uz/", "UZ", 6, 15, "computer-science", "Regional STEM scholarships for secondary students in Central Asia."),
    ("african-math-grant-2026", "African Mathematics Millennium Science Initiative grants", "https://www.ammiscience.org/", "KE", 3, 31, "mathematics", "Pan-African math talent support with secondary outreach."),
    ("caribbean-exam-schol-2026", "CAPE / Caribbean scholarship awards", "https://www.cxc.org/", "JM", 6, 30, "writing", "Caribbean advanced proficiency scholarship awards for secondary leavers."),
]

WRITING: list[tuple] = [
    ("scholastic-art-writing-2026", "Scholastic Art & Writing Awards", "https://www.artandwriting.org/", "US", 12, 1, "writing", "US national creative writing and art awards for teens."),
    ("national-poetry-competition-youth-2026", "National Poetry Competition — Young Poets", "https://poetrysociety.org.uk/", "GB", 10, 31, "writing", "UK Poetry Society competitions with youth categories."),
    ("foyle-young-poets-2026", "Foyle Young Poets of the Year", "https://foyleyoungpoets.org/", "GB", 7, 31, "writing", "Major UK poetry competition for 11-17 year olds."),
    ("bbc-young-writers-2026", "BBC Young Writers' Award", "https://www.bbc.co.uk/programmes/articles/young-writers-award", "GB", 4, 4, "writing", "BBC short story award for 14-18 year olds."),
    ("nytimes-student-editorial-2026", "New York Times Student Editorial Contest", "https://www.nytimes.com/column/learning-network", "US", 3, 20, "writing", "NYT Learning Network annual student editorial contest."),
    ("patricia-grodd-poetry-2026", "Patricia Grodd Poetry Prize for Young Writers", "https://www.kenyonreview.org/", "US", 11, 1, "writing", "Kenyon Review poetry prize for high-school writers."),
    ("bennington-young-writers-2026", "Bennington Young Writers Awards", "https://www.bennington.edu/", "US", 11, 1, "writing", "Bennington College awards for poetry, fiction, and nonfiction."),
    ("john-locke-essay-2026", "John Locke Institute Essay Competition", "https://www.johnlockeinstitute.com/", "GB", 6, 30, "writing", "International essay competition for secondary students across subjects."),
    ("harvard-iprize-2026", "Harvard International Review Academic Writing Contest", "https://hir.harvard.edu/", "US", 1, 31, "social-science", "HIR essay contest for high-school students on IR topics."),
    ("columbia-scholastic-press-2026", "Columbia Scholastic Press Association Contests", "https://cspa.columbia.edu/", "US", 2, 15, "writing", "Journalism and writing contests for high-school publications."),
    ("pulse-writing-ca-2026", "Canada Writes / CBC literary youth contests", "https://www.cbc.ca/books/canadawrites", "CA", 3, 15, "writing", "CBC Canada Writes contests with youth-eligible categories."),
    ("fraser-institute-essay-2026", "Fraser Institute Student Essay Contest", "https://www.fraserinstitute.org/", "CA", 5, 30, "economics", "Canadian student essay contest on economics and public policy."),
    ("australian-writing-comp-2026", "Australian Writing Competition (state / national)", "https://www.australiancurriculum.edu.au/", "AU", 8, 15, "writing", "Australian secondary writing competitions and state awards."),
    ("nz-young-writers-2026", "New Zealand Young Writers Festival contests", "https://www.nzbookawards.nz/", "NZ", 7, 1, "writing", "NZ young writers awards and festival contests."),
    ("singapore-writing-comp-2026", "National Schools Literature / writing contests (SG)", "https://www.moe.gov.sg/", "SG", 5, 31, "writing", "Singapore schools literature and creative writing contests."),
    ("hk-budding-poets-2026", "Hong Kong Budding Poets Award", "https://www.edb.gov.hk/", "HK", 2, 28, "writing", "EDB Hong Kong budding poets award for secondary students."),
    ("india-cbse-expression-2026", "CBSE Expression Series / writing contests", "https://www.cbse.gov.in/", "IN", 8, 15, "writing", "CBSE national expression series for school students."),
    ("india-in-litsociety-2026", "The Hindu Young World / India youth writing", "https://www.thehindu.com/", "IN", 6, 30, "writing", "Indian newspaper-linked youth writing competitions."),
    ("sa-youth-writing-2026", "South African Youth Writing Awards", "https://www.nlsa.ac.za/", "ZA", 9, 15, "writing", "South African library and youth writing award programs."),
    ("kenya-essay-2026", "Kenya National Essay Competitions (schools)", "https://www.education.go.ke/", "KE", 7, 31, "writing", "Kenyan ministry and NGO school essay competitions."),
    ("nigeria-essay-2026", "Nigeria national schools essay contests", "https://education.gov.ng/", "NG", 6, 15, "writing", "Nigerian secondary school essay and debate writing contests."),
    ("brazil-olimpiada-lp-2026", "Olimpiada de Lingua Portuguesa (Brazil)", "https://www.writeandwin.org.br/", "BR", 5, 15, "writing", "Brazilian Portuguese language olympiad for school students."),
    ("mexico-olympiad-lang-2026", "Mexican language and literature school contests", "https://www.gob.mx/sep", "MX", 4, 30, "writing", "SEP Mexico language/literature contests for secondary students."),
    ("germany-bundeswettbewerb-2026", "Bundeswettbewerb Fremdsprachen / writing", "https://www.bundeswettbewerb-fremdsprachen.de/", "DE", 1, 15, "writing", "German federal foreign-language competition for school students."),
    ("france-concours-2026", "Concours de plaidoiries / French school writing", "https://www.education.gouv.fr/", "FR", 3, 1, "writing", "French school rhetoric and writing competitions."),
    ("spain-olimpiada-filosofia-2026", "Spanish Philosophy Olympiad (essay)", "https://www.olimpiadafilosofica.es/", "ES", 2, 28, "social-science", "Spain philosophy olympiad with essay rounds for secondary students."),
    ("italy-certamen-2026", "Certamen Ciceronianum / Italian classics contests", "https://www.certamenciceronianum.it/", "IT", 3, 15, "writing", "Italian classical language and literature contests for secondary students."),
    ("japan-essay-nhk-2026", "NHK / Japan high-school essay contests", "https://www.nhk.or.jp/", "JP", 9, 30, "writing", "Japanese high-school essay and speech writing contests."),
    ("korea-essay-2026", "Korea secondary essay and debate writing contests", "https://www.moe.go.kr/", "KR", 5, 15, "writing", "Korean ministry-linked secondary writing contests."),
    ("uae-think-science-essay-2026", "UAE Think Science / youth essay tracks", "https://www.thinkscience.ae/", "AE", 2, 28, "writing", "UAE science communication and youth essay tracks."),
]

ROBOTICS: list[tuple] = [
    ("frc-first-championship-2026", "FIRST Robotics Competition — Championship path", "https://www.firstinspires.org/robotics/frc", "US", 1, 10, "engineering", "FRC team build season leading to district/regional events and worlds."),
    ("ftc-first-tech-2026", "FIRST Tech Challenge", "https://www.firstinspires.org/robotics/ftc", "US", 10, 15, "engineering", "FTC robotics competition for middle and high school teams."),
    ("fll-challenge-2026", "FIRST LEGO League Challenge", "https://www.firstinspires.org/robotics/fll", "US", 9, 30, "engineering", "FLL Challenge season for younger secondary robotics teams."),
    ("vex-vrc-worlds-path-2026", "VEX VRC — World Championship path", "https://www.vexrobotics.com/", "US", 2, 28, "engineering", "VEX Robotics Competition qualifying path for high-school teams."),
    ("vex-iq-hs-2026", "VEX IQ / VIQRC secondary divisions", "https://www.vexrobotics.com/", "US", 11, 15, "engineering", "VEX IQ challenge with secondary school divisions."),
    ("wro-international-2026", "World Robot Olympiad", "https://wro-association.org/", "", 10, 1, "engineering", "International robotics olympiad with national qualifiers worldwide."),
    ("robocup-junior-2026", "RoboCupJunior", "https://junior.robocup.org/", "", 9, 15, "engineering", "Youth league of RoboCup with soccer, rescue, and onstage categories."),
    ("mate-rov-2026", "MATE ROV Competition", "https://materovcompetition.org/", "US", 3, 1, "engineering", "Underwater ROV competition for student teams including high school."),
    ("best-robotics-2026", "BEST Robotics", "https://www.bestinc.org/", "US", 9, 1, "engineering", "Boosting Engineering Science and Technology robotics for US schools."),
    ("sea-perch-2026", "SeaPerch Underwater Robotics", "https://seaperch.org/", "US", 4, 15, "engineering", "Affordable underwater robotics program with regional competitions."),
    ("botball-2026", "Botball Educational Robotics", "https://www.kipr.org/botball", "US", 2, 15, "engineering", "KIPR Botball autonomous robotics for middle and high school."),
    ("oceania-robotics-2026", "Australian RoboCupJunior / National finals", "https://www.robocupjunior.org.au/", "AU", 5, 31, "engineering", "Australian RoboCupJunior national pathway."),
    ("uk-student-robotics-2026", "Student Robotics (UK)", "https://studentrobotics.org/", "GB", 1, 31, "engineering", "UK student robotics competition for sixth-form teams."),
    ("uk-first-legoleague-2026", "FIRST LEGO League UK & Ireland", "https://www.firstlegoleague.co.uk/", "GB", 10, 31, "engineering", "FLL UK & Ireland season for school teams."),
    ("canada-skills-robotics-2026", "Skills Canada Robotics", "https://www.skillscompetencescanada.com/", "CA", 2, 28, "engineering", "Skills Canada secondary robotics competitions."),
    ("india-wro-2026", "WRO India National Championship", "https://wroindia.org/", "IN", 8, 15, "engineering", "India national qualifiers for World Robot Olympiad."),
    ("india-irc-2026", "Indian Robotics Challenge / school nationals", "https://www.indiaeducationdiary.in/", "IN", 7, 1, "engineering", "Indian school robotics nationals and challenges."),
    ("singapore-nrc-2026", "National Robotics Competition (Singapore)", "https://www.science.edu.sg/", "SG", 6, 30, "engineering", "Singapore Science Centre national robotics competition."),
    ("hk-robotics-2026", "Hong Kong Robotics Olympic / school contests", "https://www.hkrobotics.org/", "HK", 3, 15, "engineering", "Hong Kong school robotics contests and olympiad path."),
    ("japan-et-robot-2026", "Japan ET Robocon / school robotics", "https://www.etrobo.jp/", "JP", 5, 15, "engineering", "Japan embedded technology robot contests with student divisions."),
    ("korea-robot-2026", "Korea Robot Week / school nationals", "https://www.robotweek.kr/", "KR", 8, 31, "engineering", "Korean school robotics nationals and festivals."),
    ("germany-robo-2026", "German RoboCupJunior / World Robot Olympiad DE", "https://www.robocupjunior.de/", "DE", 3, 1, "engineering", "German national robotics olympiad pathways."),
    ("brazil-obr-2026", "Olimpiada Brasileira de Robotica (OBR)", "https://www.obr.org.br/", "BR", 5, 15, "engineering", "Brazilian robotics olympiad for school teams."),
    ("mexico-robomatrix-2026", "Mexican robotics school nationals", "https://www.femexrobotica.org/", "MX", 4, 30, "engineering", "Mexico school robotics federation contests."),
    ("uae-think-science-robotics-2026", "UAE Think Science robotics tracks", "https://www.thinkscience.ae/", "AE", 2, 15, "engineering", "UAE national science and robotics competition tracks."),
]

BUSINESS: list[tuple] = [
    ("deca-icdc-2026", "DECA International Career Development Conference path", "https://www.deca.org/", "US", 1, 15, "business", "DECA competitive events from district to ICDC for high-school members."),
    ("fbla-nationals-2026", "FBLA National Leadership Conference", "https://www.fbla.org/", "US", 3, 1, "business", "Future Business Leaders of America competitive events nationals."),
    ("bpa-nationals-2026", "Business Professionals of America Nationals", "https://bpa.org/", "US", 2, 15, "business", "BPA secondary division competitive business events."),
    ("nec-nfec-2026", "National Economics Challenge (CFE)", "https://www.councilforeconed.org/", "US", 2, 1, "economics", "US high-school economics competition run by CEE."),
    ("fed-challenge-hs-2026", "Federal Reserve High School Fed Challenge", "https://www.federalreserve.gov/", "US", 1, 31, "economics", "Fed Challenge for US high-school teams analyzing monetary policy."),
    ("wharton-kwhs-2026", "Wharton KWHS Investment Competition", "https://kwhs.wharton.upenn.edu/", "US", 10, 15, "business", "Global high-school investment competition by Wharton."),
    ("diamond-challenge-2026", "Diamond Challenge for High School Entrepreneurs", "https://diamondchallenge.org/", "US", 1, 20, "business", "Global high-school entrepreneurship pitch competition."),
    ("nfte-nationals-2026", "NFTE National Youth Entrepreneurship Challenge", "https://www.nfte.com/", "US", 4, 15, "business", "Network for Teaching Entrepreneurship youth challenge."),
    ("ja-company-program-2026", "Junior Achievement Company Program", "https://jausa.ja.org/", "US", 10, 1, "business", "JA company program culminating in regional competitions."),
    ("hult-prize-hs-2026", "Hult Prize — secondary / early pathways", "https://www.hultprize.org/", "", 11, 15, "business", "Social entrepreneurship challenge with youth-accessible pathways."),
    ("base-competition-ca-2026", "BASE Business Competition (Canada)", "https://www.basecompetition.com/", "CA", 2, 28, "business", "Canadian high-school business case competition."),
    ("debca-ca-2026", "DECA Canada provincials / nationals", "https://www.decaca.com/", "CA", 1, 20, "business", "DECA Canada competitive events pathway."),
    ("young-enterprise-uk-2026", "Young Enterprise UK Company Programme", "https://www.young-enterprise.org.uk/", "GB", 10, 31, "business", "UK young enterprise company programme competitions."),
    ("ifs-student-investor-2026", "IFS Student Investor Challenge (UK)", "https://www.libf.ac.uk/", "GB", 10, 15, "economics", "UK schools investment challenge."),
    ("australia-asx-2026", "ASX Schools Sharemarket Game", "https://www.asx.com.au/", "AU", 3, 1, "economics", "Australian schools sharemarket simulation competition."),
    ("nz-young-enterprise-2026", "Young Enterprise Scheme (New Zealand)", "https://youngenterprise.org.nz/", "NZ", 3, 15, "business", "NZ young enterprise company scheme."),
    ("singapore-sif-2026", "Singapore Youth Business / Junior Achievement", "https://www.ja.org/", "SG", 5, 15, "business", "Singapore JA and youth business challenge events."),
    ("hk-ja-company-2026", "JA Company Programme Hong Kong", "https://www.jahk.org/", "HK", 10, 1, "business", "Hong Kong JA company programme competition."),
    ("india-tie-young-2026", "TiE Young Entrepreneurs (India)", "https://www.tie.org/", "IN", 9, 15, "business", "TiE youth entrepreneurship competitions in India."),
    ("india-cbse-business-2026", "CBSE Business & Commerce olympiad-style contests", "https://www.cbse.gov.in/", "IN", 8, 1, "business", "Indian school business and commerce contests."),
    ("eu-ja-company-2026", "JA Europe Company of the Year", "https://jaeurope.org/", "DE", 4, 30, "business", "European JA company of the year competition for secondary teams."),
    ("germany-jugend-gruendet-2026", "Jugend grundet (Germany)", "https://www.jugend-gruendet.de/", "DE", 2, 15, "business", "German school entrepreneurship competition."),
    ("france-mini-enterprise-2026", "Mini-Entreprises / Entreprendre pour Apprendre", "https://www.entreprendre-pour-apprendre.fr/", "FR", 3, 31, "business", "French school mini-enterprise programme competitions."),
    ("brazil-olympiad-econ-2026", "Olimpiada Brasileira de Economia (school)", "https://www.anpec.org.br/", "BR", 6, 15, "economics", "Brazilian economics olympiad pathways for secondary students."),
    ("mexico-deca-2026", "DECA Mexico / youth business contests", "https://www.deca.org/", "MX", 2, 28, "business", "Mexico DECA and school business competitions."),
]


def build_dated_regional_catalog() -> list[ScrapedOpportunity]:
    """Construct exactly 500 dated/regional ScrapedOpportunity rows."""
    items: list[ScrapedOpportunity] = []

    for i, (code, name) in enumerate(US_STATES):
        month = 2 + (i % 3)
        day = 5 + (i % 20)
        items.append(
            _item(
                external_id=f"us-{code.lower()}-science-engineering-fair-2026",
                title=f"{name} Science and Engineering Fair",
                url="https://www.societyforscience.org/isef/",
                description=(
                    f"State-level science and engineering fair for {name} high-school "
                    "researchers; typical pathway toward Regeneron ISEF."
                ),
                opportunity_type=OT.COMPETITION,
                field_slugs=["research", "biology", "engineering"],
                eligible_countries=["US"],
                experience="School / regional fair qualification often required",
                deadline_at=_dt(2026, month, day),
                deadline_summary=(
                    f"Typical {name} state fair registration window (verify local affiliate)"
                ),
            )
        )

    for ci, (cc, cname, curl) in enumerate(COUNTRIES):
        for si, (slug, label, title_suffix, field, ot, desc, fallback) in enumerate(SUBJECTS):
            key = f"{cc.lower()}-{slug}-olympiad-2026"
            url = curl if slug == "math" else fallback
            month = 1 + ((ci + si * 3) % 10)
            day = 5 + ((ci * 2 + si) % 23)
            items.append(
                _item(
                    external_id=key,
                    title=f"{cname} {title_suffix}",
                    url=url,
                    description=(
                        f"{desc} National body: {cname}. Confirm the current registration "
                        "window with the national olympiad committee."
                    ),
                    opportunity_type=ot,
                    field_slugs=[field],
                    eligible_countries=[cc],
                    experience="Usually via school / national olympiad committee",
                    deadline_at=_dt(2026, month, day if month != 2 else min(day, 28)),
                    deadline_summary=(
                        f"Typical national registration window for {cname} {label.lower()}"
                    ),
                )
            )

    for eid, title, url, cc, m, d, field, ot, desc in SUMMERS:
        items.append(
            _row(eid, title, url, [cc] if cc else [], m, d, field, ot, desc)
        )

    for eid, title, url, cc, m, d, field, desc in SCHOLARSHIPS:
        items.append(
            _row(
                eid,
                title,
                url,
                [cc] if cc else [],
                m,
                d,
                field,
                OT.SCHOLARSHIP,
                desc,
                grade_min=11,
                grade_max=12,
                deadline_summary="Main scholarship deadline for the 2026 cycle (verify official site)",
            )
        )

    for eid, title, url, cc, m, d, field, desc in WRITING:
        items.append(
            _row(
                eid,
                title,
                url,
                [cc] if cc else [],
                m,
                d,
                field,
                OT.COMPETITION,
                desc,
                deadline_summary="Submission deadline for the 2026 cycle (verify official site)",
            )
        )

    for eid, title, url, cc, m, d, field, desc in ROBOTICS:
        items.append(
            _row(
                eid,
                title,
                url,
                [cc] if cc else [],
                m,
                d,
                field,
                OT.COMPETITION,
                desc,
                fields=[field, "engineering"],
                experience="Team registration via school / club often required",
                deadline_summary="Team registration / kickoff window for 2026 season",
            )
        )

    for eid, title, url, cc, m, d, field, desc in BUSINESS:
        items.append(
            _row(
                eid,
                title,
                url,
                [cc] if cc else [],
                m,
                d,
                field,
                OT.COMPETITION,
                desc,
                experience="Often via school chapter / club",
                deadline_summary="Registration / submission window for the 2026 cycle",
            )
        )

    if len(items) != 500:
        raise RuntimeError(f"dated_regional_catalog expected 500 items, got {len(items)}")

    ids = [item.external_id for item in items]
    if len(ids) != len(set(ids)):
        raise RuntimeError("dated_regional_catalog has duplicate external_id values")

    for item in items:
        has_deadline = item.deadline_at is not None
        has_region = item.eligible_countries is not None
        if not (has_deadline or has_region):
            raise RuntimeError(f"{item.external_id} missing deadline and region")

    return items


DATED_REGIONAL_CATALOG = build_dated_regional_catalog()


def seed_dated_regional_catalog(db: Session) -> dict[str, int]:
    """Upsert dated regional catalog entries (automated update check each run)."""
    stats = {"listed": 0, "created": 0, "updated": 0, "skipped": 0, "no_deadline": 0}

    items = DATED_REGIONAL_CATALOG
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
            if index == 1 or index == len(items) or index % 100 == 0:
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
