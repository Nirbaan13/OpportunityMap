from curl_cffi import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs

BASE = "https://www.pathwaystoscience.org/"
base_q = "programs.aspx?u=&r=&s=HighSchool&sa=either&p=either&o=either&c=either&f=&dd=&ft=&submit=y&adv=adv"

for suffix in ["", "&pg=2", "&page=2", "&pageno=2", "&start=25"]:
    u = base_q + suffix
    r = requests.get(BASE + u, impersonate="chrome131", timeout=30)
    soup = BeautifulSoup(r.text, "lxml")
    seen = set()
    for a in soup.select("a[href*='programhub.aspx']"):
        qs = parse_qs(urlparse(a.get("href", "")).query)
        sort = qs.get("sort", [None])[0]
        if sort:
            seen.add(sort)
    print(suffix or "(page1)", "count", len(seen), "first", list(seen)[:1])
