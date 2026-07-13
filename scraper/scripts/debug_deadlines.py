from curl_cffi import requests
from bs4 import BeautifulSoup

from scraper.sources.pathways_to_science import (
    _extract_labeled_value,
    parse_detail_page,
    ListingItem,
)
from scraper.parsers.dates import parse_date, pick_notification_deadline

BASE = "https://www.pathwaystoscience.org/"
PROGRAMS = [
    ("FEL-MontanaState-FellScholarships", "no deadline - Montana"),
    ("PDC-NRC-PostDocAwards", "has deadline - NRC"),
    ("FEL-NationalAcademies- Gant", "no deadline - Gant"),
    ("SUM-IRIS-Geosciences", "no deadline - URISE"),
]

for sort_id, label in PROGRAMS:
    url = f"{BASE}programhub.aspx?sort={sort_id}"
    r = requests.get(url, impersonate="chrome131", timeout=30)
    soup = BeautifulSoup(r.text, "lxml")
    main = soup.select_one("div.col-sm-7") or soup
    deadline_label = _extract_labeled_value(main, "Application Deadline")
    content = main.get_text("\n", strip=True)
    parsed_direct = parse_date(deadline_label, end_of_day=True) if deadline_label else None
    parsed_pick, pick_label = pick_notification_deadline(content)
    listing = ListingItem(external_id=sort_id, title=label, url=url)
    scraped = parse_detail_page(r.text, listing)
    print("===", label, "===")
    print("deadline_label:", repr(deadline_label))
    print("parsed_direct:", parsed_direct)
    print("parsed_pick:", parsed_pick, pick_label)
    print("scraped:", scraped.deadline_at)
    # show deadline-related snippets
    for line in content.split("\n"):
        low = line.lower()
        if any(k in low for k in ("deadline", "due", "closes", "application")):
            print(" line:", line[:120])
