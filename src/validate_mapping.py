import requests
from bs4 import BeautifulSoup
import json
from .config import DATA_DIR, OCLC_ALL_URL

with open(DATA_DIR / "mapping.json", "r", encoding="utf-8") as f:
    mapping = json.load(f)

resp = requests.get(OCLC_ALL_URL, timeout=30)
resp.raise_for_status()

soup = BeautifulSoup(resp.text, "html.parser")

oclc_titles = []

# OCLC page: <li><a>Title</a> (date)</li>
for li in soup.find_all("li"):
    a = li.find("a")
    if a:
        title = a.get_text(strip=True)
        if title:
            oclc_titles.append(title)

print(f"Found {len(oclc_titles)} stanza titles on OCLC page.")

oclc_set = set(t for t in oclc_titles)

matched = []
missing = []

for local_file, title in mapping.items():
    if title in oclc_set:
        matched.append((local_file, title))
    else:
        missing.append((local_file, title))

print("\nMatched:", len(matched))
print("Not found:", len(missing))

if missing:
    print("\n---- Potential issues ----")
    for f, t in missing:
        print(f"{f}  -->  {t}")
