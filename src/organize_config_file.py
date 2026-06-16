from pathlib import Path
from datetime import datetime
from .config import CONFIG_FILE
from .db import get_stanzas
from .logging_config import logger


def _filename_from_line(line: str) -> str:
    return Path(line.split()[-1]).name.lower()


def _parse_entries(lines: list[str]) -> list[tuple[str, str]]:
    """Extract (comment, includefile) pairs from a block of lines."""
    entries = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#") and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line.startswith("IncludeFile"):
                entries.append((lines[i], lines[i + 1]))
                i += 2
                continue
        i += 1
    return entries


def _sort_block_from_db(block_lines: list[str], section: str) -> list[str]:
    """
    Sort IncludeFile entries in a block using DB-ordered filenames.
    Entries not in the DB fall back to alphabetical order at the end.
    """
    db_rows = get_stanzas(section)
    db_order = {row["filename"].lower(): idx for idx, row in enumerate(db_rows)}

    entries = _parse_entries(block_lines)
    logger.info("Found {} entries in {} block", len(entries), section)

    entries.sort(key=lambda e: (
        db_order.get(_filename_from_line(e[1]), len(db_order)),
        _filename_from_line(e[1]),
    ))

    result = []
    for comment, include in entries:
        result.append(comment)
        result.append(include)
        result.append("")
    return result


def _process_section(lines: list[str], start_marker: str, end_marker: str, section: str) -> list[str]:
    if start_marker not in lines or end_marker not in lines:
        logger.warning("Marker not found: {}", start_marker)
        return lines

    start_idx = lines.index(start_marker) + 1
    end_idx = lines.index(end_marker)
    block = lines[start_idx:end_idx]

    logger.info("Processing section: {}", start_marker)
    sorted_block = _sort_block_from_db(block, section)

    return lines[:start_idx] + sorted_block + lines[end_idx:]


def _normalize(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines() if line.strip() != "" or True)


def organize_config_file():
    config_path = CONFIG_FILE
    logger.info("Starting config sort: {}", config_path)

    old_text = config_path.read_text(encoding="utf-8")
    lines = old_text.splitlines()

    lines = _process_section(
        lines,
        "#------------ Start of IncludeFile - Custom Stanzas ------------#",
        "#------------ End of IncludeFile - Custom Stanzas ------------#",
        "custom",
    )
    lines = _process_section(
        lines,
        "#------------ Start of IncludeFile - OCLC ------------#",
        "#------------ End of IncludeFile - OCLC ------------#",
        "oclc",
    )

    new_text = "\n".join(lines) + "\n"

    if _normalize(old_text) == _normalize(new_text):
        logger.info("No changes detected. Config file remains unchanged.")
        return config_path, None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = config_path.with_name(f"config.organize.{timestamp}.beforeorganization.txt")

    backup_path.write_text(old_text, encoding="utf-8")
    logger.info("Backup created: {}", backup_path)

    config_path.write_text(new_text, encoding="utf-8")
    logger.warning("Config file updated successfully")

    return config_path, backup_path
