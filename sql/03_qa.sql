-- Each query should return zero rows unless the comment documents an expected exception.

-- Grain: source order-item key must be unique.
SELECT order_item_id, COUNT(*) AS row_count
FROM stg_order_items
GROUP BY order_item_id
HAVING COUNT(*) <> 1;

-- Grain: fact_orders must contain one row per eligible source order.
SELECT order_id, COUNT(*) AS row_count
FROM fact_orders
GROUP BY order_id
HAVING COUNT(*) <> 1;

-- Impossible chronology.
SELECT order_item_id, order_date_dateorders, shipping_date_dateorders
FROM stg_order_items
WHERE datetime(shipping_date_dateorders) < datetime(order_date_dateorders);

-- Impossible negative durations.
SELECT order_item_id, days_for_shipping_real, days_for_shipment_scheduled
FROM stg_order_items
WHERE days_for_shipping_real < 0
   OR days_for_shipment_scheduled < 0;

-- Zero or negative commercial values among eligible rows.
SELECT order_item_id, unit_list_price, quantity, gross_sales
FROM analysis_order_items
WHERE unit_list_price <= 0
   OR quantity <= 0
   OR gross_sales <= 0;

-- Negative profit is a business condition, not automatically a data error.
-- This query intentionally returns rows for analysis.
SELECT order_item_id, order_id, category_name, discount_rate, net_sales, profit
FROM analysis_order_items
WHERE profit < 0;

-- Late-target agreement must be exact after excluded statuses are removed.
SELECT order_item_id, source_late_flag, calculated_late_flag
FROM analysis_order_items
WHERE source_late_flag <> calculated_late_flag;

-- Order-constant fields should not vary across the same order.
SELECT
    order_id,
    COUNT(DISTINCT order_date_dateorders) AS order_dates,
    COUNT(DISTINCT order_status) AS statuses,
    COUNT(DISTINCT shipping_mode) AS shipping_modes,
    COUNT(DISTINCT days_for_shipment_scheduled) AS scheduled_day_values,
    COUNT(DISTINCT days_for_shipping_real) AS actual_day_values
FROM stg_order_items
GROUP BY order_id
HAVING order_dates <> 1
    OR statuses <> 1
    OR shipping_modes <> 1
    OR scheduled_day_values <> 1
    OR actual_day_values <> 1;

-- Exact duplicate source measures should remain equal.
SELECT order_item_id
FROM stg_order_items
WHERE ABS(benefit_per_order - order_profit_per_order) > 0.000001
   OR ABS(sales_per_customer - order_item_total) > 0.000001
   OR ABS(product_price - order_item_product_price) > 0.000001;

-- Machine-readable QA summary consumed by src/run_qa.py.
DROP VIEW IF EXISTS qa_summary;

CREATE VIEW qa_summary AS
SELECT
    'duplicate_order_item_ids' AS check_name,
    'error' AS severity,
    COUNT(*) AS issue_count
FROM (
    SELECT order_item_id
    FROM stg_order_items
    GROUP BY order_item_id
    HAVING COUNT(*) <> 1
)
UNION ALL
SELECT
    'duplicate_fact_order_ids',
    'error',
    COUNT(*)
FROM (
    SELECT order_id
    FROM fact_orders
    GROUP BY order_id
    HAVING COUNT(*) <> 1
)
UNION ALL
SELECT
    'shipping_before_order',
    'error',
    COUNT(*)
FROM stg_order_items
WHERE datetime(shipping_date_dateorders) < datetime(order_date_dateorders)
UNION ALL
SELECT
    'negative_shipping_duration',
    'error',
    COUNT(*)
FROM stg_order_items
WHERE days_for_shipping_real < 0
   OR days_for_shipment_scheduled < 0
UNION ALL
SELECT
    'nonpositive_price_quantity_or_sales',
    'error',
    COUNT(*)
FROM analysis_order_items
WHERE unit_list_price <= 0
   OR quantity <= 0
   OR gross_sales <= 0
UNION ALL
SELECT
    'eligible_late_label_disagreement',
    'error',
    COUNT(*)
FROM analysis_order_items
WHERE source_late_flag <> calculated_late_flag
UNION ALL
SELECT
    'order_constant_field_variation',
    'error',
    COUNT(*)
FROM (
    SELECT order_id
    FROM stg_order_items
    GROUP BY order_id
    HAVING COUNT(DISTINCT order_date_dateorders) <> 1
        OR COUNT(DISTINCT order_status) <> 1
        OR COUNT(DISTINCT shipping_mode) <> 1
        OR COUNT(DISTINCT days_for_shipment_scheduled) <> 1
        OR COUNT(DISTINCT days_for_shipping_real) <> 1
)
UNION ALL
SELECT
    'duplicate_measure_disagreement',
    'error',
    COUNT(*)
FROM stg_order_items
WHERE ABS(benefit_per_order - order_profit_per_order) > 0.000001
   OR ABS(sales_per_customer - order_item_total) > 0.000001
   OR ABS(product_price - order_item_product_price) > 0.000001
UNION ALL
SELECT
    'negative_profit_items',
    'business_condition',
    COUNT(*)
FROM analysis_order_items
WHERE profit < 0;

