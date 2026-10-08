import hashlib
import json

import pandas as pd

from src.config import (
    DATA_DICTIONARY,
    ENCODING,
    EXPECTED_COLUMN_COUNT,
    EXPECTED_ROW_COUNT,
    PROFILE_JSON,
    RAW_CSV,
    ensure_directories,
)
from src.data_utils import read_source_csv


def _sha256(path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def profile_data() -> dict:
    ensure_directories()
    frame = read_source_csv(RAW_CSV, ENCODING)
    if frame.shape != (EXPECTED_ROW_COUNT, EXPECTED_COLUMN_COUNT):
        raise ValueError(
            f"Unexpected source shape {frame.shape}; expected "
            f"({EXPECTED_ROW_COUNT}, {EXPECTED_COLUMN_COUNT})."
        )

    calculated_late = (
        frame["days_for_shipping_real"] > frame["days_for_shipment_scheduled"]
    ).astype("int8")
    mismatch = calculated_late.ne(frame["late_delivery_risk"])
    excluded = frame["order_status"].isin(["CANCELED", "SUSPECTED_FRAUD"])

    profile = {
        "file": str(RAW_CSV),
        "sha256": _sha256(RAW_CSV),
        "rows": int(len(frame)),
        "columns": int(frame.shape[1]),
        "distinct_orders": int(frame["order_id"].nunique()),
        "distinct_order_items": int(frame["order_item_id"].nunique()),
        "exact_duplicate_rows": int(frame.duplicated().sum()),
        "order_date_min": frame["order_date_dateorders"].min().isoformat(),
        "order_date_max": frame["order_date_dateorders"].max().isoformat(),
        "shipping_date_min": frame["shipping_date_dateorders"].min().isoformat(),
        "shipping_date_max": frame["shipping_date_dateorders"].max().isoformat(),
        "excluded_item_rows": int(excluded.sum()),
        "excluded_orders": int(frame.loc[excluded, "order_id"].nunique()),
        "late_flag_mismatches": int(mismatch.sum()),
        "eligible_late_flag_mismatches": int((mismatch & ~excluded).sum()),
        "columns_detail": [],
    }

    for column in frame.columns:
        profile["columns_detail"].append(
            {
                "column": column,
                "dtype": str(frame[column].dtype),
                "null_count": int(frame[column].isna().sum()),
                "null_pct": round(float(frame[column].isna().mean() * 100), 4),
                "distinct_count": int(frame[column].nunique(dropna=True)),
            }
        )

    PROFILE_JSON.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    DATA_DICTIONARY.write_text(_render_markdown(profile), encoding="utf-8")
    print(f"Wrote {PROFILE_JSON} and {DATA_DICTIONARY}")
    return profile


def _render_markdown(profile: dict) -> str:
    lines = [
        "# Data dictionary and source profile",
        "",
        "Generated from the local raw CSV by `python -m src.profile_data`.",
        "",
        "## Source profile",
        "",
        f"- Rows: {profile['rows']:,}",
        f"- Columns: {profile['columns']}",
        f"- Distinct orders: {profile['distinct_orders']:,}",
        f"- Distinct order items: {profile['distinct_order_items']:,}",
        f"- Exact duplicate rows: {profile['exact_duplicate_rows']:,}",
        f"- Order dates: {profile['order_date_min']} through {profile['order_date_max']}",
        f"- Shipping dates: {profile['shipping_date_min']} through {profile['shipping_date_max']}",
        f"- Canceled/suspected-fraud item rows: {profile['excluded_item_rows']:,}",
        f"- Canceled/suspected-fraud orders: {profile['excluded_orders']:,}",
        f"- Source/calculated late-label disagreements: {profile['late_flag_mismatches']:,}",
        f"- Late-label disagreements among eligible orders: {profile['eligible_late_flag_mismatches']:,}",
        f"- SHA-256: `{profile['sha256']}`",
        "",
        "## Fields",
        "",
        "| Normalized field | Inferred type | Nulls | Null % | Distinct non-null |",
        "|---|---:|---:|---:|---:|",
    ]
    for field in profile["columns_detail"]:
        lines.append(
            f"| `{field['column']}` | {field['dtype']} | "
            f"{field['null_count']:,} | {field['null_pct']:.4f}% | "
            f"{field['distinct_count']:,} |"
        )
    lines.extend(
        [
            "",
            "## Known source-field relationships",
            "",
            "- `benefit_per_order` duplicates `order_profit_per_order`.",
            "- `sales_per_customer` duplicates `order_item_total`.",
            "- `product_price` duplicates `order_item_product_price`.",
            "- `product_description` is entirely null.",
            "- `order_zipcode` is mostly null and is excluded from analytical exports.",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    profile_data()

