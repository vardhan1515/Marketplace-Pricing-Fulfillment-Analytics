from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
EXPORT_DIR = DATA_DIR / "exports"
DOCS_DIR = PROJECT_ROOT / "docs"
SQL_DIR = PROJECT_ROOT / "sql"

RAW_CSV = RAW_DIR / "DataCoSupplyChainDataset.csv"
DATABASE_PATH = PROCESSED_DIR / "marketplace_analytics.sqlite"
PROFILE_JSON = PROCESSED_DIR / "data_profile.json"
DATA_DICTIONARY = DOCS_DIR / "data_dictionary.md"

ENCODING = "latin-1"
DATE_COLUMNS = ["order_date_dateorders", "shipping_date_dateorders"]
EXCLUDED_ORDER_STATUSES = {"CANCELED", "SUSPECTED_FRAUD"}
EXPECTED_ROW_COUNT = 180_519
EXPECTED_COLUMN_COUNT = 53


def ensure_directories() -> None:
    for path in (RAW_DIR, PROCESSED_DIR, EXPORT_DIR, DOCS_DIR):
        path.mkdir(parents=True, exist_ok=True)

