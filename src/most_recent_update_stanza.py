import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from .config import DATA_DIR, OCUL_MOST_RECENT_URL, BASE_URL


# ===== CHECK MOST RECENT UPDATES =====
def check_most_recent_updates(CHECK_DATE):
    with open(DATA_DIR / "mapping.json", "r", encoding="utf-8") as f:
        mapping = json.load(f)
    # Titles we care about
    target_titles = set(t.lower() for t in mapping.values())

    if CHECK_DATE:
        check_date = datetime.strptime(CHECK_DATE, "%Y-%m-%d").date()
    else:
        check_date = datetime.today().date()

    resp = requests.get(OCUL_MOST_RECENT_URL, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
# === Compare using mapping ===
    updated_items = []
    title_to_file = {v.lower(): k for k, v in mapping.items()}

# === Find the correct section by h3 title ===
    target_h3 = None
    for h3 in soup.find_all("h3"):
        if "Recently updated database stanzas" in h3.get_text():
            target_h3 = h3
            break

    if not target_h3:
        print("Could not find recent updates section.")
        exit()

# The table should follow the h3
    table = target_h3.find_next("table")

    if not table:
        print("No table found after recent updates header.")
        exit()

# === Parse table rows ===
    for row in table.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) < 2:
            continue

        a = cols[0].find("a")
        if not a:
            continue

        title = a.get_text(strip=True)
        link = a.get("href")
        date_text = cols[1].get_text(strip=True)

        if title.lower() not in target_titles:
            continue

        try:
            update_date = datetime.strptime(date_text, "%Y-%m-%d").date()
        except ValueError:
            continue

        if update_date >= check_date:
            if link.startswith("/"):
                link = BASE_URL + link

            filename = title_to_file.get(title.lower(), "UNKNOWN")
            updated_items.append({
                "filename": filename,
                "title": title,
                "date": str(update_date),
                "link": link
            })

    return updated_items