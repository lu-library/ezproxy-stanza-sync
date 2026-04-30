import time
import sys
import traceback
from pathlib import Path
from .logging_config import logger
from .most_recent_update_stanza import check_most_recent_updates
from .update_config_file import update_config_file
from .send_email import update_email, error_email
from .diff_stanza import process_diffs, save_diff_file

# ====== CONFIG ======
MAX_RETRIES = 3
RETRY_DELAY = 3600  # 1 hour
# Set to None to use today's date automatically
CHECK_DATE = None
# Or set manually in "YYYY-MM-DD" for testing
# CHECK_DATE = "2026-04-16"

# ====================

    
def execute_sync():
    updated_items = check_most_recent_updates(CHECK_DATE)

    if updated_items:
        try:
            config_path, config_diff_path = update_config_file(updated_items)
            if config_diff_path is not None:
                logger.info("Config updated successfully")
                logger.info("New config: {}", config_path)
                logger.info("Config diff saved to {}", config_diff_path)
        except Exception:
            logger.error("Failed to update config", exc_info=True)

        diff_results = process_diffs(updated_items)
            
        logger.warning("Stanzas updated after the specified date: {}", len(updated_items))
        for item in updated_items:
            logger.info(f"File: {item['filename']}")
            logger.info(f"Title: {item['title']}")
            logger.info(f"Date: {item['date']}")
            logger.info(f"Link: {item['link']}\n")

        logger.warning("Stanzas updated after the specified date that are NOT YET synced locally: {}", len(diff_results))
        if diff_results:
            for r in diff_results:
                diff_path = save_diff_file(r["filename"], r["diff"])
                logger.warning("Diff detected for {}", r["filename"])
                logger.info("Diff saved to {}", diff_path)
                r["diff_path"] = diff_path
            try:
                update_email(diff_results)
            except Exception:
                logger.warning(
                    "Updates found but failed to send email notification",
                    exc_info=True
                )
        else:
            logger.info("All stanzas are synced up to date.")
    else:
        logger.info("No updates found.")


def run():
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info("Run attempt {}/{}", attempt, MAX_RETRIES)
            execute_sync()
            logger.info("Sync finished successfully")
            return
        except Exception as e:
            tb = traceback.format_exc()
            logger.exception("Attempt {} failed", attempt)

            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                logger.error("Sending error email with traceback:\n%s", tb)
                error_email(tb)
                sys.exit(1)


if __name__ == "__main__":
    run()
