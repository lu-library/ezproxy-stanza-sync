from pathlib import Path
import sys

# Project root (ezproxy-stanza-sync/)
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
DIFF_DIR = DATA_DIR / "diff"
LOG_DIR = DATA_DIR / "logs"
CONFIG_DIR = DATA_DIR / "config"
CONFIG_FILE = CONFIG_DIR / "config.txt"

OCLC_MOST_RECENT_URL = (
    "https://help.oclc.org/Library_Management/EZproxy/"
    "EZproxy_database_stanzas/Database_stanzas/"
    "EZproxy_database_stanzas_most_recent"
)
OCLC_ALL_URL = (
    "https://help.oclc.org/Library_Management/EZproxy/"
    "EZproxy_database_stanzas/Database_stanzas/"
    "EZproxy_database_stanzas_-_All"
)

BASE_URL = "https://help.oclc.org"
