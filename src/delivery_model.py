import math
import sqlite3

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.config import DATABASE_PATH, DOCS_DIR, EXPORT_DIR, PROJECT_ROOT


MODEL_DIR = PROJECT_ROOT / "models"
BASE_CATEGORICAL = ["primary_category", "order_region"]
BASE_NUMERIC = [
    "total_quantity",
    "average_net_unit_price",
    "weighted_discount_rate",
]


def _make_pipeline(categorical: list[str], numeric: list[str], model) -> Pipeline:
    preprocessing = ColumnTransformer(
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
    return Pipeline([("preprocess", preprocessing), ("model", model)])


def _metrics(y_true: pd.Series, scores, split_label: str) -> dict:
    top_n = max(1, math.ceil(len(y_true) * 0.10))
    ranked = pd.DataFrame({"actual": y_true.to_numpy(), "score": scores}).nlargest(
        top_n, "score"
    )
    return {
        "model": split_label,
        "test_orders": int(len(y_true)),
        "test_late_rate": float(y_true.mean()),
        "roc_auc": float(roc_auc_score(y_true, scores)),
        "pr_auc": float(average_precision_score(y_true, scores)),
        "brier_score": float(brier_score_loss(y_true, scores)),
        "top_decile_late_rate": float(ranked["actual"].mean()),
        "top_decile_late_capture": float(ranked["actual"].sum() / y_true.sum()),
    }


def run_delivery_model() -> pd.DataFrame:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DATABASE_PATH) as connection:
        orders = pd.read_sql_query("SELECT * FROM fact_orders", connection)

    orders["order_date"] = pd.to_datetime(orders["order_date"])
    orders = orders.sort_values(["order_date", "order_id"]).reset_index(drop=True)
    boundary_position = int(len(orders) * 0.80)
    cutoff = orders.loc[boundary_position, "order_date"]
    train = orders.loc[orders["order_date"] < cutoff].copy()
    test = orders.loc[orders["order_date"] >= cutoff].copy()
    target = "calculated_late_flag"

    variants = {
        "operational": {
            "categorical": BASE_CATEGORICAL + ["shipping_mode"],
            "numeric": BASE_NUMERIC + ["scheduled_shipping_days"],
        },
        "stress_test_without_shipping_promise": {
            "categorical": BASE_CATEGORICAL,
            "numeric": BASE_NUMERIC,
        },
    }
    algorithms = {
        "logistic_regression": LogisticRegression(
            max_iter=2_000, class_weight="balanced", random_state=42
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=300,
            min_samples_leaf=10,
            class_weight="balanced_subsample",
            random_state=42,
            n_jobs=-1,
        ),
    }

    rows = []
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
    for variant_name, feature_groups in variants.items():
        features = feature_groups["categorical"] + feature_groups["numeric"]
        for algorithm_name, estimator in algorithms.items():
            pipeline = _make_pipeline(
                feature_groups["categorical"], feature_groups["numeric"], estimator
            )
            pipeline.fit(train[features], train[target])
            scores = pipeline.predict_proba(test[features])[:, 1]
            model_name = f"{variant_name}__{algorithm_name}"
            row = _metrics(test[target], scores, model_name)
            row["train_orders"] = int(len(train))
            row["train_end"] = train["order_date"].max().isoformat()
            row["test_start"] = test["order_date"].min().isoformat()
            rows.append(row)
            scored_test[f"risk_{model_name}"] = scores
            joblib.dump(pipeline, MODEL_DIR / f"{model_name}.joblib")

    evaluation = pd.DataFrame(rows).sort_values("roc_auc", ascending=False)
    evaluation.to_csv(EXPORT_DIR / "model_evaluation.csv", index=False)
    scored_test.to_csv(EXPORT_DIR / "delivery_risk_test_orders.csv", index=False)

    full_best = evaluation.loc[
        evaluation["model"].str.startswith("operational__")
    ].iloc[0]
    reduced_best = evaluation.loc[
        evaluation["model"].str.startswith("stress_test_without_shipping_promise__")
    ].iloc[0]
    auc_gap = full_best["roc_auc"] - reduced_best["roc_auc"]

    report = [
        "# Delivery-risk model evaluation",
        "",
        "The target is calculated only for eligible orders as actual shipping days greater than scheduled shipping days. The split is chronological; the latest approximately 20% of orders form the untouched test period.",
        "",
        f"- Training orders: {len(train):,}",
        f"- Test orders: {len(test):,}",
        f"- Training period ends: {train['order_date'].max()}",
        f"- Test period begins: {test['order_date'].min()}",
        f"- Test late rate: {test[target].mean():.2%}",
        "",
        "## Results",
        "",
        "| Model | ROC-AUC | PR-AUC | Brier | Top-decile late rate | Late orders captured |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in evaluation.itertuples(index=False):
        report.append(
            f"| {row.model} | {row.roc_auc:.3f} | {row.pr_auc:.3f} | "
            f"{row.brier_score:.3f} | {row.top_decile_late_rate:.2%} | "
            f"{row.top_decile_late_capture:.2%} |"
        )
    report.extend(
        [
            "",
            "## Shipping-promise sensitivity",
            "",
            f"The best operational model exceeds the best stress-test model by {auc_gap:.3f} ROC-AUC. Shipping mode and scheduled days were removed together because they are perfectly redundant in this dataset and scheduled days are part of the target definition.",
            "",
            "Actual shipping days, shipping date, delivery status, the supplied late flag, and financial outcomes were excluded from all model inputs.",
            "",
        ]
    )
    (DOCS_DIR / "model_evaluation.md").write_text("\n".join(report), encoding="utf-8")
    print(evaluation.to_string(index=False))
    print("Delivery model artifacts, scores, and evaluation report created.")
    return evaluation


if __name__ == "__main__":
    run_delivery_model()
