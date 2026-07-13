from curl_cffi import requests
from bs4 import BeautifulSoup

BASE = "https://www.pathwaystoscience.org/"
u = "programhub.aspx?sort=PDC-NationalAcademies-AirForceFell"
r = requests.get(BASE + u, impersonate="chrome131", timeout=30)
open("debug_detail.html", "w", encoding="utf-8").write(r.text)
soup = BeautifulSoup(r.text, "lxml")
print("title", soup.title.get_text(strip=True) if soup.title else None)
for tag in ["h1", "h2", "h3"]:
    for el in soup.select(tag):
        print(tag, el.get_text(strip=True)[:100])
print("---labels---")
text = soup.get_text("\n", strip=True)
for line in text.split("\n"):
    if any(k in line.lower() for k in ["deadline", "grade", "eligib", "high school", "location", "country", "apply"]):
        print(line[:120])
