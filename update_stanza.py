import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

OCUL_URL = "https://help.oclc.org/Library_Management/EZproxy/EZproxy_database_stanzas/Database_stanzas/EZproxy_database_stanzas_-_All"
BASE_URL = "https://help.oclc.org"

# ====== CONFIG ======

# Set to None to use today's date automatically
CHECK_DATE = None
# Or set manually like "2024-01-01" for testing
#CHECK_DATE = "2024-01-01"

# ====================

with open("mapping.json", "r", encoding="utf-8") as f:
    mapping = json.load(f)


if CHECK_DATE:
    check_date = datetime.strptime(CHECK_DATE, "%Y-%m-%d").date()
else:
    check_date = datetime.today().date()

print(f"Checking updates since: {check_date}\n")

resp = requests.get(OCUL_URL, timeout=30)
resp.raise_for_status()

soup = BeautifulSoup(resp.text, "html.parser")

# =========================
# Build OCUL data dictionary
# =========================

ocul_data = {}

for li in soup.find_all("li"):
    a = li.find("a")
    if not a:
        continue

    title = a.get_text(strip=True)
    link = a.get("href")

    if not title or not link:
        continue

    full_text = li.get_text(" ", strip=True)

    if "(" not in full_text:
        continue

    date_part = full_text.split("(")[-1].replace(")", "").strip()

    try:
        update_date = datetime.strptime(date_part, "%Y-%m-%d").date()
    except ValueError:
        continue

    if link.startswith("/"):
        link = BASE_URL + link

    ocul_data[title] = {
        "date": update_date,
        "link": link
    }

# =========================
# Compare using mapping
# =========================

updated_items = []
updated_amount = 0

for filename, title in mapping.items():

    if title not in ocul_data:
        continue

    ocul_item = ocul_data[title]
    update_date = ocul_item["date"]

    if update_date >= check_date:
        updated_amount+=1
        updated_items.append({
            "filename": filename,
            "title": title,
            "date": str(update_date),
            "link": ocul_item["link"]
        })

# ===== OUTPUT =====

if not updated_items:
    print("No updates found.")
else:
    print("Updated stanzas:",updated_amount,"\n")
    for item in updated_items:
        print(f"File: {item['filename']}")
        print(f"Title: {item['title']}")
        print(f"Date: {item['date']}")
        print(f"Link: {item['link']}\n")
