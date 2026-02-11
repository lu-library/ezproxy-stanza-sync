import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from .logging_config import logger
from .config import DATA_DIR, OCUL_ALL_URL, BASE_URL
from .send_email import update_email
from .diff_stanza import process_diffs, save_diff_file


# ===== CHECK ALL UPDATES =====
def check_all_updates(CHECK_DATE):
    with open(DATA_DIR / "mapping.json", "r", encoding="utf-8") as f:
        mapping = json.load(f)
    # Titles we care about
    target_titles = set(t.lower() for t in mapping.values())

    if CHECK_DATE:
        check_date = datetime.strptime(CHECK_DATE, "%Y-%m-%d").date()
    else:
        check_date = datetime.today().date()

    print(f"Checking updates since: {check_date}\n")

    resp = requests.get(OCUL_ALL_URL, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

# ==== Build OCUL data dictionary ====
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

# ==== Compare using mapping =====
    logger.info("Starting full EZproxy stanza update check.")
    updated_items = []

    for filename, title in mapping.items():

        if title not in ocul_data:
            continue

        ocul_item = ocul_data[title]
        update_date = ocul_item["date"]

        if update_date >= check_date:
            updated_items.append({
                "filename": filename,
                "title": title,
                "date": str(update_date),
                "link": ocul_item["link"]
            })

    if updated_items:

        diff_results = process_diffs(updated_items) 
        for r in diff_results:
            diff_path = save_diff_file(r["filename"], r["diff"])
            logger.info("Diff saved to {}", diff_path)

        logger.warning("Updated stanzas: {}", len(updated_items))
        for item in updated_items:
            logger.info(
            "File: {} | Title: {} | Date: {}",
            item["filename"],
            item["title"],
            item["date"]
        )
        try:
            update_email(updated_items)
        except Exception:
            logger.warning(
                "Updates found but failed to send email notification",
                exc_info=True
            )
    else:
        logger.info("No updates found.")
        return


if __name__ == "__main__":
    while True:
        CHECK_DATE = input("Press ENTER for current date or input a custom date in YYYY-MM-DD: ").strip()

        try:
            check_all_updates(CHECK_DATE or None)
            break

        except ValueError:
            print("DATE FORMAT ERROR. Please use YYYY-MM-DD.")
            continue

        except Exception:
            logger.exception("Unexpected error occurred while running update_stanza")
            break