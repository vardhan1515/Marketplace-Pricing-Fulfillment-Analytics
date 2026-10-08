import sqlite3

from src.config import DATABASE_PATH, ENCODING, RAW_CSV, SQL_DIR, ensure_directories
from src.data_utils import read_source_csv


def load_database() -> None:
    ensure_directories()
    if not RAW_CSV.exists():
        raise FileNotFoundError(
            f"Missing {RAW_CSV}. Download the DataCo CSV as described in data/README.md."
        )

    frame = read_source_csv(RAW_CSV, ENCODING)
    for column in ("order_date_dateorders", "shipping_date_dateorders"):
        frame[column] = frame[column].dt.strftime("%Y-%m-%d %H:%M:%S")

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript((SQL_DIR / "01_load.sql").read_text(encoding="utf-8"))
        frame.to_sql(
            "stg_order_items",
            connection,
            if_exists="append",
            index=False,
            chunksize=10_000,
        )
        connection.executescript(
            (SQL_DIR / "02_order_table.sql").read_text(encoding="utf-8")
        )
        connection.executescript((SQL_DIR / "03_qa.sql").read_text(encoding="utf-8"))

    print(f"Loaded {len(frame):,} rows into {DATABASE_PATH}")


if __name__ == "__main__":
    load_database()

