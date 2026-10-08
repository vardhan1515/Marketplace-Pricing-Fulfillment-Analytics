import sqlite3

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from src.config import DATABASE_PATH, DOCS_DIR, EXPORT_DIR


TEST_WEEKS = 12
N_CATEGORIES = 4
LAGS = (1, 2, 3, 4, 13, 52)


def _trim_sparse_edges(series: pd.Series) -> pd.Series:
    series = series.sort_index()
    positive = series[series > 0]
    if positive.empty:
        return series.iloc[0:0]
    series = series.loc[positive.index.min() : positive.index.max()]
    if len(series) < 3:
        return series
    interior_median = series.iloc[1:-1].median()
    threshold = interior_median * 0.25
    if series.iloc[0] < threshold:
        series = series.iloc[1:]
    if len(series) > 1 and series.iloc[-1] < threshold:
        series = series.iloc[:-1]
    return series


def _feature_frame(series: pd.Series) -> pd.DataFrame:
    frame = pd.DataFrame({"actual_units": series.astype(float)})
    for lag in LAGS:
        frame[f"lag_{lag}"] = frame["actual_units"].shift(lag)
    frame["rolling_mean_4"] = frame["actual_units"].shift(1).rolling(4).mean()
    frame["rolling_mean_8"] = frame["actual_units"].shift(1).rolling(8).mean()
    frame["trend"] = np.arange(len(frame), dtype=float)
    frame["month_sin"] = np.sin(2 * np.pi * frame.index.month / 12)
    frame["month_cos"] = np.cos(2 * np.pi * frame.index.month / 12)
    return frame


def _wape(actual: pd.Series, forecast: pd.Series) -> float:
    denominator = actual.abs().sum()
    return float((actual - forecast).abs().sum() / denominator) if denominator else np.nan


def run_demand_forecast() -> pd.DataFrame:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DATABASE_PATH) as connection:
        items = pd.read_sql_query(
            "SELECT order_date, category_name, quantity FROM analysis_order_items",
            connection,
        )
    items["order_date"] = pd.to_datetime(items["order_date"])
    items["week"] = items["order_date"].dt.to_period("W-SUN").dt.start_time
    weekly = items.groupby(["category_name", "week"])["quantity"].sum()

    candidates = []
    series_by_category = {}
    for category in weekly.index.get_level_values(0).unique():
        observed = weekly.loc[category]
        complete_index = pd.date_range(observed.index.min(), observed.index.max(), freq="7D")
        series = _trim_sparse_edges(observed.reindex(complete_index, fill_value=0))
        if len(series) < 104 + TEST_WEEKS:
            continue
        coverage = float((series > 0).mean())
        if coverage < 0.80:
            continue
        training_units = float(series.iloc[:-TEST_WEEKS].sum())
        candidates.append((category, training_units, coverage, len(series)))
        series_by_category[category] = series

    selected = [
        row[0]
        for row in sorted(candidates, key=lambda row: row[1], reverse=True)[:N_CATEGORIES]
    ]
    if len(selected) < N_CATEGORIES:
        raise RuntimeError("Fewer than four categories satisfy the continuity contract.")

    metric_rows = []
    forecast_rows = []
    feature_columns = [
        *(f"lag_{lag}" for lag in LAGS),
        "rolling_mean_4",
        "rolling_mean_8",
        "trend",
        "month_sin",
        "month_cos",
    ]
    for category in selected:
        features = _feature_frame(series_by_category[category]).dropna().copy()
        train = features.iloc[:-TEST_WEEKS]
        test = features.iloc[-TEST_WEEKS:]
        model = RandomForestRegressor(
            n_estimators=400,
            min_samples_leaf=3,
            random_state=42,
            n_jobs=-1,
        )
        model.fit(train[feature_columns], train["actual_units"])
        predictions = {
            "lag_feature_model": np.maximum(model.predict(test[feature_columns]), 0),
            "naive_previous_week": test["lag_1"].to_numpy(),
            "moving_average_4": test["rolling_mean_4"].to_numpy(),
        }
        for method, values in predictions.items():
            metric_rows.append(
                {
                    "category_name": category,
                    "method": method,
                    "test_weeks": len(test),
                    "wape": _wape(test["actual_units"], pd.Series(values, index=test.index)),
                    "mae": float(np.mean(np.abs(test["actual_units"].to_numpy() - values))),
                    "test_start": test.index.min(),
                    "test_end": test.index.max(),
                }
            )
            for week, actual, forecast in zip(
                test.index, test["actual_units"].to_numpy(), values
            ):
                forecast_rows.append(
                    {
                        "category_name": category,
                        "week_start": week,
                        "method": method,
                        "actual_units": actual,
                        "forecast_units": forecast,
                    }
                )

    metrics = pd.DataFrame(metric_rows)
    forecasts = pd.DataFrame(forecast_rows)
    metrics.to_csv(EXPORT_DIR / "forecast_evaluation.csv", index=False)
    forecasts.to_csv(EXPORT_DIR / "weekly_forecast_backtest.csv", index=False)

    report = [
        "# Short-horizon demand forecast evaluation",
        "",
        "Demand is weekly units sold, not order-item row count. Four categories were selected by pre-holdout volume after requiring at least 80% active-week coverage and two years of history. Sparse first or last weeks below 25% of the interior median were removed.",
        "",
        "The final 12 active weeks of each category are evaluated with rolling one-step features. The lag model uses lags 1, 2, 3, 4, 13, and 52, rolling means, trend, and cyclical month features.",
        "",
        "| Category | Method | Test period | WAPE | MAE units |",
        "|---|---|---|---:|---:|",
    ]
    for row in metrics.sort_values(["category_name", "wape"]).itertuples(index=False):
        report.append(
            f"| {row.category_name} | {row.method} | "
            f"{pd.Timestamp(row.test_start).date()} to {pd.Timestamp(row.test_end).date()} | "
            f"{row.wape:.2%} | {row.mae:,.1f} |"
        )
    report.extend(
        [
            "",
            "Because category availability changes abruptly in the source data, each category is evaluated on its own last active weeks rather than treating later zero-coverage weeks as genuine zero demand.",
            "",
        ]
    )
    (DOCS_DIR / "forecast_evaluation.md").write_text("\n".join(report), encoding="utf-8")
    print(metrics.sort_values(["category_name", "wape"]).to_string(index=False))
    print(f"Selected categories: {', '.join(selected)}")
    return metrics


if __name__ == "__main__":
    run_demand_forecast()
