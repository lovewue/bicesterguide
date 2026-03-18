from pathlib import Path
import json
import pandas as pd


# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

DATA_DIR = PROJECT_ROOT / "data"
INPUT_FILE = DATA_DIR / "places_master.xlsx"
OUTPUT_FILE = DATA_DIR / "places.json"


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def clean_value(value):
    """Convert NaN to empty string and normalise booleans."""
    if pd.isna(value):
        return ""

    if isinstance(value, bool):
        return value

    return str(value).strip()


def row_to_dict(row) -> dict:
    """Convert a dataframe row to a clean dictionary."""
    item = {}

    for column, value in row.items():
        cleaned = clean_value(value)

        if column == "featured":
            if str(cleaned).lower() in ("true", "1", "yes"):
                cleaned = True
            else:
                cleaned = False

        item[column] = cleaned

    return item


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    df = pd.read_excel(INPUT_FILE)

    records = [row_to_dict(row) for _, row in df.iterrows()]

    OUTPUT_FILE.write_text(
        json.dumps(records, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Built JSON: {OUTPUT_FILE}")
    print(f"Records: {len(records)}")


if __name__ == "__main__":
    main()
