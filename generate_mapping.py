import csv
import json

SOURCE_FILE = "mapping_source.csv"
OUTPUT_FILE = "mapping.json"

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
