import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

OCUL_URL = "https://help.oclc.org/Library_Management/EZproxy/EZproxy_database_stanzas/Database_stanzas/EZproxy_database_stanzas_-_All"

# ====== CONFIG ======

# Set to None to use today's date automatically
CHECK_DATE = None
# Or set manually like "2024-01-01" for testing
#CHECK_DATE = "2024-01-01"

# ====================

with open("mapping.json", "r", encoding="utf-8") as f:
    mapping = json.load(f)

# Titles we care about
target_titles = set(t.lower() for t in mapping.values())

if CHECK_DATE:
    check_date = datetime.strptime(CHECK_DATE, "%Y-%m-%d").date()
else:
    check_date = datetime.today().date()

print(f"Checking updates since: {check_date}\n")

resp = requests.get(OCUL_URL, timeout=30)
resp.raise_for_status()

soup = BeautifulSoup(resp.text, "html.parser")

updated_items = []

BASE_URL = "https://help.oclc.org"

for li in soup.find_all("li"):
    a = li.find("a")
    if not a:
        continue

    title = a.get_text(strip=True)
    link = a.get("href")

    if not title or not link:
        continue

    # Only check stanzas we use
    if title.lower() not in target_titles:
        continue

    # Get date text from li (after <a>)
    full_text = li.get_text(" ", strip=True)

    # Example: "University of Chicago Press (2022-08-10)"
    if "(" not in full_text:
        continue

    date_part = full_text.split("(")[-1].replace(")", "").strip()

    try:
        update_date = datetime.strptime(date_part, "%Y-%m-%d").date()
    except ValueError:
        continue

    if update_date >= check_date:
        if link.startswith("/"):
            link = BASE_URL + link

        updated_items.append({
            "title": title,
            "date": str(update_date),
            "link": link
        })

# ===== OUTPUT =====

if not updated_items:
    print("No updates found.")
else:
    print("Updated stanzas:\n")
    for item in updated_items:
        print(f"{item['title']}")
        print(f"  Date: {item['date']}")
        print(f"  Link: {item['link']}\n")
