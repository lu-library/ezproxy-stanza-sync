from pathlib import Path
from datetime import datetime
from .logging_config import logger

from .config import CONFIG_FILE, CONFIG_DIR


def extract_filename(line: str) -> str:
    """Extract filename from IncludeFile line"""
    return Path(line.split()[-1]).name.lower()


def parse_entries(lines):
    """
    Convert lines into entry blocks:
    Each entry = (comment, includefile)
    """
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


def sort_block(block_lines):
    """Sort entries inside a block"""
    entries = parse_entries(block_lines)

    logger.info("Found {} entries in block", len(entries))

    entries.sort(key=lambda e: extract_filename(e[1]))

    sorted_lines = []
    for comment, include in entries:
        sorted_lines.append(comment)
        sorted_lines.append(include)
        sorted_lines.append("")  # keep blank line

    return sorted_lines


def process_section(lines, start_marker, end_marker):
    """Sort a specific section"""
    if start_marker not in lines or end_marker not in lines:
        logger.warning("Marker not found: {}", start_marker)
        return lines

    start_idx = lines.index(start_marker) + 1
    end_idx = lines.index(end_marker)

    block = lines[start_idx:end_idx]

    logger.info("Processing section: {}", start_marker)

    sorted_block = sort_block(block)

    return lines[:start_idx] + sorted_block + lines[end_idx:]



def normalize(text: str) -> str:
    return "\n".join(
        line.rstrip() for line in text.splitlines()
        if line.strip() != "" or True
    )


def organize_config_file():
    config_path = CONFIG_FILE

    logger.info("Starting config sort: {}", config_path)

    old_text = config_path.read_text(encoding="utf-8")
    lines = old_text.splitlines()

    # ---- Section 1: Custom IncludeFile ----
    lines = process_section(
        lines,
        "#------------ Start of IncludeFile - Custom Stanzas ------------#",
        "#------------ End of IncludeFile - Custom Stanzas ------------#"
    )

    # ---- Section 2: OCLC IncludeFile ----
    lines = process_section(
        lines,
        "#------------ Start of IncludeFile - OCLC ------------#",
        "#------------ End of IncludeFile - OCLC ------------#"
    )

    new_text = "\n".join(lines) + "\n"
    
    if normalize(old_text) == normalize(new_text):
        logger.info("No changes detected. Config file remains unchanged.")
        return config_path, None

    # ===== backup =====
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = config_path.with_name(f"config.organize.{timestamp}.beforeorganization.txt")

    backup_path.write_text(old_text, encoding="utf-8")
    logger.info("Backup created: {}", backup_path)

    config_path.write_text(new_text, encoding="utf-8")
    logger.warning("Config file updated successfully")

    return config_path, backup_path