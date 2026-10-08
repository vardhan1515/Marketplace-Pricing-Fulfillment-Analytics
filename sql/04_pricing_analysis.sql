DROP VIEW IF EXISTS margin_by_dimension;

CREATE VIEW margin_by_dimension AS
SELECT
    'category' AS dimension,
    category_name AS segment,
    COUNT(*) AS item_count,
    COUNT(DISTINCT order_id) AS order_count,
    SUM(quantity) AS units,
    SUM(net_sales) AS net_sales,
    SUM(profit) AS profit,
    SUM(profit) / NULLIF(SUM(net_sales), 0) AS weighted_margin,
    AVG(CASE WHEN profit < 0 THEN 1.0 ELSE 0.0 END) AS negative_profit_item_rate
FROM analysis_order_items
GROUP BY category_name
UNION ALL
SELECT
    'region', order_region, COUNT(*), COUNT(DISTINCT order_id), SUM(quantity),
    SUM(net_sales), SUM(profit),
    SUM(profit) / NULLIF(SUM(net_sales), 0),
    AVG(CASE WHEN profit < 0 THEN 1.0 ELSE 0.0 END)
FROM analysis_order_items
GROUP BY order_region
UNION ALL
SELECT
    'shipping_mode', shipping_mode, COUNT(*), COUNT(DISTINCT order_id), SUM(quantity),
    SUM(net_sales), SUM(profit),
    SUM(profit) / NULLIF(SUM(net_sales), 0),
    AVG(CASE WHEN profit < 0 THEN 1.0 ELSE 0.0 END)
FROM analysis_order_items
GROUP BY shipping_mode;

DROP VIEW IF EXISTS discount_summary;

CREATE VIEW discount_summary AS
SELECT
    ROUND(discount_rate, 4) AS discount_rate,
    COUNT(*) AS item_count,
    COUNT(DISTINCT order_id) AS order_count,
    SUM(gross_sales) AS gross_sales,
    SUM(discount_amount) AS discount_amount,
    SUM(net_sales) AS net_sales,
    SUM(profit) AS profit,
    SUM(profit) / NULLIF(SUM(net_sales), 0) AS weighted_margin,
    AVG(CASE WHEN profit < 0 THEN 1.0 ELSE 0.0 END) AS negative_profit_item_rate
FROM analysis_order_items
GROUP BY ROUND(discount_rate, 4);

DROP VIEW IF EXISTS category_discount_summary;

CREATE VIEW category_discount_summary AS
SELECT
    category_name,
    ROUND(discount_rate, 4) AS discount_rate,
    COUNT(*) AS item_count,
    COUNT(DISTINCT order_id) AS order_count,
    SUM(net_sales) AS net_sales,
    SUM(profit) AS profit,
    SUM(profit) / NULLIF(SUM(net_sales), 0) AS weighted_margin,
    AVG(CASE WHEN profit < 0 THEN 1.0 ELSE 0.0 END) AS negative_profit_item_rate
FROM analysis_order_items
GROUP BY category_name, ROUND(discount_rate, 4);

