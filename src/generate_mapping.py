import csv
import json
from .logging_config import logger
from .config import DATA_DIR

def run():
    SOURCE_FILE = DATA_DIR / "mapping_source.csv"
    OUTPUT_FILE = DATA_DIR / "mapping.json"

    mapping = {}

    with open(SOURCE_FILE, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            filename = row["filename"].strip()+".txt"
            title = row["title"].strip()

            if filename and title:
                mapping[filename] = title

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

    logger.info(f"Generated {OUTPUT_FILE} with {len(mapping)} entries.")
    

if __name__ == "__main__":
    run()