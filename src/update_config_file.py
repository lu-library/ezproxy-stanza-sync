from datetime import datetime
from pathlib import Path
import difflib
from .config import CONFIG_FILE, CONFIG_DIR, DATA_DIR
from .logging_config import logger

def extract_filename(line: str) -> str:
    # IncludeFile databases/xxx.txt → xxx.txt
    return Path(line.split()[-1]).name



def normalize(text: str) -> str:
    return "\n".join(
        line.rstrip() for line in text.splitlines()
        if line.strip() != "" or True
    )



def update_config_file(updated_items):
    updated_map = {item["filename"]: item for item in updated_items}

    config_path = CONFIG_FILE

    old_text = config_path.read_text(encoding="utf-8")
    lines = old_text.splitlines()
    new_lines = []

    for line in lines:
        if line.strip().startswith("IncludeFile"):
            filename = extract_filename(line)

            if filename in updated_map:
                item = updated_map[filename]

                if new_lines:
                    prev_line = new_lines[-1]

                    if "last update" in prev_line.lower():
                        new_lines[-1] = f"# {item['title']} - last update {item['date']}"

        new_lines.append(line)

    new_text = "\n".join(new_lines)

    if normalize(old_text) == normalize(new_text):
        logger.info("No changes detected. Config file remains unchanged.")
        return config_path, None

    # ===== backup =====
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = config_path.with_name(f"config.update.{timestamp}.txt")

    backup_path.write_text(old_text, encoding="utf-8")
    config_path.write_text(new_text, encoding="utf-8")

    diff = difflib.unified_diff(
        old_text.splitlines(),
        new_text.splitlines(),
        fromfile="config_old",
        tofile="config_new",
        lineterm=""
    )

    diff_text = "\n".join(diff)

    diff_path = DATA_DIR / "diff/config" / f"{timestamp}_config.diff"
    diff_path.parent.mkdir(exist_ok=True)
    diff_path.write_text(diff_text, encoding="utf-8")

    return config_path, diff_path