import requests
from bs4 import BeautifulSoup
from datetime import datetime
from .config import OCLC_MOST_RECENT_URL, BASE_URL
from .db import get_title_to_filename


def check_most_recent_updates(CHECK_DATE):
    title_to_file = get_title_to_filename()
    target_titles = set(title_to_file.keys())

    if CHECK_DATE:
        check_date = datetime.strptime(CHECK_DATE, "%Y-%m-%d").date()
    else:
        check_date = datetime.today().date()

    resp = requests.get(OCLC_MOST_RECENT_URL, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    target_h3 = None
    for h3 in soup.find_all("h3"):
        if "Recently updated database stanzas" in h3.get_text():
            target_h3 = h3
            break

    if not target_h3:
        print("Could not find recent updates section.")
        exit()

    table = target_h3.find_next("table")

    if not table:
        print("No table found after recent updates header.")
        exit()

    updated_items = []

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

            filename = title_to_file[title.lower()]
            updated_items.append({
                "filename": filename,
                "title": title,
                "date": str(update_date),
                "link": link,
            })

    return updated_items
