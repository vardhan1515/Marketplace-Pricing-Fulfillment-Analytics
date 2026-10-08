# Methodology and analysis decisions

## Data grain

The raw dataset contains one row per order item. The pipeline preserves this grain for pricing, margin, category, and demand work. It also creates one row per order for delivery-risk modeling.

Because an order can contain multiple categories, `primary_category` is the category with the greatest net sales within the order. Ties are resolved alphabetically for deterministic output. `category_count` preserves information about mixed-category orders.

## Transaction eligibility

Rows with `Order Status` equal to `CANCELED` or `SUSPECTED_FRAUD` remain in staging for auditability but are excluded from:

- realized sales and profit KPIs;
- late-delivery model training and evaluation;
- demand forecasting; and
- discount-policy simulation.

These records must not be interpreted as on-time deliveries because the supplied late flag is forced to zero for them.

## Canonical financial fields

The source contains exact duplicate measures. The analytical layer uses:

- `order_item_total` as net sales instead of `sales_per_customer`;
- `order_profit_per_order` as item-level profit instead of `benefit_per_order`; and
- `order_item_product_price` as unit list price instead of `product_price`.

Despite its source name, `order_profit_per_order` varies by item within most multi-item orders and is summed when building the order table.

Weighted margin is calculated as total profit divided by total net sales. Row-level ratios are not averaged.

## Late-delivery target

For eligible orders:

```text
calculated_late_flag = 1 when actual_shipping_days > scheduled_shipping_days, otherwise 0
```

The operational model will contain only fields available at order time. Actual shipping days, shipping date, delivery status, and the supplied late flag are excluded from model inputs.

`Shipping Mode` maps exactly to scheduled shipping days in this dataset. Results will therefore be reported for:

1. an operational model containing shipping mode and scheduled days; and
2. a stress-test model excluding both fields.

The enhanced diagnostic model also uses order weekday, hour, month, a year-end holiday-window flag, items per order, multi-category status, department, market, customer segment, and prior-seven-day order counts for the same region and primary category. Historical-load counts use strictly earlier timestamps; simultaneous and future orders are excluded.

Models are compared against a shipping-mode-only rule. Performance is also reported within each shipping mode, with calibration and contact-budget diagnostics. A separate regression predicts actual minus scheduled shipping days, and a promise-feasibility table reports historical on-time rates under alternative promised-day thresholds.

## Privacy

Analytical exports omit names, email, password, street, ZIP code, and exact coordinates. Anonymous IDs are retained only when necessary for grain and QA.

## Causal limitations

Price sensitivity, shipping-mode comparisons, and discount-cap results are observational. A fixed-volume discount-cap calculation is an accounting scenario and not a forecast of customer response.

