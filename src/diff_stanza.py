import requests
import traceback
from bs4 import BeautifulSoup
from loguru import logger
from urllib.parse import urljoin
from pathlib import Path
import difflib
from datetime import datetime
from .config import DIFF_DIR, DATA_DIR
from .send_email import error_email

class StanzaNotFoundError(RuntimeError):
    pass

def fetch_stanza_text(stanza_url: str) -> str:
    """
    Fetch stanza text from OCUL.
    Supports:
    1. <pre>...</pre> embedded content
    2. External .txt link inside <div class="highlight-box">
    """
    resp = requests.get(stanza_url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # ---- Case 1: external link inside highlight-box ----
    for box in soup.select("div[class*='highlight-box']"):
        a = box.find("a", href=True)
        if not a:
            continue
        href = a["href"]
        link_text = a.get_text(strip=True).lower()
        if ".txt" in href or link_text.endswith(".txt"):
            txt_url = urljoin(stanza_url, href)
            #logger.info("Fetching external stanza file: {}", txt_url)
            txt_resp = requests.get(txt_url, timeout=30)
            txt_resp.raise_for_status()
            return txt_resp.text.strip()

    # ---- Case 2: embedded <pre> (if no external link) ----
    pre = soup.find("pre")
    if pre:
        #logger.info("Using embedded <pre> stanza")
        return pre.get_text().strip()

    raise StanzaNotFoundError(f"Could not locate stanza text on OCUL page: {stanza_url}")


def load_local_stanza(file_path: Path) -> str:
    if not file_path.exists():
        raise FileNotFoundError(f"Local stanza not found: {file_path}")
    return file_path.read_text(encoding="utf-8").strip()


def diff_stanza(local_text: str, remote_text: str) -> str:
    """
    Return unified diff between local and remote stanza text
    """
    local_lines = local_text.splitlines()
    remote_lines = remote_text.splitlines()

    diff = difflib.unified_diff(
        local_lines,
        remote_lines,
        fromfile="local",
        tofile="ocul",
        lineterm=""
    )

    return "\n".join(diff)


def process_diffs(updated_items):
    results = []

    for item in updated_items:
        try:
            local_path = DATA_DIR / "stanzas" / item["filename"]

            remote_text = fetch_stanza_text(item["link"])
            local_text = load_local_stanza(local_path)
            diff_text = diff_stanza(local_text, remote_text)

            results.append({
                **item,
                "diff": diff_text
            })
    
        except StanzaNotFoundError:
            logger.error(
                "Stanza text not found for {}. OCUL page: {}",
                item["filename"],
                item["link"],
                exc_info=True
            )
            continue

        except Exception as e:
            tb = traceback.format_exc()
            print(tb,"\n\n\n")
            logger.error(
                "Failed to process diff for {}. Access details at {}.\n Error {}",
                item["filename"],
                item["link"],
                tb
            )
            continue

    return results


def save_diff_file(filename, diff_text):
    DIFF_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = filename.replace("/", "_")

    diff_filename = f"{timestamp}_{safe_name}.diff"
    diff_path = DIFF_DIR / diff_filename

    content = (
    f"# Filename: {filename}\n"
    f"# Generated at: {timestamp}\n\n"
    + diff_text
)

    diff_path.write_text(content, encoding="utf-8")

    return diff_path