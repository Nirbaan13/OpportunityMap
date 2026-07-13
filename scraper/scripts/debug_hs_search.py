from curl_cffi import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs

BASE = "https://www.pathwaystoscience.org/"

# High school advanced search
u = "programs.aspx?u=&r=&s=HighSchool&sa=either&p=either&o=either&c=either&f=&dd=&ft=&submit=y&adv=adv"
r = requests.get(BASE + u, impersonate="chrome131", timeout=30)
soup = BeautifulSoup(r.text, "lxml")
items = []
seen = set()
for a in soup.select("a[href*='programhub.aspx']"):
    href = a.get("href", "")
    if "read more" in a.get_text(strip=True).lower():
        continue
    qs = parse_qs(urlparse(href).query)
    sort = qs.get("sort", [None])[0]
    if not sort or sort in seen:
        continue
    title = a.get_text(strip=True)
    if not title or title.startswith("..."):
        continue
    seen.add(sort)
    items.append((sort, title, urljoin(BASE, href)))
print("high school programs", len(items))
for sort, title, url in items[:15]:
    print(sort, "|", title[:70])
