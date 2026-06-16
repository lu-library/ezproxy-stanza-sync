import sqlite3
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from .config import DATA_DIR, CONFIG_FILE
from .generate_config import StanzaEntry
from .logging_config import logger

DB_PATH = DATA_DIR / "stanzas.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS stanzas (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    section       TEXT    NOT NULL CHECK(section IN ('alumni', 'oclc', 'custom')),
    filename      TEXT    NOT NULL,
    title         TEXT    NOT NULL,
    note          TEXT    NOT NULL DEFAULT '',
    date_updated  TEXT,
    date_synced   TEXT    NOT NULL,
    UNIQUE(section, filename)
);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(_SCHEMA)
    return conn


def upsert_stanzas(section: str, entries: Sequence[StanzaEntry]) -> int:
    """Insert or update entries for a section. Returns number of rows affected."""
    now = datetime.now().isoformat(timespec="seconds")
    rows = [
        (section, e["filename"], e["title"], e.get("note", ""), e.get("date") or None, now)
        for e in entries
    ]
    with _connect() as conn:
        conn.executemany(
            """
            INSERT INTO stanzas (section, filename, title, note, date_updated, date_synced)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(section, filename) DO UPDATE SET
                title        = excluded.title,
                note         = excluded.note,
                date_updated = excluded.date_updated,
                date_synced  = excluded.date_synced
            """,
            rows,
        )
    logger.info("Upserted {} {} entries into DB", len(rows), section)
    return len(rows)



def get_stanzas(section: str | None = None) -> list[sqlite3.Row]:
    #Return all rows, optionally filtered by section.
    with _connect() as conn:
        if section:
            return conn.execute(
                "SELECT * FROM stanzas WHERE section = ? ORDER BY filename", (section,)
            ).fetchall()
        return conn.execute("SELECT * FROM stanzas ORDER BY section, filename").fetchall()



def get_stanza(filename: str) -> sqlite3.Row | None:
    """Return a single row by filename (searches all sections)."""
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM stanzas WHERE filename = ?", (filename,)
        ).fetchone()


def update_date(filename: str, date_updated: str) -> int:
    """Update date_updated and date_synced for all rows matching filename. Returns rows affected."""
    now = datetime.now().isoformat(timespec="seconds")
    with _connect() as conn:
        cur = conn.execute(
            "UPDATE stanzas SET date_updated = ?, date_synced = ? WHERE filename = ?",
            (date_updated, now, filename),
        )
    return cur.rowcount


def get_tracked_filenames() -> set[str]:
    """Return the set of all filenames tracked in the DB (any section)."""
    with _connect() as conn:
        rows = conn.execute("SELECT filename FROM stanzas").fetchall()
    return {row["filename"] for row in rows}


def get_title_to_filename() -> dict[str, str]:
    """Return a mapping of lowercase title → filename for all tracked stanzas (deduplicated by title)."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT title, filename FROM stanzas GROUP BY title"
        ).fetchall()
    return {row["title"].lower(): row["filename"] for row in rows}


def _parse_alumni_block(lines: list[str]) -> list[StanzaEntry]:
    """
    Extract IncludeFile entries from the alumni group block.

    Alumni entries use a two-comment format:
        # Alumni N
        # Title - last update YYYY-MM-DD
        IncludeFile stanzas/filename.txt
    """
    start_marker = "#------------ Satrt of Group ALUMNI ------------#"
    end_marker = "#------------ End of Group ALUMNI ------------#"
    try:
        start = lines.index(start_marker) + 1
        end = lines.index(end_marker)
    except ValueError:
        logger.warning("Alumni markers not found")
        return []

    entries = []
    i = start
    while i < end:
        line = lines[i].strip()
        # Skip "# Alumni N" label lines
        if line.startswith("# Alumni"):
            i += 1
            continue
        if line.startswith("#") and i + 1 < end:
            next_line = lines[i + 1].strip()
            if next_line.startswith("IncludeFile"):
                comment = line.lstrip("#").strip()
                filename = Path(next_line.split()[-1]).name
                title, update_date, note = _parse_comment(comment)
                entries.append({"title": title, "date": update_date, "filename": filename, "note": note})
                i += 2
                continue
        i += 1
    return entries


def _parse_includefile_block(lines: list[str], start_marker: str, end_marker: str) -> list[StanzaEntry]:
    """
    Extract IncludeFile entries from a delimited block.

    Returns a list of dicts with keys: title, date, filename, note.
    Each entry is expected as:
        # Title - last update YYYY-MM-DD [- note]
        IncludeFile stanzas/filename.txt
    """
    try:
        start = lines.index(start_marker) + 1
        end = lines.index(end_marker)
    except ValueError:
        logger.warning("Marker not found: {}", start_marker)
        return []

    entries = []
    i = start
    while i < end:
        line = lines[i].strip()
        if line.startswith("#") and i + 1 < end:
            next_line = lines[i + 1].strip()
            if next_line.startswith("IncludeFile"):
                comment = line.lstrip("#").strip()
                filename = Path(next_line.split()[-1]).name
                title, update_date, note = _parse_comment(comment)
                entries.append({"title": title, "date": update_date, "filename": filename, "note": note})
                i += 2
                continue
        i += 1
    return entries


def _parse_comment(comment: str) -> tuple[str, str, str]:
    """
    Parse '# Title - last update YYYY-MM-DD [- note]' into (title, date, note).
    Returns ("", "", "") components that are missing.
    """
    import re
    if " - last update " in comment:
        title_part, rest = comment.split(" - last update ", 1)
        # Date is always a YYYY-MM-DD at the start; note is anything after
        m = re.match(r"(\d{4}-\d{2}-\d{2})\s*-?\s*(.*)", rest)
        if m:
            update_date = m.group(1)
            note = m.group(2).strip().lstrip("-").strip()
        else:
            update_date = rest.strip()
            note = ""
        return title_part.strip(), update_date, note
    return comment.strip(), "", ""



STATIC_STANZAS_MARKER_START = "#------------ Start of Custom Stanzas ------------#"
STATIC_STANZAS_MARKER_END = "#------------ End of Custom Stanzas ------------#"

def _extract_static_stanzas(lines: list[str]) -> str:
    """Return the verbatim inline custom stanzas block, including its markers."""
    try:
        start = lines.index(STATIC_STANZAS_MARKER_START)
        end = lines.index(STATIC_STANZAS_MARKER_END) + 1
    except ValueError:
        logger.warning("Static stanzas markers not found")
        return ""
    return "\n".join(lines[start:end])


def load_db():
    """Parse config.txt and upsert all IncludeFile entries into the SQLite DB."""

    raw = CONFIG_FILE.read_text(encoding="utf-8")
    lines = raw.splitlines()

    alumni_entries = _parse_alumni_block(lines)
    oclc_entries = _parse_includefile_block(
        lines,
        "#------------ Start of IncludeFile - OCLC ------------#",
        "#------------ End of IncludeFile - OCLC ------------#",
    )
    custom_entries = _parse_includefile_block(
        lines,
        "#------------ Start of IncludeFile - Custom Stanzas ------------#",
        "#------------ End of IncludeFile - Custom Stanzas ------------#",
    )

    upsert_stanzas("alumni", alumni_entries)
    upsert_stanzas("oclc", oclc_entries)
    upsert_stanzas("custom", custom_entries)


def check():
    stanzas_dir = DATA_DIR / "stanzas"
    raw = CONFIG_FILE.read_text(encoding="utf-8")
    lines = raw.splitlines()

    include_lines: dict[str, int] = {}
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("IncludeFile"):
            parts = stripped.split()
            if len(parts) >= 2:
                fn = Path(parts[-1]).name
                include_lines[fn] = i

    parsed = []
    parsed.extend(_parse_alumni_block(lines))
    parsed.extend(_parse_includefile_block(
        lines,
        "#------------ Start of IncludeFile - OCLC ------------#",
        "#------------ End of IncludeFile - OCLC ------------#",
    ))
    parsed.extend(_parse_includefile_block(
        lines,
        "#------------ Start of IncludeFile - Custom Stanzas ------------#",
        "#------------ End of IncludeFile - Custom Stanzas ------------#",
    ))

    with _connect() as conn:
        db_rows = conn.execute("SELECT filename, title, date_updated, note FROM stanzas").fetchall()
    db_map = {r["filename"]: r for r in db_rows}

    errors = 0
    config_filenames = set()
    for entry in parsed:
        fn = entry["filename"]
        config_filenames.add(fn)
        lineno = include_lines.get(fn)
        loc = f" (config.txt:{lineno})" if lineno else ""
        stanza_path = stanzas_dir / fn
        if not stanza_path.exists():
            print(f"FILE MISSING: stanzas/{fn}{loc}")
            errors += 1
        if fn not in db_map:
            print(f"MISSING in DB: {fn}{loc}")
            errors += 1
            continue
        row = db_map[fn]
        if row["title"] != entry["title"]:
            print(f"TITLE mismatch [{fn}]{loc}: config={entry['title']!r} db={row['title']!r}")
            errors += 1
        if (row["date_updated"] or "") != entry.get("date", ""):
            print(f"DATE mismatch [{fn}]{loc}: config={entry.get('date', '')!r} db={row['date_updated']!r}")
            errors += 1
        if (row["note"] or "") != entry.get("note", ""):
            print(f"NOTE mismatch [{fn}]{loc}: config={entry.get('note', '')!r} db={row['note']!r}")
            errors += 1

    db_filenames = {r["filename"] for r in db_rows}
    for fn in sorted(db_filenames - config_filenames):
        print(f"MISSING in config.txt: {fn}")
        errors += 1
        stanza_path = stanzas_dir / fn
        if not stanza_path.exists():
            print(f"  FILE MISSING: stanzas/{fn}")

    for stanza_file in sorted(stanzas_dir.iterdir()):
        if stanza_file.is_file() and stanza_file.name not in db_filenames:
            print(f"FILE NOT IN DB: stanzas/{stanza_file.name}")
            errors += 1

    if errors == 0:
        print("All entries match.")
    else:
        print(f"\n{errors} difference(s) found.")


def insert_stanza(section: str, filename: str, title: str, note: str = "") -> None:
    """Insert a single new stanza entry. Raises ValueError if it already exists."""
    if section not in ("alumni", "oclc", "custom"):
        raise ValueError(f"Invalid section: {section!r}")
    now = datetime.now().isoformat(timespec="seconds")
    today = datetime.now().strftime("%Y-%m-%d")   
    with _connect() as conn:
        try:
            cur = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM stanzas")
            next_id = cur.fetchone()[0]
            conn.execute(
                """
                INSERT INTO stanzas (id, section, filename, title, note, date_updated, date_synced)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (next_id, section, filename, title, note, today, now),
            )
        except sqlite3.IntegrityError:
            raise ValueError(f"{filename!r} already exists in section {section!r}")
    logger.info("Inserted {} / {} into DB ({})", section, filename, title)