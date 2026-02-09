import time
import sys
import traceback
from pathlib import Path
from .logging_config import logger
from .most_recent_update_stanza import check_most_recent_updates
from .send_email import update_email, error_email

# ====== CONFIG ======
MAX_RETRIES = 3
RETRY_DELAY = 3600  # 1 hour
# Set to None to use today's date automatically
CHECK_DATE = None
# Or set manually like "2024-01-01" for testing
CHECK_DATE = "2025-01-01"

# ====================

def run_job():
    updated_items = check_most_recent_updates(CHECK_DATE)

    if updated_items:
        logger.warning("Updated stanzas: {}", len(updated_items))
        for item in updated_items:
            logger.info(f"File: {item['filename']}")
            logger.info(f"Title: {item['title']}")
            logger.info(f"Date: {item['date']}")
            logger.info(f"Link: {item['link']}\n")
        try:
            update_email(updated_items)
        except Exception:
            logger.warning(
                "Updates found but failed to send email notification",
                exc_info=True
            )
    else:
        logger.info("No updates found.")


def main():
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info("Run attempt {}/{}", attempt, MAX_RETRIES)
            run_job()
            logger.info("Job finished successfully")
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
    main()
