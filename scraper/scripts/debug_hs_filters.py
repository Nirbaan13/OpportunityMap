from curl_cffi import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs

BASE = "https://www.pathwaystoscience.org/"
searches = [
    ("HighSchool adv", "programs.aspx?u=&r=&s=HighSchool&sa=either&p=either&o=either&c=either&f=&dd=&ft=&submit=y&adv=adv"),
    ("HighSchool comp", "programs.aspx?u=&r=&s=HighSchool&sa=either&p=either&o=Competition&c=either&f=&dd=&ft=&submit=y&adv=adv"),
    ("Summer HS", "programs.aspx?descriptorhub=SummerResearch_Summer Research Opportunity"),
]

for name, path in searches:
    r = requests.get(BASE + path, impersonate="chrome131", timeout=30)
    soup = BeautifulSoup(r.text, "lxml")
    items = []
    seen = set()
    for a in soup.select('a[href*="programhub.aspx"]'):
        href = a.get("href", "")
        title = a.get_text(strip=True)
        if not title or title.startswith("..."):
            continue
        qs = parse_qs(urlparse(href).query)
        sort = qs.get("sort", [None])[0]
        if sort and sort not in seen:
            seen.add(sort)
            items.append((sort, title))
    print(name, "count", len(items))
    for sort, title in items[:8]:
        print(" ", sort[:20], title[:70])
