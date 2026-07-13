from curl_cffi import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs

BASE = "https://www.pathwaystoscience.org/"
u = "programs.aspx?u=&r=&s=HighSchool&sa=either&p=either&o=either&c=either&f=&dd=&ft=&submit=y&adv=adv&page=2"
r = requests.get(BASE + u, impersonate="chrome131", timeout=30)
soup = BeautifulSoup(r.text, "lxml")
seen = set()
for a in soup.select("a[href*='programhub.aspx']"):
    href = a.get("href", "")
    qs = parse_qs(urlparse(href).query)
    sort = qs.get("sort", [None])[0]
    if sort:
        seen.add(sort)
print("page2 count", len(seen))
# pagination links
for a in soup.select("a[href]"):
    t = a.get_text(strip=True)
    if t.isdigit() or "next" in t.lower() or "page" in t.lower():
        print("pag", a.get("href"), t)
