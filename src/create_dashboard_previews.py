from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import seaborn as sns

from src.config import EXPORT_DIR, PROJECT_ROOT


SCREENSHOT_DIR = PROJECT_ROOT / "powerbi" / "screenshots"
NAVY = "#12304A"
BLUE = "#277DA1"
TEAL = "#43AA8B"
GOLD = "#F9C74F"
RED = "#F94144"
GRAY = "#667085"
BG = "#F7F9FC"


def _style() -> None:
    sns.set_theme(style="whitegrid")
    plt.rcParams.update(
        {
            "figure.facecolor": BG,
            "axes.facecolor": "white",
            "axes.edgecolor": "#D0D5DD",
            "axes.titleweight": "bold",
            "font.family": "DejaVu Sans",
        }
    )


def _currency_millions(value: float) -> str:
    return f"${value / 1_000_000:.2f}M"


def _kpi(ax, title: str, value: str, subtitle: str = "") -> None:
    ax.set_facecolor("white")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color("#E4E7EC")
    ax.text(0.06, 0.72, title.upper(), color=GRAY, fontsize=9, weight="bold", transform=ax.transAxes)
    ax.text(0.06, 0.33, value, color=NAVY, fontsize=22, weight="bold", transform=ax.transAxes)
    if subtitle:
        ax.text(0.06, 0.10, subtitle, color=GRAY, fontsize=8, transform=ax.transAxes)


def overview_page() -> Path:
    monthly = pd.read_csv(EXPORT_DIR / "overview_monthly.csv", parse_dates=["month"])
    margins = pd.read_csv(EXPORT_DIR / "margin_by_dimension.csv")
    regions = margins.loc[margins["dimension"] == "region"].nlargest(8, "net_sales")

    fig = plt.figure(figsize=(16, 9), layout="constrained")
    grid = fig.add_gridspec(3, 5, height_ratios=[0.75, 2.2, 2.2])
    fig.suptitle("Marketplace Pricing & Fulfillment — Overview", fontsize=22, weight="bold", color=NAVY)
    total_orders = int(monthly["orders"].sum())
    total_sales = monthly["net_sales"].sum()
    total_profit = monthly["profit"].sum()
    total_margin = total_profit / total_sales
    total_late = monthly["late_orders"].sum() / monthly["orders"].sum()
    cards = [
        ("Eligible orders", f"{total_orders:,}", "Canceled/fraud excluded"),
        ("Net sales", _currency_millions(total_sales), "Realized revenue"),
        ("Profit", _currency_millions(total_profit), "Item profit summed"),
        ("Weighted margin", f"{total_margin:.1%}", "Profit / net sales"),
        ("Late rate", f"{total_late:.1%}", "Actual days > scheduled"),
    ]
    for index, card in enumerate(cards):
        _kpi(fig.add_subplot(grid[0, index]), *card)

    ax_sales = fig.add_subplot(grid[1, :3])
    ax_sales.plot(monthly["month"], monthly["net_sales"] / 1e6, color=BLUE, linewidth=2.5, label="Net sales")
    ax_sales.plot(monthly["month"], monthly["profit"] / 1e6, color=TEAL, linewidth=2.2, label="Profit")
    ax_sales.set_title("Monthly commercial trend", loc="left")
    ax_sales.set_ylabel("USD millions")
    ax_sales.legend(frameon=False, ncol=2)

    ax_late = fig.add_subplot(grid[1, 3:])
    ax_late.plot(monthly["month"], monthly["late_rate"], color=RED, linewidth=2.5)
    ax_late.axhline(monthly["late_rate"].mean(), color=GRAY, linestyle="--", linewidth=1)
    ax_late.set_title("Monthly late rate", loc="left")
    ax_late.yaxis.set_major_formatter(mtick.PercentFormatter(1))
    ax_late.set_ylim(0, 0.75)

    ax_region = fig.add_subplot(grid[2, :3])
    ordered = regions.sort_values("net_sales")
    ax_region.barh(ordered["segment"], ordered["net_sales"] / 1e6, color=BLUE)
    ax_region.set_title("Largest regions by net sales", loc="left")
    ax_region.set_xlabel("USD millions")

    ax_margin = fig.add_subplot(grid[2, 3:])
    ordered_margin = regions.sort_values("weighted_margin")
    colors = [TEAL if value >= 0 else RED for value in ordered_margin["weighted_margin"]]
    ax_margin.barh(ordered_margin["segment"], ordered_margin["weighted_margin"], color=colors)
    ax_margin.set_title("Regional weighted margin", loc="left")
    ax_margin.xaxis.set_major_formatter(mtick.PercentFormatter(1))

    path = SCREENSHOT_DIR / "01_overview.png"
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    return path


def pricing_page() -> Path:
    margins = pd.read_csv(EXPORT_DIR / "margin_by_dimension.csv")
    discount = pd.read_csv(EXPORT_DIR / "discount_summary.csv")
    caps = pd.read_csv(EXPORT_DIR / "discount_cap_scenarios.csv")
    categories = margins.loc[margins["dimension"] == "category"].copy()

    fig = plt.figure(figsize=(16, 9), layout="constrained")
    grid = fig.add_gridspec(2, 2)
    fig.suptitle("Marketplace Pricing & Fulfillment — Pricing and Margin", fontsize=22, weight="bold", color=NAVY)

    ax_cat = fig.add_subplot(grid[0, :])
    shown = pd.concat([categories.nsmallest(8, "weighted_margin"), categories.nlargest(8, "weighted_margin")]).drop_duplicates()
    shown = shown.sort_values("weighted_margin")
    ax_cat.barh(shown["segment"], shown["weighted_margin"], color=[RED if value < 0 else TEAL for value in shown["weighted_margin"]])
    ax_cat.set_title("Category margin spread — lowest and highest", loc="left")
    ax_cat.xaxis.set_major_formatter(mtick.PercentFormatter(1))
    ax_cat.axvline(0, color=NAVY, linewidth=1)

    ax_discount = fig.add_subplot(grid[1, 0])
    ax_discount.plot(discount["discount_rate"], discount["weighted_margin"], marker="o", color=BLUE, label="Weighted margin")
    ax_discount.plot(discount["discount_rate"], discount["negative_profit_item_rate"], marker="o", color=RED, label="Negative-profit rate")
    ax_discount.set_title("Discount depth versus profitability", loc="left")
    ax_discount.xaxis.set_major_formatter(mtick.PercentFormatter(1))
    ax_discount.yaxis.set_major_formatter(mtick.PercentFormatter(1))
    ax_discount.legend(frameon=False)

    ax_cap = fig.add_subplot(grid[1, 1])
    ax_cap.bar(caps["discount_cap"].map(lambda value: f"{value:.0%}"), caps["accounting_profit_change"] / 1000, color=[GOLD, BLUE, TEAL])
    ax_cap.set_title("Fixed-volume discount-cap scenarios", loc="left")
    ax_cap.set_ylabel("Accounting profit change ($000s)")
    for position, value in enumerate(caps["accounting_profit_change"] / 1000):
        ax_cap.text(position, value, f"${value:,.0f}K", ha="center", va="bottom", weight="bold", color=NAVY)
    ax_cap.text(0.01, -0.18, "Scenario only: quantity and inferred costs held constant", transform=ax_cap.transAxes, color=GRAY, fontsize=9)

    path = SCREENSHOT_DIR / "02_pricing_margin.png"
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    return path


def action_page() -> Path:
    actions = pd.read_csv(EXPORT_DIR / "action_grid.csv")
    risks = pd.read_csv(EXPORT_DIR / "risk_ranked_orders.csv")
    forecast = pd.read_csv(EXPORT_DIR / "weekly_forecast_backtest.csv", parse_dates=["week_start"])
    top_categories = actions.groupby("primary_category")["profit_exposure"].sum().nlargest(10).index
    top_regions = actions.groupby("order_region")["profit_exposure"].sum().nlargest(8).index
    matrix = actions.loc[
        actions["primary_category"].isin(top_categories)
        & actions["order_region"].isin(top_regions)
    ].pivot(index="primary_category", columns="order_region", values="profit_exposure")

    fig = plt.figure(figsize=(16, 9), layout="constrained")
    grid = fig.add_gridspec(2, 3, width_ratios=[2.2, 1, 1.3])
    fig.suptitle("Marketplace Pricing & Fulfillment — Action Grid", fontsize=22, weight="bold", color=NAVY)

    ax_heat = fig.add_subplot(grid[:, 0])
    sns.heatmap(matrix.fillna(0), cmap="YlGnBu", linewidths=0.4, ax=ax_heat, cbar_kws={"label": "Profit exposure ($)"})
    ax_heat.set_title("Category × region priority", loc="left")
    ax_heat.set_xlabel("")
    ax_heat.set_ylabel("")

    ax_actions = fig.add_subplot(grid[0, 1])
    counts = actions["recommended_action"].value_counts().sort_values()
    palette = {"Monitor": GRAY, "Change shipping mode": BLUE, "Reprice or cap discounts": GOLD, "Add capacity (validate)": TEAL}
    ax_actions.barh(counts.index, counts.values, color=[palette.get(name, BLUE) for name in counts.index])
    ax_actions.set_title("Recommended actions", loc="left")
    ax_actions.set_xlabel("Cells")

    ax_forecast = fig.add_subplot(grid[1, 1:])
    selected_category = "Cleats"
    subset = forecast.loc[forecast["category_name"] == selected_category]
    actual = subset.drop_duplicates("week_start").sort_values("week_start")
    ax_forecast.plot(actual["week_start"], actual["actual_units"], color=NAVY, marker="o", label="Actual")
    for method, color in [("lag_feature_model", TEAL), ("moving_average_4", GOLD), ("naive_previous_week", GRAY)]:
        group = subset.loc[subset["method"] == method].sort_values("week_start")
        ax_forecast.plot(group["week_start"], group["forecast_units"], color=color, linewidth=1.8, label=method.replace("_", " "))
    ax_forecast.set_title(f"12-week forecast backtest — {selected_category}", loc="left")
    ax_forecast.set_ylabel("Units")
    ax_forecast.legend(frameon=False, fontsize=8, ncol=2)

    ax_table = fig.add_subplot(grid[0, 2])
    ax_table.axis("off")
    top = risks.nlargest(8, "profit_exposure")[["order_id", "primary_category", "predicted_late_risk", "profit_exposure"]]
    cell_text = [[f"{int(row.order_id)}", str(row.primary_category)[:18], f"{row.predicted_late_risk:.0%}", f"${row.profit_exposure:,.0f}"] for row in top.itertuples(index=False)]
    table = ax_table.table(cellText=cell_text, colLabels=["Order", "Category", "Risk", "Exposure"], loc="center", cellLoc="left")
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.45)
    ax_table.set_title("Highest profit exposure orders", loc="left")

    path = SCREENSHOT_DIR / "03_action_grid.png"
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    return path


def create_dashboard_previews() -> list[Path]:
    _style()
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    paths = [overview_page(), pricing_page(), action_page()]
    print("Created dashboard previews:")
    for path in paths:
        print(path)
    return paths


if __name__ == "__main__":
    create_dashboard_previews()
