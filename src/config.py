from pathlib import Path

# Project root (ezproxy-stanza-sync/)
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
DIFF_DIR = DATA_DIR / "diff"
LOG_DIR = BASE_DIR / "logs"

OCUL_MOST_RECENT_URL = (
    "https://help.oclc.org/Library_Management/EZproxy/"
    "EZproxy_database_stanzas/Database_stanzas/"
    "EZproxy_database_stanzas_most_recent"
)
OCUL_ALL_URL = (
    "https://help.oclc.org/Library_Management/EZproxy/"
    "EZproxy_database_stanzas/Database_stanzas/"
    "EZproxy_database_stanzas_-_All"
)

BASE_URL = "https://help.oclc.org"
