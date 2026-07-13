from curl_cffi import requests
from bs4 import BeautifulSoup
import re

BASE = "https://www.pathwaystoscience.org/"
u = "programs.aspx?submit=y&link=deadlineapproaching"
r = requests.get(BASE + u, impersonate="chrome131", timeout=30)
open("debug_results.html", "w", encoding="utf-8").write(r.text)
soup = BeautifulSoup(r.text, "lxml")
for a in soup.select("a[href]"):
    href = a.get("href", "")
    text = a.get_text(strip=True)[:80]
    if text and "program" in href.lower():
        print(href, "|", text)
print("---tables---")
for table in soup.select("table"):
    print("table", table.get("id"), table.get("class"))
    rows = table.select("tr")
    print(" rows", len(rows))
    for row in rows[:5]:
        print("  ", row.get_text(" | ", strip=True)[:120])
