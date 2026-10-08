import sqlite3

import numpy as np
import pandas as pd

from src.config import DATABASE_PATH, DOCS_DIR, EXPORT_DIR, PROJECT_ROOT


def _assign_actions(cells: pd.DataFrame) -> pd.DataFrame:
    eligible = cells["order_count"] >= 20
    margin_cut = cells.loc[eligible, "weighted_margin"].quantile(0.25)
    loss_cut = cells.loc[eligible, "negative_profit_order_rate"].quantile(0.75)
    risk_cut = cells.loc[eligible, "average_late_risk"].quantile(0.75)
    volume_cut = cells.loc[eligible, "order_count"].quantile(0.75)

    conditions = [
        eligible
        & (
            (cells["weighted_margin"] < 0)
            | (
                (cells["weighted_margin"] <= margin_cut)
                & (cells["negative_profit_order_rate"] >= loss_cut)
            )
        ),
        eligible & (cells["average_late_risk"] >= risk_cut),
        eligible
        & (cells["average_late_risk"] >= cells.loc[eligible, "average_late_risk"].median())
        & (cells["order_count"] >= volume_cut),
    ]
    choices = [
        "Reprice or cap discounts",
        "Change shipping mode",
        "Add capacity (validate)",
    ]
    cells["recommended_action"] = np.select(conditions, choices, default="Monitor")
    return cells


def create_dashboard_exports() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    scored_path = EXPORT_DIR / "enhanced_delivery_risk_test_orders.csv"
    scores = pd.read_csv(scored_path, parse_dates=["order_date"])
    score_column = "risk_enriched_operational__random_forest"

    with sqlite3.connect(DATABASE_PATH) as connection:
        items = pd.read_sql_query(
            """
            SELECT order_id, order_date, category_name, order_region, shipping_mode,
                   quantity, gross_sales, discount_amount, net_sales, profit,
                   calculated_late_flag
            FROM analysis_order_items
            """,
            connection,
        )
        orders = pd.read_sql_query("SELECT * FROM fact_orders", connection)

    items["order_date"] = pd.to_datetime(items["order_date"])
    orders["order_date"] = pd.to_datetime(orders["order_date"])
    orders["month"] = orders["order_date"].dt.to_period("M").dt.to_timestamp()
    monthly = (
        orders.groupby("month", as_index=False)
        .agg(
            orders=("order_id", "nunique"),
            units=("total_quantity", "sum"),
            net_sales=("net_sales", "sum"),
            profit=("profit", "sum"),
            late_orders=("calculated_late_flag", "sum"),
        )
    )
    monthly["weighted_margin"] = monthly["profit"] / monthly["net_sales"]
    monthly["late_rate"] = monthly["late_orders"] / monthly["orders"]
    monthly.to_csv(EXPORT_DIR / "overview_monthly.csv", index=False)

    risk_orders = scores[
        [
            "order_id",
            "order_date",
            "primary_category",
            "order_region",
            "shipping_mode",
            "net_sales",
            "profit",
            "calculated_late_flag",
            score_column,
        ]
    ].rename(columns={score_column: "predicted_late_risk"})
    risk_orders["positive_profit_at_stake"] = risk_orders["profit"].clip(lower=0)
    risk_orders["profit_exposure"] = (
        risk_orders["predicted_late_risk"] * risk_orders["positive_profit_at_stake"]
    )
    risk_orders.sort_values("profit_exposure", ascending=False).to_csv(
        EXPORT_DIR / "risk_ranked_orders.csv", index=False
    )

    cells = (
        risk_orders.groupby(["primary_category", "order_region"], as_index=False)
        .agg(
            order_count=("order_id", "nunique"),
            net_sales=("net_sales", "sum"),
            profit=("profit", "sum"),
            late_rate=("calculated_late_flag", "mean"),
            average_late_risk=("predicted_late_risk", "mean"),
            profit_exposure=("profit_exposure", "sum"),
            negative_profit_order_rate=("profit", lambda values: float((values < 0).mean())),
        )
    )
    cells["weighted_margin"] = cells["profit"] / cells["net_sales"]
    cells["priority_rank"] = cells["profit_exposure"].rank(
        method="dense", ascending=False
    ).astype(int)
    cells = _assign_actions(cells)
    cells.sort_values("priority_rank").to_csv(EXPORT_DIR / "action_grid.csv", index=False)

    action_counts = cells["recommended_action"].value_counts()
    formula = [
        "# Priority score and action rules",
        "",
        "## Formula",
        "",
        "At order level:",
        "",
        "```text",
        "profit_exposure = predicted_late_probability × max(order_profit, 0)",
        "```",
        "",
        "At category-region level, the score is the sum of order-level profit exposure. It is a prioritization index measured in risk-weighted profit dollars, not an estimate of loss caused by lateness.",
        "",
        "## Deterministic action rules",
        "",
        "Cells with fewer than 20 test orders default to Monitor. Among sufficiently supported cells:",
        "",
        "1. **Reprice or cap discounts:** negative margin, or both bottom-quartile margin and top-quartile negative-profit rate.",
        "2. **Change shipping mode:** top-quartile predicted late risk, after applying the pricing rule.",
        "3. **Add capacity (validate):** at least median risk and top-quartile order volume, after the prior rules.",
        "4. **Monitor:** all remaining cells.",
        "",
        "The capacity action is a hypothesis requiring external capacity data; this dataset contains no direct capacity measure.",
        "",
        "## Generated action counts",
        "",
    ]
    formula.extend(f"- {action}: {count:,} cells" for action, count in action_counts.items())
    (DOCS_DIR / "priority_score.md").write_text("\n".join(formula) + "\n", encoding="utf-8")
    print("Power BI-ready exports and action grid created.")


if __name__ == "__main__":
    create_dashboard_exports()
