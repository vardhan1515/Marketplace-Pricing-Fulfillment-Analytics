# Power BI deliverables

Load the generated CSV files from `data/exports/` and follow `docs/dashboard_spec.md`.

The `.pbix` file is intentionally ignored until the dashboard is built and reviewed. The `screenshots/` directory contains generated dashboard previews based on the same export tables. These previews are visual specifications, not screenshots captured from Power BI Desktop.

Suggested model tables:

- `risk_ranked_orders`
- `overview_monthly`
- `margin_by_dimension`
- `discount_summary`
- `discount_cap_scenarios`
- `action_grid`
- `weekly_forecast_backtest`
- `promise_feasibility`
- `promise_scenarios`
- `within_mode_model_evaluation`
- `model_calibration`
- `risk_contact_tradeoff`

Create measures using `measures.dax`. Keep the Power BI privacy level consistent because all tables are local generated exports.

