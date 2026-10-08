-- SQLite staging schema for DataCoSupplyChainDataset.csv.
-- The CSV transfer itself is performed by src/load_database.py so encoding,
-- dates, nulls, and data-contract checks are reproducible across platforms.

DROP VIEW IF EXISTS analysis_order_items;
DROP TABLE IF EXISTS fact_orders;
DROP TABLE IF EXISTS stg_order_items;

CREATE TABLE stg_order_items (
    type TEXT,
    days_for_shipping_real INTEGER,
    days_for_shipment_scheduled INTEGER,
    benefit_per_order REAL,
    sales_per_customer REAL,
    delivery_status TEXT,
    late_delivery_risk INTEGER,
    category_id INTEGER,
    category_name TEXT,
    customer_city TEXT,
    customer_country TEXT,
    customer_email TEXT,
    customer_fname TEXT,
    customer_id INTEGER,
    customer_lname TEXT,
    customer_password TEXT,
    customer_segment TEXT,
    customer_state TEXT,
    customer_street TEXT,
    customer_zipcode REAL,
    department_id INTEGER,
    department_name TEXT,
    latitude REAL,
    longitude REAL,
    market TEXT,
    order_city TEXT,
    order_country TEXT,
    order_customer_id INTEGER,
    order_date_dateorders TEXT NOT NULL,
    order_id INTEGER NOT NULL,
    order_item_cardprod_id INTEGER,
    order_item_discount REAL,
    order_item_discount_rate REAL,
    order_item_id INTEGER NOT NULL PRIMARY KEY,
    order_item_product_price REAL,
    order_item_profit_ratio REAL,
    order_item_quantity INTEGER,
    sales REAL,
    order_item_total REAL,
    order_profit_per_order REAL,
    order_region TEXT,
    order_state TEXT,
    order_status TEXT,
    order_zipcode REAL,
    product_card_id INTEGER,
    product_category_id INTEGER,
    product_description TEXT,
    product_image TEXT,
    product_name TEXT,
    product_price REAL,
    product_status INTEGER,
    shipping_date_dateorders TEXT,
    shipping_mode TEXT
);

CREATE INDEX idx_stg_order_items_order_id
    ON stg_order_items (order_id);
CREATE INDEX idx_stg_order_items_order_date
    ON stg_order_items (order_date_dateorders);
CREATE INDEX idx_stg_order_items_category_region
    ON stg_order_items (category_name, order_region);

