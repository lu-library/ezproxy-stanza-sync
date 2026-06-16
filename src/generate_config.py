"""
Generate config.txt by rendering Jinja2 templates with data parsed from config.txt.
"""
from datetime import datetime, date
from pathlib import Path
import difflib
from typing import TypedDict
from jinja2 import Environment, FileSystemLoader

from .config import CONFIG_FILE, CONFIG_DIR, DATA_DIR
from .logging_config import logger


class StanzaEntry(TypedDict):
    title: str
    date: str
    filename: str
    note: str

TEMPLATES_DIR = CONFIG_DIR / "templates"


def render_config(output_path: Path | None = None, create_backup: bool = True) -> str:
    """
    Read data from SQLite DB, render Jinja2 templates, and return the result.
    If output_path is given, write the rendered config there.
    If create_backup is True, backup the existing config before overwriting.
    """
    from .db import get_stanzas
    
    alumni_entries = get_stanzas("alumni")
    oclc_entries = get_stanzas("oclc")
    custom_entries = get_stanzas("custom")
    
    
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    context = {
        "generated_date": date.today().isoformat(),
        "generated_time": datetime.now().time().isoformat(),
        "alumni_entries": alumni_entries,
        "oclc_entries": oclc_entries,
        "custom_entries": custom_entries,
    }

    header = env.get_template("header.tpl").render(**context)
    alumni = env.get_template("alumni.tpl").render(**context)
    config_body = env.get_template("config.tpl").render(**context)
    footer = env.get_template("footer.tpl").render(**context)

    rendered = "\n".join([header, alumni, config_body, "", footer])
    config_path = CONFIG_FILE

    old_text = config_path.read_text(encoding="utf-8")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    diff = difflib.unified_diff(
                old_text.splitlines(),
                rendered.splitlines(),
                fromfile="config_old",
                tofile="config_new",
                lineterm="",
            )
    diff_text = "\n".join(diff)
    if diff_text:
        config_path.write_text(rendered, encoding="utf-8")
        logger.info("Config written to {}", config_path)
        diff_path = DATA_DIR / "diff/config" / f"{timestamp}_config.diff"
        diff_path.parent.mkdir(exist_ok=True)
        diff_path.write_text(diff_text, encoding="utf-8")
        logger.info("Diff written to {}", diff_path)

        if output_path.exists():
            # backup
            if create_backup and diff_text:

                backup_path = config_path.with_name(f"config.update.{timestamp}.txt")

                backup_path.write_text(old_text, encoding="utf-8")
                logger.info("Backup written to {}", backup_path)

    else:
        logger.info("No update in config.txt")
        

    return rendered


def run():
    result = render_config(output_path=CONFIG_FILE)