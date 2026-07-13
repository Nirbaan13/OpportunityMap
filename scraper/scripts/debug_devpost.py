from curl_cffi import requests
import json
import re

# Try common Devpost API patterns
session = requests.Session()
headers = {"Accept": "application/json"}
candidates = [
    "https://devpost.com/api/hackathons?challenge_type[]=online&themes[]=Beginner%20Friendly&status[]=open",
    "https://devpost.com/api/hackathons",
    "https://devpost.com/hackathons.json",
    "https://devpost.com/hackathons?challenge_type[]=online&themes[]=Beginner%20Friendly&status[]=open&page=1",
]
for u in candidates:
    try:
        r = session.get(u, impersonate="chrome131", timeout=30, headers=headers)
        print(u, r.status_code, r.headers.get("content-type", "")[:40], len(r.text))
        if "json" in r.headers.get("content-type", ""):
            print(r.text[:500])
    except Exception as e:
        print(u, "ERR", e)

html = open("devpost_test.html", encoding="utf-8").read()
for pat in [r"window\.__[^=]+=\s*(\{.+?\});", r"data-page=\"([^\"]+)\"", r"/api/[^\"']+"]:
    m = re.search(pat, html[:50000])
    if m:
        print("match", pat, str(m.group(0))[:120])

# look for inertia/vue payload
for key in ["hackathons", "challenges", "props", "pageProps"]:
    if key in html:
        print("found key", key)
