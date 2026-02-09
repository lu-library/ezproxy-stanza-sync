import requests
from bs4 import BeautifulSoup
import json
from .config import DATA_DIR, OCUL_ALL_URL

with open(DATA_DIR / "mapping.json", "r", encoding="utf-8") as f:
    mapping = json.load(f)

resp = requests.get(OCUL_ALL_URL, timeout=30)
resp.raise_for_status()

soup = BeautifulSoup(resp.text, "html.parser")

ocul_titles = []

# OCUL page: <li><a>Title</a> (date)</li>
for li in soup.find_all("li"):
    a = li.find("a")
    if a:
        title = a.get_text(strip=True)
        if title:
            ocul_titles.append(title)

print(f"Found {len(ocul_titles)} stanza titles on OCUL page.")

ocul_set = set(t.lower() for t in ocul_titles)

matched = []
missing = []

for local_file, title in mapping.items():
    if title.lower() in ocul_set:
        matched.append((local_file, title))
    else:
        missing.append((local_file, title))

print("\nMatched:", len(matched))
print("Not found:", len(missing))

if missing:
    print("\n---- Potential issues ----")
    for f, t in missing:
        print(f"{f}  -->  {t}")
