import re
from collections.abc import Iterable

import pandas as pd


def normalize_column_name(name: str) -> str:
    """Convert source headers to stable snake_case SQLite identifiers."""
    normalized = re.sub(r"[^0-9A-Za-z]+", "_", name.strip()).strip("_").lower()
    return normalized


def normalize_columns(columns: Iterable[str]) -> list[str]:
    normalized = [normalize_column_name(column) for column in columns]
    if len(normalized) != len(set(normalized)):
        raise ValueError("Column normalization produced duplicate names.")
    return normalized


def read_source_csv(path, encoding: str) -> pd.DataFrame:
    frame = pd.read_csv(path, encoding=encoding, low_memory=False)
    frame.columns = normalize_columns(frame.columns)
    for column in ("order_date_dateorders", "shipping_date_dateorders"):
        frame[column] = pd.to_datetime(frame[column], errors="raise")
    return frame

