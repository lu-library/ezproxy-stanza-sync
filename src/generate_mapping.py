import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

SOURCE_FILE = DATA_DIR / "mapping_source.csv"
OUTPUT_FILE = DATA_DIR / "mapping.json"

mapping = {}

with open(SOURCE_FILE, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        filename = row["filename"].strip()
        title = row["title"].strip()

        if filename and title:
            mapping[filename] = title

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(mapping, f, indent=2, ensure_ascii=False)

print(f"Generated {OUTPUT_FILE} with {len(mapping)} entries.")
