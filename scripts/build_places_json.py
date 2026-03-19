from pathlib import Path
import json
import pandas as pd
import unicodedata


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


def slugify_column_name(column_name: str) -> str:
    """
    Convert spreadsheet column names to JSON-friendly snake_case keys.

    Examples:
    - "distance minutes" -> "distance_minutes"
    - "Google Maps URL" -> "google_maps_url"
    - "Café Type" -> "cafe_type"
    """
    text = str(column_name).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace("&", " and ")
    text = text.replace("/", " ")
    text = text.replace("-", "_")
    text = " ".join(text.split())
    text = text.replace(" ", "_")
    return text


def row_to_dict(row) -> dict:
    """Convert a dataframe row to a clean dictionary with normalised keys."""
    item = {}

    for column, value in row.items():
        key = slugify_column_name(column)
        cleaned = clean_value(value)

        if key == "featured":
            cleaned = str(cleaned).lower() in {"true", "1", "yes"}

        item[key] = cleaned

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

    if records:
        print("Sample keys:")
        print(list(records[0].keys()))


if __name__ == "__main__":
    main()
