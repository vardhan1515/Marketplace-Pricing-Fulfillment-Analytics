import math
import sqlite3

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.config import DATABASE_PATH, DOCS_DIR, EXPORT_DIR


CATEGORICAL_BASE = [
    "primary_category",
    "primary_department",
    "order_region",
    "market",
    "customer_segment",
]
NUMERIC_BASE = [
    "total_quantity",
    "average_net_unit_price",
    "weighted_discount_rate",
    "item_count",
    "category_count",
    "is_multi_category",
    "order_day_of_week",
    "order_hour",
    "order_month",
    "is_weekend",
    "year_end_holiday_window",
    "prior_7d_region_orders",
    "prior_7d_category_orders",
]


def _prior_seven_day_count(frame: pd.DataFrame, group_column: str) -> pd.Series:
    result = pd.Series(0, index=frame.index, dtype="int64")
    seven_days = np.timedelta64(7, "D")
    for _, group in frame.groupby(group_column, sort=False):
        ordered = group.sort_values(["order_date", "order_id"])
        timestamps = ordered["order_date"].to_numpy(dtype="datetime64[ns]")
        starts = np.searchsorted(timestamps, timestamps - seven_days, side="left")
        strictly_earlier = np.searchsorted(timestamps, timestamps, side="left")
        result.loc[ordered.index] = strictly_earlier - starts
    return result


def _enrich(orders: pd.DataFrame) -> pd.DataFrame:
    orders = orders.copy()
    orders["order_date"] = pd.to_datetime(orders["order_date"])
    orders = orders.sort_values(["order_date", "order_id"]).reset_index(drop=True)
    orders["order_day_of_week"] = orders["order_date"].dt.dayofweek
    orders["order_hour"] = orders["order_date"].dt.hour
    orders["order_month"] = orders["order_date"].dt.month
    orders["is_weekend"] = orders["order_day_of_week"].isin([5, 6]).astype(int)

    normalized = orders["order_date"].dt.normalize()
    christmas = pd.to_datetime(orders["order_date"].dt.year.astype(str) + "-12-25")
    new_year_current = pd.to_datetime(orders["order_date"].dt.year.astype(str) + "-01-01")
    new_year_next = pd.to_datetime((orders["order_date"].dt.year + 1).astype(str) + "-01-01")
    proximity = pd.concat(
        [
            (normalized - christmas).abs().dt.days,
            (normalized - new_year_current).abs().dt.days,
            (normalized - new_year_next).abs().dt.days,
        ],
        axis=1,
    ).min(axis=1)
    orders["year_end_holiday_window"] = proximity.le(7).astype(int)
    orders["prior_7d_region_orders"] = _prior_seven_day_count(orders, "order_region")
    orders["prior_7d_category_orders"] = _prior_seven_day_count(
        orders, "primary_category"
    )
    orders["delay_days"] = (
        orders["actual_shipping_days"] - orders["scheduled_shipping_days"]
    )
    return orders


def _preprocessor(categorical: list[str], numeric: list[str]) -> ColumnTransformer:
    return ColumnTransformer(
        [
            (
                "categorical",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical,
            ),
            (
                "numeric",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scale", StandardScaler()),
                    ]
                ),
                numeric,
            ),
        ]
    )


def _classification_pipeline(categorical, numeric, algorithm: str) -> Pipeline:
    if algorithm == "logistic_regression":
        estimator = LogisticRegression(
            max_iter=2_000, class_weight="balanced", random_state=42
        )
    else:
        estimator = RandomForestClassifier(
            n_estimators=250,
            min_samples_leaf=15,
            class_weight="balanced_subsample",
            random_state=42,
            n_jobs=-1,
        )
    return Pipeline(
        [("preprocess", _preprocessor(categorical, numeric)), ("model", estimator)]
    )


def _classification_metrics(actual, score, label: str, mode: str = "ALL") -> dict:
    top_n = max(1, math.ceil(len(actual) * 0.10))
    ranked = pd.DataFrame({"actual": np.asarray(actual), "score": score}).nlargest(
        top_n, "score"
    )
    base_rate = float(np.mean(actual))
    top_rate = float(ranked["actual"].mean())
    return {
        "model": label,
        "shipping_mode": mode,
        "orders": int(len(actual)),
        "late_rate": base_rate,
        "roc_auc": float(roc_auc_score(actual, score)),
        "pr_auc": float(average_precision_score(actual, score)),
        "brier_score": float(brier_score_loss(actual, score)),
        "top_decile_late_rate": top_rate,
        "top_decile_lift": top_rate / base_rate if base_rate else np.nan,
        "top_decile_capture": float(ranked["actual"].sum() / np.sum(actual)),
    }


def _calibration(actual, score, label: str) -> pd.DataFrame:
    frame = pd.DataFrame({"actual": np.asarray(actual), "score": score})
    frame["bin"] = pd.qcut(frame["score"], 10, duplicates="drop")
    result = (
        frame.groupby("bin", observed=True)
        .agg(orders=("actual", "size"), predicted_risk=("score", "mean"), observed_late_rate=("actual", "mean"))
        .reset_index(drop=True)
    )
    result["model"] = label
    result["absolute_calibration_error"] = (
        result["predicted_risk"] - result["observed_late_rate"]
    ).abs()
    return result


def _contact_curve(actual, score, label: str) -> pd.DataFrame:
    ranked = pd.DataFrame({"actual": np.asarray(actual), "score": score}).sort_values(
        "score", ascending=False
    )
    rows = []
    for fraction in (0.05, 0.10, 0.20, 0.30, 0.40, 0.50):
        contacted = ranked.head(math.ceil(len(ranked) * fraction))
        rows.append(
            {
                "model": label,
                "contact_fraction": fraction,
                "orders_contacted": len(contacted),
                "late_orders_captured": int(contacted["actual"].sum()),
                "late_capture_rate": float(contacted["actual"].sum() / ranked["actual"].sum()),
                "contact_precision": float(contacted["actual"].mean()),
            }
        )
    return pd.DataFrame(rows)


def _promise_feasibility(orders: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary_rows = []
    scenario_rows = []
    for mode, group in orders.groupby("shipping_mode"):
        actual = group["actual_shipping_days"]
        current = int(group["scheduled_shipping_days"].mode().iloc[0])
        quantiles = actual.quantile([0.80, 0.90, 0.95])
        recommendation = int(math.ceil(quantiles.loc[0.90]))
        summary_rows.append(
            {
                "shipping_mode": mode,
                "orders": len(group),
                "current_promise_days": current,
                "current_on_time_rate": float((actual <= current).mean()),
                "actual_days_p80": float(quantiles.loc[0.80]),
                "actual_days_p90": float(quantiles.loc[0.90]),
                "actual_days_p95": float(quantiles.loc[0.95]),
                "promise_for_90pct_on_time": recommendation,
                "on_time_rate_at_recommended_promise": float(
                    (actual <= recommendation).mean()
                ),
            }
        )
        for promise in range(0, 7):
            scenario_rows.append(
                {
                    "shipping_mode": mode,
                    "candidate_promise_days": promise,
                    "on_time_rate": float((actual <= promise).mean()),
                }
            )
    return pd.DataFrame(summary_rows), pd.DataFrame(scenario_rows)


def run_delivery_diagnostics() -> None:
    with sqlite3.connect(DATABASE_PATH) as connection:
        orders = pd.read_sql_query("SELECT * FROM fact_orders", connection)
    orders = _enrich(orders)
    cutoff = orders.loc[int(len(orders) * 0.80), "order_date"]
    train = orders.loc[orders["order_date"] < cutoff].copy()
    test = orders.loc[orders["order_date"] >= cutoff].copy()
    target = "calculated_late_flag"

    feature_sets = {
        "enriched_operational": (
            CATEGORICAL_BASE + ["shipping_mode"],
            NUMERIC_BASE + ["scheduled_shipping_days"],
        ),
        "enriched_without_shipping_promise": (CATEGORICAL_BASE, NUMERIC_BASE),
    }
    evaluations = []
    scores = {}

    train_mode_rates = train.groupby("shipping_mode")[target].mean()
    rule_scores = test["shipping_mode"].map(train_mode_rates).fillna(train[target].mean()).to_numpy()
    evaluations.append(
        _classification_metrics(test[target], rule_scores, "shipping_mode_only_rule")
    )
    scores["shipping_mode_only_rule"] = rule_scores

    for variant, (categorical, numeric) in feature_sets.items():
        features = categorical + numeric
        for algorithm in ("logistic_regression", "random_forest"):
            label = f"{variant}__{algorithm}"
            pipeline = _classification_pipeline(categorical, numeric, algorithm)
            pipeline.fit(train[features], train[target])
            score = pipeline.predict_proba(test[features])[:, 1]
            evaluations.append(_classification_metrics(test[target], score, label))
            scores[label] = score

    global_evaluation = pd.DataFrame(evaluations).sort_values("roc_auc", ascending=False)
    global_evaluation.to_csv(EXPORT_DIR / "enhanced_model_evaluation.csv", index=False)

    scored_test = test[
        [
            "order_id",
            "order_date",
            "primary_category",
            "order_region",
            "shipping_mode",
            "net_sales",
            "profit",
            target,
        ]
    ].copy()
    for label, score in scores.items():
        scored_test[f"risk_{label}"] = score
    scored_test.to_csv(EXPORT_DIR / "enhanced_delivery_risk_test_orders.csv", index=False)

    best_without_promise = global_evaluation.loc[
        global_evaluation["model"].str.startswith("enriched_without_shipping_promise")
    ].iloc[0]["model"]
    best_operational = global_evaluation.loc[
        global_evaluation["model"].str.startswith("enriched_operational")
    ].iloc[0]["model"]

    within_rows = []
    for mode in test["shipping_mode"].unique():
        test_mask = test["shipping_mode"].eq(mode)
        if test.loc[test_mask, target].nunique() < 2:
            continue
        for label in (best_operational, best_without_promise):
            within_rows.append(
                _classification_metrics(
                    test.loc[test_mask, target], scores[label][test_mask.to_numpy()], f"global__{label}", mode
                )
            )
        train_mode = train.loc[train["shipping_mode"].eq(mode)]
        test_mode = test.loc[test_mask]
        for algorithm in ("logistic_regression", "random_forest"):
            pipeline = _classification_pipeline(CATEGORICAL_BASE, NUMERIC_BASE, algorithm)
            features = CATEGORICAL_BASE + NUMERIC_BASE
            pipeline.fit(train_mode[features], train_mode[target])
            score = pipeline.predict_proba(test_mode[features])[:, 1]
            within_rows.append(
                _classification_metrics(
                    test_mode[target], score, f"mode_specific__{algorithm}", mode
                )
            )
    within_mode = pd.DataFrame(within_rows).sort_values(
        ["shipping_mode", "roc_auc"], ascending=[True, False]
    )
    within_mode.to_csv(EXPORT_DIR / "within_mode_model_evaluation.csv", index=False)

    calibration = pd.concat(
        [_calibration(test[target], scores[label], label) for label in (best_operational, best_without_promise)],
        ignore_index=True,
    )
    calibration.to_csv(EXPORT_DIR / "model_calibration.csv", index=False)
    calibration_summary = (
        calibration.assign(
            weighted_error=lambda frame: frame["orders"]
            * frame["absolute_calibration_error"]
        )
        .groupby("model")
        .apply(
            lambda group: group["weighted_error"].sum() / group["orders"].sum(),
            include_groups=False,
        )
    )
    contact = pd.concat(
        [_contact_curve(test[target], scores[label], label) for label in (best_operational, best_without_promise)],
        ignore_index=True,
    )
    contact.to_csv(EXPORT_DIR / "risk_contact_tradeoff.csv", index=False)

    regression_rows = []
    regression_scores = {}
    mode_mean = train.groupby("shipping_mode")["delay_days"].mean()
    baseline_prediction = test["shipping_mode"].map(mode_mean).fillna(train["delay_days"].mean())
    regression_scores["shipping_mode_mean_rule"] = baseline_prediction.to_numpy()
    for label, prediction in regression_scores.items():
        regression_rows.append(
            {
                "model": label,
                "mae_days": mean_absolute_error(test["delay_days"], prediction),
                "rmse_days": mean_squared_error(test["delay_days"], prediction) ** 0.5,
                "r_squared": r2_score(test["delay_days"], prediction),
            }
        )
    for variant, (categorical, numeric) in feature_sets.items():
        features = categorical + numeric
        pipeline = Pipeline(
            [
                ("preprocess", _preprocessor(categorical, numeric)),
                (
                    "model",
                    RandomForestRegressor(
                        n_estimators=250,
                        min_samples_leaf=15,
                        random_state=42,
                        n_jobs=-1,
                    ),
                ),
            ]
        )
        pipeline.fit(train[features], train["delay_days"])
        prediction = pipeline.predict(test[features])
        regression_rows.append(
            {
                "model": variant,
                "mae_days": mean_absolute_error(test["delay_days"], prediction),
                "rmse_days": mean_squared_error(test["delay_days"], prediction) ** 0.5,
                "r_squared": r2_score(test["delay_days"], prediction),
            }
        )
    regression = pd.DataFrame(regression_rows).sort_values("mae_days")
    regression.to_csv(EXPORT_DIR / "delay_days_model_evaluation.csv", index=False)

    promise, promise_scenarios = _promise_feasibility(orders)
    promise.to_csv(EXPORT_DIR / "promise_feasibility.csv", index=False)
    promise_scenarios.to_csv(EXPORT_DIR / "promise_scenarios.csv", index=False)

    operational_row = global_evaluation.loc[global_evaluation["model"].eq(best_operational)].iloc[0]
    reduced_row = global_evaluation.loc[global_evaluation["model"].eq(best_without_promise)].iloc[0]
    lines = [
        "# Delivery diagnostics and promise feasibility",
        "",
        "All features are available at order time. Prior-seven-day load counts use strictly earlier timestamps, excluding simultaneous and future orders.",
        "",
        "## Global classification",
        "",
        "| Model | ROC-AUC | PR-AUC | Brier | Top-decile lift |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in global_evaluation.itertuples(index=False):
        lines.append(
            f"| {row.model} | {row.roc_auc:.3f} | {row.pr_auc:.3f} | {row.brier_score:.3f} | {row.top_decile_lift:.2f}x |"
        )
    lines.extend(
        [
            "",
            f"The best enriched operational model has ROC-AUC {operational_row.roc_auc:.3f}; the best enriched model without shipping-promise fields has ROC-AUC {reduced_row.roc_auc:.3f}.",
            "",
            "## Within-mode classification",
            "",
            "| Mode | Model | Orders | Late rate | ROC-AUC | PR-AUC | Top-decile lift |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in within_mode.itertuples(index=False):
        lines.append(
            f"| {row.shipping_mode} | {row.model} | {row.orders:,} | {row.late_rate:.2%} | {row.roc_auc:.3f} | {row.pr_auc:.3f} | {row.top_decile_lift:.2f}x |"
        )
    lines.extend(
        [
            "",
            "First Class is omitted from within-mode AUC because every eligible First Class order is late.",
            "",
            "Same Day is the exception: order hour perfectly separates the source outcome in the test period. Orders before noon have zero actual shipping days; orders from noon onward have one. Order hour is available at placement, so this is not leakage, but the perfect cutoff is likely a data-generation rule and requires validation on operational data.",
            "",
            "## Delay-days regression",
            "",
            "| Model | MAE days | RMSE days | R² |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in regression.itertuples(index=False):
        lines.append(
            f"| {row.model} | {row.mae_days:.3f} | {row.rmse_days:.3f} | {row.r_squared:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Calibration and intervention workload",
            "",
            f"- Best operational expected calibration error: {calibration_summary.loc[best_operational]:.2%}",
            f"- Best no-promise expected calibration error: {calibration_summary.loc[best_without_promise]:.2%}",
            "",
            "| Model | Contacted | Orders contacted | Late capture | Contact precision |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in contact.itertuples(index=False):
        lines.append(
            f"| {row.model} | {row.contact_fraction:.0%} | {row.orders_contacted:,} | {row.late_capture_rate:.2%} | {row.contact_precision:.2%} |"
        )
    lines.extend(
        [
            "",
            "## Promise feasibility",
            "",
            "| Mode | Current promise | Current on-time | P80 actual | P90 actual | P95 actual | Promise for 90% | Resulting on-time |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in promise.itertuples(index=False):
        lines.append(
            f"| {row.shipping_mode} | {row.current_promise_days} days | {row.current_on_time_rate:.2%} | {row.actual_days_p80:.1f} | {row.actual_days_p90:.1f} | {row.actual_days_p95:.1f} | {row.promise_for_90pct_on_time} days | {row.on_time_rate_at_recommended_promise:.2%} |"
        )
    lines.extend(
        [
            "",
            "The promise scenarios are descriptive feasibility calculations, not forecasts of how operations or customers would respond to changed promises.",
            "",
        ]
    )
    (DOCS_DIR / "delivery_diagnostics.md").write_text("\n".join(lines), encoding="utf-8")
    print(global_evaluation.to_string(index=False))
    print(within_mode.to_string(index=False))
    print(regression.to_string(index=False))
    print(promise.to_string(index=False))


if __name__ == "__main__":
    run_delivery_diagnostics()
