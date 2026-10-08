-- Privacy-safe item view for commercial analysis and forecasting.
-- Canceled and suspected-fraud rows remain in staging but are excluded here.

DROP VIEW IF EXISTS analysis_order_items;

CREATE VIEW analysis_order_items AS
SELECT
    order_item_id,
    order_id,
    order_customer_id,
    order_date_dateorders AS order_date,
    shipping_date_dateorders AS shipping_date,
    order_status,
    delivery_status,
    shipping_mode,
    days_for_shipment_scheduled AS scheduled_shipping_days,
    days_for_shipping_real AS actual_shipping_days,
    late_delivery_risk AS source_late_flag,
    CASE
        WHEN days_for_shipping_real > days_for_shipment_scheduled THEN 1
        ELSE 0
    END AS calculated_late_flag,
    category_id,
    category_name,
    department_id,
    department_name,
    product_card_id,
    product_name,
    customer_segment,
    market,
    order_region,
    order_country,
    order_state,
    order_city,
    order_item_quantity AS quantity,
    order_item_product_price AS unit_list_price,
    sales AS gross_sales,
    order_item_discount AS discount_amount,
    order_item_discount_rate AS discount_rate,
    order_item_total AS net_sales,
    order_profit_per_order AS profit
FROM stg_order_items
WHERE order_status NOT IN ('CANCELED', 'SUSPECTED_FRAUD');

DROP TABLE IF EXISTS fact_orders;

CREATE TABLE fact_orders AS
WITH category_totals AS (
    SELECT
        order_id,
        category_name,
        MIN(department_name) AS department_name,
        SUM(order_item_total) AS category_net_sales
    FROM stg_order_items
    WHERE order_status NOT IN ('CANCELED', 'SUSPECTED_FRAUD')
    GROUP BY order_id, category_name
),
ranked_categories AS (
    SELECT
        order_id,
        category_name,
        department_name,
        ROW_NUMBER() OVER (
            PARTITION BY order_id
            ORDER BY category_net_sales DESC, category_name ASC
        ) AS category_rank
    FROM category_totals
),
order_aggregates AS (
    SELECT
        order_id,
        MIN(order_date_dateorders) AS order_date,
        MIN(shipping_date_dateorders) AS shipping_date,
        MIN(order_status) AS order_status,
        MIN(delivery_status) AS delivery_status,
        MIN(shipping_mode) AS shipping_mode,
        MIN(days_for_shipment_scheduled) AS scheduled_shipping_days,
        MIN(days_for_shipping_real) AS actual_shipping_days,
        MIN(late_delivery_risk) AS source_late_flag,
        CASE
            WHEN MIN(days_for_shipping_real) > MIN(days_for_shipment_scheduled) THEN 1
            ELSE 0
        END AS calculated_late_flag,
        MIN(market) AS market,
        MIN(customer_segment) AS customer_segment,
        MIN(order_region) AS order_region,
        MIN(order_country) AS order_country,
        COUNT(DISTINCT category_name) AS category_count,
        COUNT(*) AS item_count,
        SUM(order_item_quantity) AS total_quantity,
        SUM(sales) AS gross_sales,
        SUM(order_item_discount) AS discount_amount,
        SUM(order_item_total) AS net_sales,
        SUM(order_profit_per_order) AS profit
    FROM stg_order_items
    WHERE order_status NOT IN ('CANCELED', 'SUSPECTED_FRAUD')
    GROUP BY order_id
)
SELECT
    orders.order_id,
    orders.order_date,
    orders.shipping_date,
    orders.order_status,
    orders.delivery_status,
    orders.shipping_mode,
    orders.scheduled_shipping_days,
    orders.actual_shipping_days,
    orders.source_late_flag,
    orders.calculated_late_flag,
    orders.market,
    orders.customer_segment,
    orders.order_region,
    orders.order_country,
    orders.category_count,
    primary_category.category_name AS primary_category,
    primary_category.department_name AS primary_department,
    orders.item_count,
    CASE WHEN orders.category_count > 1 THEN 1 ELSE 0 END AS is_multi_category,
    orders.total_quantity,
    orders.gross_sales,
    orders.discount_amount,
    orders.net_sales,
    orders.profit,
    CASE
        WHEN orders.gross_sales = 0 THEN NULL
        ELSE orders.discount_amount / orders.gross_sales
    END AS weighted_discount_rate,
    CASE
        WHEN orders.total_quantity = 0 THEN NULL
        ELSE orders.net_sales / orders.total_quantity
    END AS average_net_unit_price
FROM order_aggregates AS orders
LEFT JOIN ranked_categories AS primary_category
    ON orders.order_id = primary_category.order_id
   AND primary_category.category_rank = 1;

CREATE UNIQUE INDEX idx_fact_orders_order_id
    ON fact_orders (order_id);
CREATE INDEX idx_fact_orders_order_date
    ON fact_orders (order_date);

