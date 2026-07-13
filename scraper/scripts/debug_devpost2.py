from curl_cffi import requests
import json

API = "https://devpost.com/api/hackathons"
params = {
    "challenge_type[]": "online",
    "themes[]": "Beginner Friendly",
    "status[]": "open",
}
r = requests.get(API, params=params, impersonate="chrome131", timeout=30, headers={"Accept": "application/json"})
data = r.json()
print("count", len(data.get("hackathons", [])))
if data.get("hackathons"):
    print(json.dumps(data["hackathons"][0], indent=2)[:2000])

# detail page
url = data["hackathons"][0]["url"]
r2 = requests.get(url, impersonate="chrome131", timeout=30)
print("detail", url, r2.status_code, len(r2.text))
open("devpost_detail.html", "w", encoding="utf-8").write(r2.text[:150000])

# pagination?
for page in [1, 2]:
    p = {**params, "page": page}
    r3 = requests.get(API, params=p, impersonate="chrome131", timeout=30, headers={"Accept": "application/json"})
    print("page", page, r3.status_code, len(r3.json().get("hackathons", [])))
