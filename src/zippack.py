import zipfile
from datetime import datetime
from pathlib import Path
from src.config import CONFIG_FILE, DATA_DIR

def run():
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    zip_path = DATA_DIR / f"ez-config-{timestamp}.zip"
    stanzas_dir = DATA_DIR / "stanzas"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        if CONFIG_FILE.exists():
            zf.write(CONFIG_FILE, CONFIG_FILE.name)
        if stanzas_dir.exists():
            for stanza_file in sorted(stanzas_dir.iterdir()):
                if stanza_file.is_file():
                    zf.write(stanza_file, f"stanzas/{stanza_file.name}")

    print(f"Packed {zip_path}")