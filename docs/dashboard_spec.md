# Power BI dashboard specification

All dashboard inputs are generated in `data/exports/`. They omit direct customer identifiers and precise location fields.

## Page 1 — Overview

- KPI cards: distinct orders, net sales, profit, weighted margin, late rate
- Monthly net-sales and profit trend
- Monthly late-rate trend
- Current versus feasible shipping-promise days and historical on-time rate
- Slicers: order date, region, category, shipping mode

Primary inputs: `overview_monthly.csv`, `risk_ranked_orders.csv`, `margin_by_dimension.csv`, and `promise_feasibility.csv`.

## Page 2 — Pricing and margin

- Weighted margin by category
- Weighted margin by region
- Discount rate versus weighted margin and negative-profit rate
- Discount-cap scenario table
- Tooltip explaining that cap results hold volume and costs constant

Primary inputs: `margin_by_dimension.csv`, `discount_summary.csv`, `category_discount_summary.csv`, and `discount_cap_scenarios.csv`.

## Page 3 — Action grid

- Category-region matrix colored by profit exposure
- Action slicer or legend
- Risk-ranked order table with order ID, date, category, region, mode, predicted risk, profit at stake, and profit exposure
- Forecast comparison for the four selected categories
- Contact-budget curve showing late-order capture and precision

Primary inputs: `action_grid.csv`, `risk_ranked_orders.csv`, `weekly_forecast_backtest.csv`, and `risk_contact_tradeoff.csv`.

## Semantic definitions

- Weighted margin = total profit / total net sales
- Late rate = late orders / eligible orders
- Profit exposure = predicted late probability × positive order profit
- Forecast WAPE = sum absolute error / sum actual units

