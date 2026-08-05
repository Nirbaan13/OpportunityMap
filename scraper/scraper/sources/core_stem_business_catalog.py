"""Core STEM + business/economics catalog — 240 non-Devpost opportunities.

Focus fields: mathematics, physics, chemistry, biology, business, economics.
Every entry sets eligible_countries ([] = worldwide) and a 2026 deadline_at.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.enums import OpportunityType
from scraper.repository import ScrapedOpportunity, upsert_opportunity

logger = logging.getLogger(__name__)

SOURCE_NAME = "core_stem_business_catalog"

OT = OpportunityType


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


MATH_ROWS: list[tuple] = [
    ('amc-10a-2026', 'AMC 10A', 'https://www.maa.org/math-competitions', 'US', 11, 6, 'Multiple-choice AMC 10A for students in grade 10 and below.'),
    ('amc-10b-2026', 'AMC 10B', 'https://www.maa.org/math-competitions', 'US', 11, 12, 'Multiple-choice AMC 10B for students in grade 10 and below.'),
    ('amc-12a-2026', 'AMC 12A', 'https://www.maa.org/math-competitions', 'US', 11, 6, 'Multiple-choice AMC 12A for students in grade 12 and below; AIME qualifier path.'),
    ('amc-12b-2026', 'AMC 12B', 'https://www.maa.org/math-competitions', 'US', 11, 12, 'Multiple-choice AMC 12B for students in grade 12 and below; AIME qualifier path.'),
    ('aime-2026', 'American Invitational Mathematics Examination (AIME)', 'https://www.maa.org/math-competitions', 'US', 2, 5, 'Invite-only AMC follow-on contest toward USA(J)MO.'),
    ('usamo-2026', 'USA Mathematical Olympiad (USAMO)', 'https://www.maa.org/math-competitions', 'US', 3, 18, 'Proof olympiad selecting the US IMO team shortlist.'),
    ('usajmo-2026', 'USA Junior Mathematical Olympiad (USAJMO)', 'https://www.maa.org/math-competitions', 'US', 3, 18, 'Junior proof olympiad for top AMC 10 / AIME performers.'),
    ('purple-comet-2026', 'Purple Comet! Math Meet', 'https://purplecomet.org/', 'US', 4, 1, 'Team math contest for middle and high school.'),
    ('hmmmt-november-2026', 'HMMT November', 'https://www.hmmt.org/', 'US', 10, 15, 'Harvard-MIT Mathematics Tournament November contest.'),
    ('hmmmt-february-2026', 'HMMT February', 'https://www.hmmt.org/', 'US', 1, 20, 'Harvard-MIT Mathematics Tournament February contest.'),
    ('pumac-2026', 'Princeton University Mathematics Competition (PUMaC)', 'https://pumac.princeton.edu/', 'US', 11, 1, 'Team and individual math contest hosted by Princeton.'),
    ('cmimc-2026', 'Carnegie Mellon Informatics and Mathematics Competition', 'https://cmimc.math.cmu.edu/', 'US', 3, 15, 'CMU high-school math and informatics contest.'),
    ('mathcounts-chapter-2026', 'MATHCOUNTS Chapter Competition', 'https://www.mathcounts.org/', 'US', 2, 1, 'Chapter round of the MATHCOUNTS competition series.'),
    ('mathcounts-state-2026', 'MATHCOUNTS State Competition', 'https://www.mathcounts.org/', 'US', 3, 1, 'State round advancing top chapter teams.'),
    ('mathcounts-national-2026', 'MATHCOUNTS National Competition', 'https://www.mathcounts.org/', 'US', 5, 10, 'National finals for MATHCOUNTS state winners.'),
    ('ahsme-emc-2026', 'Euler Math Competition / school invitationals', 'https://www.artofproblems.wordpress.com/', 'US', 4, 20, 'Regional high-school math invitationals in the Euler tradition.'),
    ('ukmt-smc-2026', 'UKMT Senior Mathematical Challenge', 'https://www.ukmt.org.uk/', 'GB', 10, 7, 'UKMT senior multiple-choice challenge for older secondary students.'),
    ('ukmt-bmo2-2026', 'British Mathematical Olympiad Round 2', 'https://bmo.maths.org/', 'GB', 1, 22, 'Second-round UK proof olympiad for top BMO1 scorers.'),
    ('ukmt-kangaroo-grey-2026', 'UKMT Grey Kangaroo', 'https://www.ukmt.org.uk/', 'GB', 3, 19, 'UKMT Kangaroo follow-on for Intermediate Challenge high scorers.'),
    ('smc-canada-2026', 'Canadian Senior Mathematics Contest', 'https://cemc.uwaterloo.ca/', 'CA', 11, 12, 'CEMC senior contest for Canadian secondary students.'),
    ('cayley-contest-2026', 'CEMC Cayley Contest', 'https://cemc.uwaterloo.ca/', 'CA', 2, 25, 'CEMC Cayley contest for grade 10 students.'),
    ('fermat-contest-2026', 'CEMC Fermat Contest', 'https://cemc.uwaterloo.ca/', 'CA', 2, 25, 'CEMC Fermat contest for grade 11 students.'),
    ('euclid-contest-2026', 'CEMC Euclid Contest', 'https://cemc.uwaterloo.ca/', 'CA', 4, 2, 'CEMC Euclid contest widely used for university admissions signals.'),
    ('amc-australia-2026', 'Australian Mathematics Competition (AMC)', 'https://www.amt.edu.au/amc', 'AU', 7, 30, "Australia's largest school mathematics competition."),
    ('aic-australia-2026', 'Australian Intermediate Mathematics Olympiad', 'https://www.amt.edu.au/', 'AU', 8, 20, 'AMT olympiad pathway for intermediate secondary students.'),
    ('nzmc-2026', 'New Zealand Mathematics Competitions', 'https://www.mathsolympiad.org.nz/', 'NZ', 5, 15, 'NZ school mathematics competitions and olympiad pathway.'),
    ('singapore-smo-2026', 'Singapore Mathematical Olympiad (SMO)', 'https://sms.math.nus.edu.sg/smo/', 'SG', 5, 28, 'National math olympiad organized with NUS / SMS.'),
    ('hkamo-heat-2026', 'Hong Kong Academy of Mathematical Olympiad heats', 'https://www.hkamo.org.hk/', 'HK', 9, 15, 'Hong Kong math olympiad training and selection heats.'),
    ('rmo-india-2026', 'India Regional Mathematical Olympiad (RMO)', 'https://olympiads.hbcse.tifr.res.in/', 'IN', 11, 1, 'India regional olympiad after IOQM toward INMO.'),
    ('inmo-india-2026', 'Indian National Mathematical Olympiad (INMO)', 'https://olympiads.hbcse.tifr.res.in/', 'IN', 1, 18, 'India national math olympiad selecting IMO training camp.'),
    ('ioqm-india-2026', 'IOQM — Indian Olympiad Qualifier in Mathematics', 'https://olympiads.hbcse.tifr.res.in/', 'IN', 9, 7, "First stage of India's math olympiad pipeline."),
    ('obmep-l1-2026', 'OBMEP Level 1 (Brazil)', 'https://www.obmep.org.br/', 'BR', 6, 10, 'Brazilian math olympiad for earlier secondary grades.'),
    ('obmep-l2-2026', 'OBMEP Level 2 (Brazil)', 'https://www.obmep.org.br/', 'BR', 6, 10, 'Brazilian math olympiad for later secondary grades.'),
    ('oma-argentina-2026', 'Olimpíada Matemática Argentina (OMA)', 'https://oma.org.ar/', 'AR', 5, 20, 'Argentina national mathematics olympiad stages.'),
    ('omo-mexico-2026', 'Olimpiada Mexicana de Matemáticas', 'https://www.ommenlinea.org/', 'MX', 6, 15, 'Mexico national mathematics olympiad selection.'),
    ('kangourou-france-2026', 'Kangourou des Mathématiques (France)', 'https://www.kangourou.fr/', 'FR', 3, 19, 'French Kangaroo math contest for school students.'),
    ('mo-germany-2026', 'Deutsche Mathematik-Olympiade', 'https://www.mathematik-olympiaden.de/', 'DE', 11, 10, 'German mathematics olympiad regional and national rounds.'),
    ('komal-hungary-2026', 'KöMaL contest problems / Hungary talent path', 'https://www.komal.hu/', 'HU', 9, 30, 'Hungarian KöMaL problem-solving contest tradition for secondary students.'),
    ('imo-shortlist-training-eu-2026', 'European Girls Mathematical Olympiad (EGMO) national selection', 'https://www.egmo.org/', '', 1, 31, 'National selection paths toward EGMO for girls in secondary school.'),
    ('pan-african-math-olympiad-path-2026', 'Pan African Mathematics Olympiad national trials', 'https://www.africamathunion.org/', 'ZA', 3, 15, 'National trials feeding the Pan African Mathematics Olympiad.'),
]

PHYSICS_ROWS: list[tuple] = [
    ('usapho-2026', 'USA Physics Olympiad (USAPhO)', 'https://www.aapt.org/physicsteam/', 'US', 4, 10, 'National physics olympiad selecting the US IPhO team.'),
    ('fma-physicsbowl-2026', 'PhysicsBowl', 'https://www.aapt.org/PhysicsBowl/', 'US', 3, 25, 'AAPT PhysicsBowl contest for US high-school physics students.'),
    ('physics-olympiad-screening-us-2026', 'US Physics Olympiad Screening Exam', 'https://www.aapt.org/physicsteam/', 'US', 1, 20, 'First-round screening for the USAPhO pipeline.'),
    ('iapd-physics-2026', 'International Astronomy and Astrophysics Olympiad national path (US)', 'https://www.aao-olympiad.org/', 'US', 4, 30, 'National pathway contests related to astronomy/astrophysics olympiads.'),
    ('ukpho-2026', 'British Physics Olympiad (BPhO) Round 1', 'https://www.bpho.org.uk/', 'GB', 11, 7, 'UK physics olympiad paper for secondary students.'),
    ('ukpho-round2-2026', 'British Physics Olympiad Round 2 / Astro', 'https://www.bpho.org.uk/', 'GB', 1, 30, 'BPhO follow-on rounds including astrophysics options.'),
    ('physics-challenge-uk-2026', 'BPhO Physics Challenge (GCSE)', 'https://www.bpho.org.uk/', 'GB', 3, 15, 'Physics challenge paper aimed at GCSE-level students.'),
    ('cap-highschool-prize-2026', 'Canadian Association of Physicists High School Prize Exam', 'https://www.cap.ca/', 'CA', 4, 1, 'CAP national high-school physics prize examination.'),
    ('sir-isaac-newton-2026', 'Sir Isaac Newton Exam (Canada)', 'https://uwaterloo.ca/physics-astronomy/', 'CA', 5, 15, 'University of Waterloo high-school physics contest.'),
    ('aspa-physics-2026', 'Australian Science Olympiad Physics program', 'https://www.asi.edu.au/', 'AU', 2, 28, 'Australian Science Olympiad physics selection path toward IPhO.'),
    ('nz-physics-olympiad-2026', 'New Zealand Physics Olympiad', 'https://www.nzpho.org.nz/', 'NZ', 5, 1, 'NZ physics olympiad selection and training.'),
    ('singapore-physics-olympiad-2026', 'Singapore Physics Olympiad', 'https://www.physics.nus.edu.sg/', 'SG', 6, 15, 'National physics olympiad for Singapore pre-university students.'),
    ('hkpho-2026', 'Hong Kong Physics Olympiad', 'https://www.hkage.org.hk/', 'HK', 3, 20, 'Hong Kong physics olympiad for secondary students.'),
    ('india-nsep-2026', 'National Standard Examination in Physics (NSEP)', 'https://www.iapt.org.in/', 'IN', 11, 23, 'India IAPT first-stage physics olympiad exam.'),
    ('india-inpho-2026', 'Indian National Physics Olympiad (INPhO)', 'https://olympiads.hbcse.tifr.res.in/', 'IN', 1, 31, 'India national physics olympiad after NSEP.'),
    ('china-cpho-path-2026', 'China Physics Olympiad provincial rounds', 'https://www.cps-net.org.cn/', 'CN', 9, 15, "Provincial selection rounds for China's physics olympiad."),
    ('japan-physics-challenge-2026', 'Physics Challenge (Japan)', 'https://www.phys-challenge.jp/', 'JP', 6, 1, 'Japan physics challenge / olympiad selection contests.'),
    ('korea-kpho-2026', 'Korea Physics Olympiad', 'https://www.kpho.or.kr/', 'KR', 5, 20, 'Korean physics olympiad national rounds.'),
    ('germany-physik-olympiade-2026', 'Deutsche Physik-Olympiade', 'https://www.scienceolympiaden.de/', 'DE', 11, 15, 'German physics olympiad selection rounds.'),
    ('france-olympiades-physique-2026', 'Olympiades de Physique France', 'https://www.odpf.org/', 'FR', 12, 15, 'French physics olympiad for lycée students.'),
    ('ipho-selection-brazil-2026', 'Olimpíada Brasileira de Física (OBF)', 'https://www.sbfisica.org.br/', 'BR', 5, 30, 'Brazilian physics olympiad toward IPhO selection.'),
    ('mexico-ophysics-2026', 'Olimpiada Mexicana de Física', 'https://www.smf.mx/', 'MX', 6, 10, 'Mexican physics olympiad national selection.'),
    ('south-africa-saphys-2026', 'South African Physics Olympiad', 'https://www.saip.org.za/', 'ZA', 5, 15, 'SAIP physics olympiad for secondary learners.'),
    ('eu-pho-training-2026', 'European Physics Olympiad (EuPhO) national teams', 'https://eupho.ee/', '', 3, 1, 'National team selection toward the European Physics Olympiad.'),
    ('iju-physics-2026', 'International Junior Science Olympiad physics national trials', 'https://www.ijso-official.org/', '', 4, 15, 'National junior science trials with strong physics components.'),
    ('iuso-path-physics-2026', 'International Union of Pure and Applied Physics youth contests', 'https://iupap.org/', '', 6, 30, 'IUPAP-linked youth physics contest pathways by country.'),
    ('astro-olympiad-ioaa-path-2026', 'IOAA national astronomy olympiad selection', 'https://www.ioaastrophysics.org/', '', 5, 1, 'National astronomy/astrophysics olympiad selection toward IOAA.'),
    ('planetarium-research-hs-us-2026', 'High-school planetarium / observational research awards', 'https://www.astroleague.org/', 'US', 3, 31, 'US amateur astronomy research awards open to secondary students.'),
    ('cern-beamline-hs-2026', 'CERN Beamline for Schools', 'https://beamlineforschools.cern/', '', 3, 31, 'International physics competition for high-school teams to run a CERN beam experiment.'),
    ('iypt-path-2026', 'International Young Physicists Tournament national selection', 'https://www.iypt.org/', '', 2, 28, 'Team physics tournament with national selection contests.'),
    ('physicists-tournament-uk-2026', 'UK Young Physicists Tournament', 'https://www.bpho.org.uk/', 'GB', 1, 15, 'UK team physics tournament feeding IYPT.'),
    ('canadawide-science-physics-2026', 'Canada-Wide Science Fair — physics projects', 'https://youthscience.ca/', 'CA', 4, 1, 'National science fair pathway with physics project categories.'),
    ('regeneron-sts-physics-2026', 'Regeneron STS — physics & engineering research', 'https://www.societyforscience.org/regeneron-sts/', 'US', 11, 6, 'US science talent search for independent research including physics.'),
    ('intel-isef-physics-path-2026', 'ISEF physics & astronomy category pathway', 'https://www.societyforscience.org/isef/', 'US', 3, 15, 'Science fair pathway culminating in ISEF physics/astronomy categories.'),
    ('perimeter-issyp-2026', 'Perimeter Institute ISSYP', 'https://www.perimeterinstitute.ca/', 'CA', 2, 1, 'International Summer School for Young Physicists at Perimeter Institute.'),
    ('oxford-physics-challenge-2026', 'Oxford Physics Competition / outreach contests', 'https://www.physics.ox.ac.uk/', 'GB', 2, 15, 'Oxford-linked physics contests and challenge papers for secondary students.'),
    ('mit-physics-hs-contest-2026', 'MIT Physics values / high-school contest events', 'https://physics.mit.edu/', 'US', 1, 31, 'MIT-hosted or affiliated high-school physics contest events.'),
    ('princeton-physics-competition-2026', 'Princeton University Physics Competition', 'https://pupc.princeton.edu/', 'US', 11, 15, 'Princeton high-school physics contest.'),
    ('harvard-hps-2026', 'Harvard Physics Tournament / HS events', 'https://www.physics.harvard.edu/', 'US', 3, 1, 'Harvard-linked high-school physics tournament offerings.'),
    ('rutgers-physics-olympiad-2026', 'Rutgers Physics Olympics', 'https://physicsolympics.rutgers.edu/', 'US', 1, 25, 'Hands-on physics olympics for New Jersey and regional high schools.'),
]

CHEMISTRY_ROWS: list[tuple] = [
    ('usnco-local-2026', 'U.S. National Chemistry Olympiad Local Exam', 'https://www.acs.org/education/students/highschool/olympiad.html', 'US', 3, 1, 'ACS local section exam for the US Chemistry Olympiad.'),
    ('usnco-national-2026', 'U.S. National Chemistry Olympiad National Exam', 'https://www.acs.org/education/students/highschool/olympiad.html', 'US', 4, 20, 'ACS national exam selecting US IChO study camp.'),
    ('chem-olympiad-camp-us-2026', 'US IChO Study Camp', 'https://www.acs.org/education/students/highschool/olympiad.html', 'US', 6, 1, 'Invite-only study camp selecting the US IChO team.'),
    ('acs-chemclub-contest-2026', 'ACS Chemistry Club Contests / ChemLuminary paths', 'https://www.acs.org/', 'US', 2, 15, 'ACS student chapter and chem club contest opportunities.'),
    ('ukcho-2026', 'UK Chemistry Olympiad', 'https://edu.rsc.org/resources/chemistry-olympiad', 'GB', 1, 20, 'Royal Society of Chemistry olympiad for secondary students.'),
    ('cambridge-chemistry-challenge-2026', 'Cambridge Chemistry Challenge (C3L6)', 'https://www.c3l6.com/', 'GB', 6, 1, 'Stretch chemistry challenge paper for UK sixth-form students.'),
    ('rsc-analytical-competition-2026', 'RSC Analytical Chemistry Competition', 'https://edu.rsc.org/', 'GB', 3, 15, 'RSC analytical competition for school teams.'),
    ('avogadro-exam-2026', 'Avogadro Exam (Canada)', 'https://uwaterloo.ca/chemistry/', 'CA', 5, 7, 'University of Waterloo Avogadro chemistry contest for grade 11.'),
    ('chem-13-news-2026', 'Chem 13 News Exam', 'https://uwaterloo.ca/chemistry/', 'CA', 5, 7, 'Waterloo Chem 13 News exam for grade 12 chemistry.'),
    ('asi-chemistry-2026', 'Australian Science Olympiad — Chemistry', 'https://www.asi.edu.au/', 'AU', 2, 28, 'Australian chemistry olympiad selection program.'),
    ('nz-chemistry-olympiad-2026', 'New Zealand Chemistry Olympiad', 'https://www.nzcho.org.nz/', 'NZ', 5, 1, 'NZ chemistry olympiad training and selection.'),
    ('singapore-chemistry-olympiad-2026', 'Singapore Chemistry Olympiad', 'https://www.snics.org.sg/', 'SG', 6, 10, 'National chemistry olympiad for Singapore students.'),
    ('hkcho-2026', 'Hong Kong Chemistry Olympiad', 'https://www.hkage.org.hk/', 'HK', 3, 15, 'Hong Kong chemistry olympiad for secondary students.'),
    ('india-nsec-2026', 'National Standard Examination in Chemistry (NSEC)', 'https://www.iapt.org.in/', 'IN', 11, 23, 'India IAPT first-stage chemistry olympiad exam.'),
    ('india-incho-2026', 'Indian National Chemistry Olympiad (INChO)', 'https://olympiads.hbcse.tifr.res.in/', 'IN', 1, 31, 'India national chemistry olympiad after NSEC.'),
    ('china-ccho-path-2026', 'China Chemistry Olympiad provincial rounds', 'https://www.ccs.ac.cn/', 'CN', 9, 20, 'Provincial chemistry olympiad rounds in China.'),
    ('japan-chemistry-grand-2026', 'Japan Chemistry Grand Contest / olympiad path', 'https://www.jnao.u-tokyo.ac.jp/', 'JP', 6, 15, 'Japanese chemistry olympiad selection contests.'),
    ('korea-kcho-2026', 'Korea Chemistry Olympiad', 'https://www.kcho.or.kr/', 'KR', 5, 15, 'Korean chemistry olympiad national rounds.'),
    ('germany-chemie-olympiade-2026', 'Deutsche Chemie-Olympiade', 'https://www.scienceolympiaden.de/', 'DE', 11, 20, 'German chemistry olympiad selection.'),
    ('france-olympiades-chimie-2026', 'Olympiades Nationales de Chimie', 'https://www.olympiades-chimie.fr/', 'FR', 12, 10, 'French national chemistry olympiad.'),
    ('brazil-obq-2026', 'Olimpíada Brasileira de Química (OBQ)', 'https://www.obquimica.org/', 'BR', 5, 20, 'Brazilian chemistry olympiad.'),
    ('mexico-ochem-2026', 'Olimpiada Mexicana de Química', 'https://www.sqm.org.mx/', 'MX', 6, 5, 'Mexican chemistry olympiad.'),
    ('sa-chemistry-olympiad-2026', 'South African Chemistry Olympiad', 'https://www.saci.co.za/', 'ZA', 5, 10, 'South African chemistry olympiad for learners.'),
    ('icho-eu-training-2026', 'European chemistry olympiad national camps', 'https://www.ichosc.org/', '', 4, 1, 'National training camps feeding IChO from European countries.'),
    ('chemistry-olympiad-ireland-2026', 'Irish Chemistry Olympiad', 'https://www.chemistry.ie/', 'IE', 3, 1, 'Ireland chemistry olympiad selection.'),
    ('chemistry-olympiad-nl-2026', 'Nederlandse Chemie Olympiade', 'https://www.chemieolympiade.nl/', 'NL', 1, 15, 'Dutch chemistry olympiad rounds.'),
    ('chemistry-olympiad-se-2026', 'Swedish Chemistry Olympiad', 'https://www.kva.se/', 'SE', 2, 28, 'Swedish chemistry olympiad selection.'),
    ('chemistry-olympiad-ch-2026', 'Swiss Chemistry Olympiad', 'https://chemistry.olympiad.ch/', 'CH', 1, 31, 'Swiss chemistry olympiad.'),
    ('chemistry-olympiad-pl-2026', 'Olimpiada Chemiczna (Poland)', 'https://www.olchem.edu.pl/', 'PL', 10, 15, 'Polish chemistry olympiad.'),
    ('chemistry-olympiad-ro-2026', 'Olimpiada de Chimie (Romania)', 'https://www.sscr.ro/', 'RO', 2, 20, 'Romanian chemistry olympiad.'),
    ('ycs-uk-2026', 'Young Chemists Symposium / RSC youth events', 'https://www.rsc.org/', 'GB', 4, 30, 'RSC youth chemistry presentation and competition events.'),
    ('crystal-growing-competition-2026', 'IUCr Crystal Growing Competition', 'https://www.iycr2014.org/', '', 10, 15, 'International school crystal-growing competition.'),
    ('chem-magic-show-contest-in-2026', 'India interschool chemistry quiz / science congress chem', 'https://www.isc.in/', 'IN', 8, 15, 'Indian school chemistry quizzes and science congress chemistry sections.'),
    ('acs-project-seed-2026', 'ACS Project SEED', 'https://www.acs.org/education/students/highschool/seed.html', 'US', 2, 1, 'Summer research for economically disadvantaged high-school chemistry students.'),
    ('rsc-spectroscopy-in-a-suitcase-2026', 'RSC Spectroscopy competitions / school challenges', 'https://edu.rsc.org/', 'GB', 5, 15, 'RSC school spectroscopy challenges and related contests.'),
    ('water-quality-chem-fair-2026', 'Stockholm Junior Water Prize national selections', 'https://www.siwi.org/stockholmjuniorwaterprize/', '', 4, 15, 'National water research prize selections with strong chemistry projects.'),
    ('green-chemistry-hs-challenge-2026', 'ACS Green Chemistry student challenges', 'https://www.acs.org/greenchemistry.html', 'US', 3, 31, 'Green chemistry design challenges for high-school students.'),
    ('polymer-science-olympiad-path-2026', 'Polymer / materials chemistry school contests', 'https://www.polymers.eu/', 'DE', 6, 1, 'European materials/polymer chemistry contests for secondary students.'),
    ('food-chemistry-olympiad-2026', 'Food chemistry olympiad-style school contests', 'https://www.ift.org/', 'US', 2, 28, 'Food science and chemistry contests for high-school teams.'),
    ('environmental-chem-olympiad-2026', 'Environmental chemistry olympiad national trials', 'https://www.acs.org/', 'US', 4, 10, 'Environmental chemistry contest tracks within national science olympiads.'),
]

BIOLOGY_ROWS: list[tuple] = [
    ('usabo-open-2026', 'USA Biology Olympiad Open Exam', 'https://www.usabo-trc.org/', 'US', 2, 3, 'Open exam for the USA Biology Olympiad.'),
    ('usabo-semifinal-2026', 'USA Biology Olympiad Semifinal', 'https://www.usabo-trc.org/', 'US', 3, 10, 'Semifinal round for top USABO Open scorers.'),
    ('usabo-national-finals-2026', 'USA Biology Olympiad National Finals', 'https://www.usabo-trc.org/', 'US', 5, 20, 'Finals selecting the US IBO team.'),
    ('brain-bee-nationals-2026', 'International Brain Bee — US nationals path', 'https://www.thebrainbee.org/', 'US', 3, 15, 'Neuroscience competition for high-school students.'),
    ('ukabo-2026', 'British Biology Olympiad', 'https://www.ukbiologycompetitions.org/', 'GB', 1, 15, 'UK biology olympiad for secondary students.'),
    ('biology-challenge-uk-2026', 'Biology Challenge (UK intermediate)', 'https://www.ukbiologycompetitions.org/', 'GB', 4, 20, 'Intermediate UK biology competition.'),
    ('asi-biology-2026', 'Australian Science Olympiad — Biology', 'https://www.asi.edu.au/', 'AU', 2, 28, 'Australian biology olympiad selection program.'),
    ('nz-biology-olympiad-2026', 'New Zealand Biology Olympiad', 'https://www.nzibo.org.nz/', 'NZ', 5, 1, 'NZ biology olympiad selection and training.'),
    ('singapore-biology-olympiad-2026', 'Singapore Biology Olympiad', 'https://www.sbol.org.sg/', 'SG', 6, 5, 'National biology olympiad for Singapore students.'),
    ('hkbo-2026', 'Hong Kong Biology Olympiad', 'https://www.hkage.org.hk/', 'HK', 3, 10, 'Hong Kong biology olympiad.'),
    ('india-nseb-2026', 'National Standard Examination in Biology (NSEB)', 'https://www.iapt.org.in/', 'IN', 11, 23, 'India IAPT first-stage biology olympiad exam.'),
    ('india-inbo-2026', 'Indian National Biology Olympiad (INBO)', 'https://olympiads.hbcse.tifr.res.in/', 'IN', 1, 31, 'India national biology olympiad after NSEB.'),
    ('canada-biology-olympiad-2026', 'Canadian Biology Olympiad', 'https://www.biolympiads.ca/', 'CA', 4, 15, 'Canadian biology olympiad selection.'),
    ('brain-bee-canada-2026', 'Canadian Brain Bee', 'https://www.thebrainbee.org/', 'CA', 3, 1, 'Canadian neuroscience quiz competition for high schoolers.'),
    ('germany-biologie-olympiade-2026', 'Deutsche Biologie-Olympiade', 'https://www.scienceolympiaden.de/', 'DE', 11, 10, 'German biology olympiad.'),
    ('france-olympiades-bio-2026', 'Olympiades de Biologie / SVT contests', 'https://www.education.gouv.fr/', 'FR', 12, 5, 'French biology/SVT olympiad-style contests.'),
    ('brazil-obb-2026', 'Olimpíada Brasileira de Biologia (OBB)', 'https://www.olimpiadasdebiologia.com.br/', 'BR', 5, 15, 'Brazilian biology olympiad.'),
    ('mexico-obio-2026', 'Olimpiada Mexicana de Biología', 'https://www.omb.org.mx/', 'MX', 6, 1, 'Mexican biology olympiad.'),
    ('sa-biology-olympiad-2026', 'South African Biology Olympiad', 'https://www.saasta.ac.za/', 'ZA', 5, 10, 'South African biology olympiad for learners.'),
    ('ibo-eu-training-2026', 'European biology olympiad national camps', 'https://www.ibo-info.org/', '', 4, 1, 'National training camps feeding IBO.'),
    ('ieo-path-ecology-2026', 'International Earth Science / ecology olympiad national trials', 'https://www.ieso-info.org/', '', 3, 15, 'Earth science and ecology olympiad national pathways.'),
    ('genetics-olympiad-us-2026', 'American Society of Human Genetics DNA Day essay', 'https://www.ashg.org/', 'US', 3, 3, 'ASHG DNA Day essay contest for high-school students.'),
    ('biotech-challenge-ca-2026', 'Biotechnology Heritage Award / Sanofi Biogenius Canada', 'https://www.biogenius.ca/', 'CA', 1, 31, 'Canadian high-school biotechnology research competition.'),
    ('isef-biology-path-2026', 'ISEF cellular/molecular biology category pathway', 'https://www.societyforscience.org/isef/', 'US', 3, 15, 'Science fair pathway into ISEF biology categories.'),
    ('regeneron-sts-bio-2026', 'Regeneron STS — biology research', 'https://www.societyforscience.org/regeneron-sts/', 'US', 11, 6, 'Independent biology research talent search for US seniors.'),
    ('broadcom-masters-bio-2026', 'Broadcom MASTERS — life science projects', 'https://www.societyforscience.org/broadcom-masters/', 'US', 6, 1, 'Middle-school STEM fair competition with life-science tracks.'),
    ('genes-in-space-2026', 'Genes in Space', 'https://www.genesinspace.org/', 'US', 3, 1, 'DNA experiment design competition; winners may fly experiments.'),
    ('explora-vision-bio-2026', 'ExploraVision — biomedical technology visions', 'https://www.exploravision.org/', 'US', 2, 3, 'Toshiba/NSTA technology competition with strong bio/med tracks.'),
    ('jj-scholastic-bio-2026', 'Junior Science and Humanities Symposium — life sciences', 'https://www.jshs.org/', 'US', 1, 5, 'Regional JSHS research symposia including life sciences.'),
    ('rsi-bio-track-2026', 'Research Science Institute (biology placements)', 'https://www.cee.org/programs/rsi', 'US', 1, 15, 'Highly selective summer research; many students pursue biology projects.'),
    ('ssp-bio-2026', 'Summer Science Program — biochemistry tracks', 'https://www.summerscience.org/', 'US', 2, 22, 'SSP residential research program with biochemistry/astrophysics tracks.'),
    ('rockefeller-summer-bio-2026', 'Rockefeller University Summer Neuroscience / bio outreach', 'https://www.rockefeller.edu/', 'US', 3, 1, 'Rockefeller summer research exposures for high-school students.'),
    ('cold-spring-harbor-dna-2026', 'Cold Spring Harbor DNA Learning Center programs', 'https://dnalc.cshl.edu/', 'US', 4, 1, 'DNA lab workshops and contests for secondary students.'),
    ('wellcome-genome-hs-2026', 'Wellcome Genome Campus youth science competitions', 'https://www.wellcomegenomecampus.org/', 'GB', 5, 15, 'Genome Campus school science challenges and competitions.'),
    ('pasteur-foundation-hs-2026', 'Institut Pasteur youth science contests', 'https://www.pasteur.fr/', 'FR', 3, 31, 'Pasteur-linked youth biology contests and olympiad support.'),
    ('max-planck-school-bio-2026', 'Max Planck school research internships (bio)', 'https://www.mpg.de/', 'DE', 2, 28, 'Max Planck outreach research experiences for secondary students.'),
    ('riken-hs-bio-2026', 'RIKEN high-school biology research programs', 'https://www.riken.jp/', 'JP', 5, 1, 'RIKEN-linked high-school biology research exposures.'),
    ('a-star-bio-hs-2026', 'A*STAR youth biomedical research attachments', 'https://www.a-star.edu.sg/', 'SG', 3, 15, 'Singapore biomedical research attachments for pre-university students.'),
    ('iisc-biology-summer-2026', 'IISc / NCBS biology summer exposure programs', 'https://www.ncbs.res.in/', 'IN', 3, 31, 'Biology research exposure programs for Indian high-school students.'),
    ('olympiad-neuroscience-eu-2026', 'International Neuroscience Olympiad national trials', 'https://www.thebrainbee.org/', '', 2, 15, 'Brain Bee / neuroscience olympiad national championships worldwide.'),
]

BUSINESS_ROWS: list[tuple] = [
    ('deca-principles-marketing-2026', 'DECA Principles of Business Administration events', 'https://www.deca.org/', 'US', 1, 15, 'DECA principles events for first-year high-school members.'),
    ('deca-business-services-2026', 'DECA Business Management and Administration series', 'https://www.deca.org/', 'US', 1, 15, 'DECA competitive events in business management tracks.'),
    ('deca-finance-series-2026', 'DECA Finance Career Cluster events', 'https://www.deca.org/', 'US', 1, 15, 'DECA finance events from district to ICDC.'),
    ('deca-hospitality-2026', 'DECA Hospitality and Tourism events', 'https://www.deca.org/', 'US', 1, 15, 'DECA hospitality competitive events.'),
    ('deca-entrepreneurship-2026', 'DECA Entrepreneurship series', 'https://www.deca.org/', 'US', 1, 15, 'DECA entrepreneurship written and role-play events.'),
    ('fbla-business-plan-2026', 'FBLA Business Plan competitive event', 'https://www.fbla.org/', 'US', 3, 1, 'FBLA business plan event at state and national levels.'),
    ('fbla-intro-business-2026', 'FBLA Introduction to Business Concepts', 'https://www.fbla.org/', 'US', 3, 1, 'FBLA objective test event for newer members.'),
    ('fbla-marketing-2026', 'FBLA Marketing competitive events', 'https://www.fbla.org/', 'US', 3, 1, 'FBLA marketing events including role-play and tests.'),
    ('fbla-imc-2026', 'FBLA Impromptu Speaking / business communication', 'https://www.fbla.org/', 'US', 3, 1, 'FBLA communication events for business students.'),
    ('bpa-finance-2026', 'BPA Financial Analyst / finance events', 'https://bpa.org/', 'US', 2, 15, 'Business Professionals of America finance competitive events.'),
    ('bpa-entrepreneurship-2026', 'BPA Entrepreneurship Concepts', 'https://bpa.org/', 'US', 2, 15, 'BPA entrepreneurship competitive events.'),
    ('nfec-personal-finance-2026', 'National Financial Capability Challenge / related contests', 'https://www.councilforeconed.org/', 'US', 4, 1, 'Personal finance contests for US high-school students.'),
    ('stock-market-game-us-2026', 'Stock Market Game (SIFMA Foundation)', 'https://www.stockmarketgame.org/', 'US', 8, 15, 'Classroom investing simulation competition.'),
    ('capitol-hill-challenge-2026', 'Capitol Hill Challenge', 'https://www.stockmarketgame.org/', 'US', 9, 1, 'SIFMA investing competition with Washington recognition events.'),
    ('ja-company-us-regionals-2026', 'Junior Achievement Company of the Year (US regions)', 'https://jausa.ja.org/', 'US', 4, 30, 'JA company programme regional competitions.'),
    ('diamond-challenge-innovation-2026', 'Diamond Challenge Innovation pitch', 'https://diamondchallenge.org/', 'US', 1, 20, 'High-school innovation pitch track of Diamond Challenge.'),
    ('diamond-challenge-social-2026', 'Diamond Challenge Social Innovation', 'https://diamondchallenge.org/', 'US', 1, 20, 'Social entrepreneurship track for high-school founders.'),
    ('nfte-regional-2026', 'NFTE regional youth entrepreneurship challenges', 'https://www.nfte.com/', 'US', 3, 15, 'Regional NFTE pitch competitions.'),
    ('coolest-projects-business-2026', 'Coolest Projects — enterprise / software for business', 'https://coolestprojects.org/', '', 5, 1, 'Youth project showcase including enterprise software projects.'),
    ('tigers-pitch-asia-2026', 'Tiger entrepreneurs / Asia high-school pitch contests', 'https://www.tie.org/', 'SG', 9, 15, 'Asia TiE and related high-school pitch contests.'),
    ('young-enterprise-ireland-2026', 'Young Enterprise Ireland / Student Enterprise Programme', 'https://studententerprise.ie/', 'IE', 3, 1, 'Irish student enterprise competition.'),
    ('young-enterprise-scotland-2026', 'Young Enterprise Scotland Company Programme', 'https://www.yes.org.uk/', 'GB', 10, 31, 'Scotland young enterprise company competitions.'),
    ('ja-europe-innovation-camp-2026', 'JA Europe Innovation Camp', 'https://jaeurope.org/', 'DE', 3, 15, 'European JA innovation camps for secondary students.'),
    ('enterprise-challenge-uk-2026', 'TEN / Enterprise Challenge UK schools', 'https://www.ten.org.uk/', 'GB', 2, 28, 'UK school enterprise challenges.'),
    ('asx-sharemarket-advanced-2026', 'ASX Schools Sharemarket Game (advanced rounds)', 'https://www.asx.com.au/', 'AU', 3, 1, 'Australian schools investing competition.'),
    ('nz-young-enterprise-awards-2026', 'Young Enterprise Scheme Awards (NZ)', 'https://youngenterprise.org.nz/', 'NZ', 9, 15, 'NZ young enterprise award finals.'),
    ('singapore-sme-youth-2026', 'SME Young Entrepreneurs / startups@schools (SG)', 'https://www.sme.org.sg/', 'SG', 6, 1, 'Singapore school entrepreneurship contests.'),
    ('hk-jumpstarter-hs-2026', 'Hong Kong school entrepreneurship contests / Jumpstarter youth', 'https://www.alibabacloud.com/jumpstarter', 'HK', 5, 15, 'Hong Kong youth entrepreneurship competition tracks.'),
    ('india-startup-india-school-2026', 'Startup India school challenge / entrepreneurship olympiad', 'https://www.startupindia.gov.in/', 'IN', 8, 15, 'Indian school entrepreneurship challenges.'),
    ('wharton-global-hs-investment-2026', 'Wharton Global High School Investment Competition', 'https://kwhs.wharton.upenn.edu/', '', 10, 15, 'Global online investment competition for high-school teams.'),
    ('blue-ocean-competition-hs-2026', 'Blue Ocean High School Entrepreneurship Competition', 'https://blueoceancompetition.org/', 'US', 1, 31, 'High-school competition applying Blue Ocean Strategy.'),
    ('congstar-business-olympiad-eu-2026', 'European Business Olympiad / school case contests', 'https://www.jaeurope.org/', 'BE', 4, 15, 'European school business case olympiad-style contests.'),
    ('case-competition-rotman-hs-2026', 'Rotman high-school business challenges', 'https://www.rotman.utoronto.ca/', 'CA', 2, 15, 'Rotman-linked high-school business and accounting challenges.'),
    ('smith-school-business-hs-2026', "Queen's Smith high-school business contests", 'https://smith.queensu.ca/', 'CA', 3, 1, 'Canadian high-school business contest offerings.'),
    ('ivey-hs-business-2026', 'Ivey Business School high-school events', 'https://www.ivey.uwo.ca/', 'CA', 2, 28, 'Ivey outreach case events for secondary students.'),
    ('nush-business-week-2026', 'NUS / SMU youth business case competitions', 'https://www.smu.edu.sg/', 'SG', 5, 20, 'Singapore university-hosted youth business cases.'),
    ('lse-su-hs-business-2026', 'LSE SU economics & business essay / case events', 'https://www.lsesu.com/', 'GB', 3, 31, 'LSE student-union contests open to sixth-form business students.'),
    ('insead-youth-business-2026', 'INSEAD youth entrepreneurship outreach contests', 'https://www.insead.edu/', 'FR', 4, 15, 'INSEAD-linked youth entrepreneurship contests in Europe/Asia.'),
    ('tec-business-challenge-mx-2026', 'Tec de Monterrey high-school business challenges', 'https://tec.mx/', 'MX', 4, 1, 'Mexican pre-college business case and entrepreneurship contests.'),
    ('fgv-business-olympiad-br-2026', 'FGV / Brazilian school business olympiads', 'https://portal.fgv.br/', 'BR', 6, 15, 'Brazilian business olympiad and case contests for secondary students.'),
]

ECONOMICS_ROWS: list[tuple] = [
    ('nec-state-2026', 'National Economics Challenge — State rounds', 'https://www.councilforeconed.org/national-economics-challenge/', 'US', 3, 1, 'State-level economics challenge for US high-school teams.'),
    ('nec-national-2026', 'National Economics Challenge — National finals', 'https://www.councilforeconed.org/national-economics-challenge/', 'US', 5, 15, 'National finals of the CEE economics challenge.'),
    ('fed-challenge-district-2026', 'High School Fed Challenge — District', 'https://www.federalreserve.gov/', 'US', 2, 15, 'District Fed Challenge monetary policy competition.'),
    ('fed-challenge-national-2026', 'High School Fed Challenge — National', 'https://www.federalreserve.gov/', 'US', 5, 1, 'National Fed Challenge finals.'),
    ('econbowl-2026', 'EconBowl', 'https://www.econ.berkeley.edu/', 'US', 11, 15, 'Quiz-bowl style economics competition for high schools.'),
    ('econolympiad-us-2026', 'International Economics Olympiad — US selection', 'https://ecolymp.org/', 'US', 4, 1, 'US pathway toward the International Economics Olympiad.'),
    ('ieo-international-2026', 'International Economics Olympiad', 'https://ecolymp.org/', '', 7, 15, 'Global economics olympiad for secondary students.'),
    ('harvard-iec-2026', 'Harvard International Economics Essay Contest links / HUEJ', 'https://economics.harvard.edu/', 'US', 1, 31, 'Harvard-linked high-school economics essay opportunities.'),
    ('wharton-econ-essay-2026', 'Wharton / Penn high-school economics essay contests', 'https://www.wharton.upenn.edu/', 'US', 2, 15, 'Penn/Wharton economics writing contests for secondary students.'),
    ('fraser-econ-essay-2026', 'Fraser Institute Student Essay Contest (economics)', 'https://www.fraserinstitute.org/', 'CA', 5, 30, 'Canadian economics and public policy essay contest.'),
    ('bank-of-canada-challenge-2026', "Bank of Canada Governor's Challenge (HS outreach)", 'https://www.bankofcanada.ca/', 'CA', 10, 15, 'BoC monetary policy challenge with youth outreach tracks.'),
    ('rba-cup-2026', 'RBA Cup / Australian economics competitions', 'https://www.rba.gov.au/', 'AU', 5, 1, 'Reserve Bank of Australia linked economics competitions for schools.'),
    ('wes-australia-2026', 'Australian Economics Olympiad / WEA contests', 'https://www.ecosoc.org.au/', 'AU', 6, 15, 'Australian school economics contests and olympiad path.'),
    ('uk-economics-olympiad-2026', 'UK Economics Olympiad / essay competitions', 'https://www.economicseducation.org/', 'GB', 3, 15, 'UK school economics olympiad and essay contests.'),
    ('tutor2u-econ-essay-2026', 'Tutor2u / UK A-level economics essay competitions', 'https://www.tutor2u.net/', 'GB', 4, 30, 'UK A-level economics essay and analysis competitions.'),
    ('ies-essay-uk-2026', 'Institute of Economic Affairs student essay prizes', 'https://iea.org.uk/', 'GB', 5, 15, 'IEA student essay prizes open to sixth-form economists.'),
    ('singapore-economics-olympiad-2026', 'Singapore Economics Olympiad', 'https://www.ess.org.sg/', 'SG', 5, 20, 'Singapore economics olympiad for pre-university students.'),
    ('hk-economics-olympiad-2026', 'Hong Kong Economics Olympiad', 'https://www.hkage.org.hk/', 'HK', 3, 20, 'Hong Kong economics olympiad for secondary students.'),
    ('india-economics-olympiad-2026', 'Indian Economics Olympiad / IEO national path', 'https://ecolymp.org/', 'IN', 4, 15, 'India selection contests toward the International Economics Olympiad.'),
    ('china-economics-olympiad-2026', 'China Economics Olympiad national rounds', 'https://ecolymp.org/', 'CN', 5, 1, 'Chinese national rounds feeding IEO.'),
    ('germany-wirtschaft-olympiade-2026', 'German Economics Olympiad / Jugend debattiert econ tracks', 'https://www.wirtschaftsolympiade.de/', 'DE', 2, 28, 'German school economics olympiad.'),
    ('france-olympiades-eco-2026', "Olympiades d'Économie (France)", 'https://www.education.gouv.fr/', 'FR', 12, 10, 'French economics olympiad for lycée students.'),
    ('brazil-obecon-2026', 'Olimpíada Brasileira de Economia', 'https://www.anpec.org.br/', 'BR', 6, 15, 'Brazilian economics olympiad.'),
    ('mexico-economia-olympiad-2026', 'Mexican economics olympiad / school contests', 'https://www.banxico.org.mx/', 'MX', 5, 15, 'Mexico school economics contests and olympiad-style events.'),
    ('sa-economics-olympiad-2026', 'South African Economics Olympiad', 'https://www.essa.org.za/', 'ZA', 5, 10, 'South African economics olympiad for learners.'),
    ('nz-economics-competition-2026', 'NZ Economics Competition', 'https://www.nzecon.org.nz/', 'NZ', 6, 1, 'New Zealand secondary economics competition.'),
    ('euro-challenge-2026', 'Euro Challenge', 'https://www.euro-challenge.org/', 'US', 2, 15, 'US high-school competition analyzing European economies.'),
    ('world-economics-cup-2026', 'World Economics Cup / school rounds', 'https://www.worldeconomicscup.org/', '', 3, 31, 'International economics competition for high-school teams.'),
    ('ipe-essay-2026', 'International Political Economy essay contests (HS)', 'https://www.cfr.org/', 'US', 4, 1, 'Foreign-policy and IPE essay contests open to high-school students.'),
    ('ft-schools-comp-2026', 'Financial Times schools competitions', 'https://www.ft.com/', 'GB', 3, 1, 'FT-linked schools competitions on markets and current economics.'),
    ('economist-essay-hs-2026', 'The Economist Open Future / youth essay tracks', 'https://www.economist.com/', '', 5, 15, 'Economist youth essay and open-future style competitions.'),
    ('imf-essay-youth-2026', 'IMF youth economics essay / blog contests', 'https://www.imf.org/', '', 6, 30, 'IMF youth economics communication contests.'),
    ('world-bank-youth-econ-2026', 'World Bank Youth Summit essay / proposal contests', 'https://www.worldbank.org/', '', 2, 28, 'World Bank youth proposal contests with economics themes.'),
    ('nabe-econ-challenge-2026', 'NABE Foundation economics challenges / scholarships', 'https://www.nabe.com/', 'US', 4, 15, 'National Association for Business Economics student challenges.'),
    ('cee-econ-video-2026', 'CEE National Personal Finance Challenge', 'https://www.councilforeconed.org/', 'US', 4, 20, 'Personal finance team challenge from Council for Economic Education.'),
    ('qe-prize-schools-2026', 'Queen Elizabeth Prize schools / innovation-econ outreach', 'https://qeprize.org/', 'GB', 5, 1, 'QEPrize school challenges linking innovation and economic impact.'),
    ('adam-smith-essay-2026', 'Adam Smith Institute / liberty essay prizes (students)', 'https://www.adamsmith.org/', 'GB', 6, 15, 'Student essay prizes on markets and classical economics.'),
    ('mises-essay-hs-2026', 'Mises Institute student essay contest', 'https://mises.org/', 'US', 7, 31, 'Essay contest on Austrian economics themes for students.'),
    ('st-gallen-symposium-hs-2026', 'St. Gallen Symposium essay competition (young leaders)', 'https://www.symposium.org/', 'CH', 2, 1, 'Essay competition; strong pre-university candidates sometimes participate.'),
    ('european-central-bank-youth-2026', 'ECB youth Generation €uro competition', 'https://www.ecb.europa.eu/', 'DE', 12, 15, 'Euro-area schools competition on monetary policy.'),
]


def _type_for(title: str, default: OpportunityType) -> OpportunityType:
    lower = title.lower()
    if any(token in lower for token in ("summer", "research institute", "internship", "attachment", "seed")):
        if "scholarship" in lower:
            return OT.SCHOLARSHIP
        return OT.RESEARCH_PROGRAM if "research" in lower or "seed" in lower else OT.SUMMER_SCHOOL
    if "olympiad" in lower or "usamo" in lower or "usajmo" in lower or "usapho" in lower or "usabo" in lower:
        return OT.OLYMPIAD
    if "scholarship" in lower:
        return OT.SCHOLARSHIP
    return default


def build_core_stem_business_catalog() -> list[ScrapedOpportunity]:
    items: list[ScrapedOpportunity] = []
    for field, rows, default_ot in (
        ("mathematics", MATH_ROWS, OT.COMPETITION),
        ("physics", PHYSICS_ROWS, OT.COMPETITION),
        ("chemistry", CHEMISTRY_ROWS, OT.COMPETITION),
        ("biology", BIOLOGY_ROWS, OT.COMPETITION),
        ("business", BUSINESS_ROWS, OT.COMPETITION),
        ("economics", ECONOMICS_ROWS, OT.COMPETITION),
    ):
        for eid, title, url, cc, month, day, desc in rows:
            safe_day = min(day, 28) if month == 2 else day
            items.append(
                _item(
                    external_id=eid,
                    title=title,
                    url=url,
                    description=desc,
                    opportunity_type=_type_for(title, default_ot),
                    field_slugs=[field],
                    eligible_countries=[cc] if cc else [],
                    deadline_at=_dt(2026, month, safe_day),
                    deadline_summary=(
                        "Registration / application window for the 2026 cycle "
                        "(verify official site)"
                    ),
                )
            )

    if len(items) != 240:
        raise RuntimeError(f"core_stem_business_catalog expected 240 items, got {len(items)}")
    ids = [i.external_id for i in items]
    if len(ids) != len(set(ids)):
        raise RuntimeError("core_stem_business_catalog has duplicate external_id values")
    for item in items:
        if item.deadline_at is None or item.eligible_countries is None:
            raise RuntimeError(f"{item.external_id} missing deadline or region")
    return items


CORE_STEM_BUSINESS_CATALOG = build_core_stem_business_catalog()


def seed_core_stem_business_catalog(db: Session) -> dict[str, int]:
    """Upsert core STEM/business catalog entries."""
    stats = {"listed": 0, "created": 0, "updated": 0, "skipped": 0, "no_deadline": 0}
    items = CORE_STEM_BUSINESS_CATALOG
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
            if index == 1 or index == len(items) or index % 80 == 0:
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
