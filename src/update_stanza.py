import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from .logging_config import logger
from .config import DATA_DIR, OCLC_ALL_URL, BASE_URL
from .db import get_stanzas
from .diff_stanza import process_diffs, save_diff_file
from .update_config_file import update_config_file
from .organize_config_file import organize_config_file

from collections import Counter
# ===== CHECK ALL UPDATES =====
def check_all_updates(CHECK_DATE):
    """
    with open(DATA_DIR / "mapping.json", "r", encoding="utf-8") as f:
        mapping = json.load(f)
    # Titles we care about
    target_titles = set(t.lower() for t in mapping.values())
    """
    stanzas = get_stanzas("oclc")+ get_stanzas("alumni")

    mapping = {
        row["filename"]: row["title"]
        for row in stanzas
    }

    target_titles = {
        title.lower()
        for title in mapping.values()
    }

    if CHECK_DATE:
        check_date = datetime.strptime(CHECK_DATE, "%Y-%m-%d").date()
    else:
        check_date = datetime.today().date()

    resp = requests.get(OCLC_ALL_URL, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

# ==== Build oclc data dictionary ====
    oclc_data = {}

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
        if not date_part:
            if title == "Coherent Digital Resources":
                date_part = "2025-03-31"
            else:
                date_part = str(check_date)
                if title in mapping.values():
                    logger.warning("Update date missing for {}, set to current date.",title)
        try:
            update_date = datetime.strptime(date_part, "%Y-%m-%d").date()
        except ValueError:
            continue

        if link.startswith("/"):
            link = BASE_URL + link

        oclc_data[title] = {
            "date": update_date,
            "link": link
        }

# ==== Compare using mapping =====
    logger.info("Starting full EZproxy stanza update check.")
    updated_items = []
    
    for filename, title in mapping.items():

        if title not in oclc_data:
            logger.warning("Didn't found matching Stanza page on OCLC website: {}",title)
            continue

        oclc_item = oclc_data[title]
        update_date = oclc_item["date"]

        if update_date >= check_date:
            updated_items.append({
                "filename": filename,
                "title": title,
                "date": str(update_date),
                "link": oclc_item["link"]
            })

    if updated_items:
        try:
            config_path, config_diff_path = update_config_file(updated_items)
            if config_diff_path is not None:
                logger.info("Config updated successfully")
                logger.info("New config: {}", config_path)
                logger.info("Config diff saved to {}", config_diff_path)
        except Exception:
            logger.error("Failed to update config", exc_info=True)

        try:
            config_path, backup_path = organize_config_file()
            if backup_path is not None:
                logger.info("Config organized successfully")
                logger.info("Organized config: {}", config_path)
        except Exception:
            logger.error("Failed to organize config", exc_info=True)
        
        diff_results = process_diffs(updated_items)     
        logger.warning("Stanzas updated after the specified date: {}", len(updated_items))
        """
        for item in updated_items:
            logger.info(
            "File: {} | Title: {} | Date: {}",
            item["filename"],
            item["title"],
            item["date"]
        )
        """
        logger.info("Stanzas updated after the specified date that are NOT YET synced locally: {}", len(diff_results))
        if diff_results:
            for r in diff_results:
                diff_path = save_diff_file(r["filename"], r["diff"])
                logger.info("Diff saved to {}", diff_path)
                r["diff_path"] = diff_path
            """
            try:
                update_email(diff_results)
            except Exception:
                logger.warning(
                    "Updates found but failed to send email notification",
                    exc_info=True
                )
            """
        else:
            logger.info("All stanzas are synced up to date.")
    else:
        logger.info("No updates found.")
        return

def run(check_date: str | None = None):
    if check_date is None:
        # still works from command line without GUI
        while True:
            raw = input("Press ENTER for current date or input a custom date in YYYY-MM-DD: ").strip()
            try:
                check_all_updates(raw or None)
                break
            except ValueError:
                print("DATE FORMAT ERROR. Please use YYYY-MM-DD.")
                continue
            except Exception:
                logger.exception("Unexpected error occurred while running update_stanza")
                break
    else:
        # called from GUI with date already provided
        check_all_updates(check_date)


if __name__ == "__main__":
    run()