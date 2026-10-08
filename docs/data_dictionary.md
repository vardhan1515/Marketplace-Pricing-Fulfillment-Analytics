# Data dictionary and source profile

Generated from the local raw CSV by `python -m src.profile_data`.

## Source profile

- Rows: 180,519
- Columns: 53
- Distinct orders: 65,752
- Distinct order items: 180,519
- Exact duplicate rows: 0
- Order dates: 2015-01-01T00:00:00 through 2018-01-31T23:38:00
- Shipping dates: 2015-01-03T00:00:00 through 2018-02-06T22:14:00
- Canceled/suspected-fraud item rows: 7,754
- Canceled/suspected-fraud orders: 2,855
- Source/calculated late-label disagreements: 4,423
- Late-label disagreements among eligible orders: 0
- SHA-256: `fa6d022ed437155e1a2f0378710602848703c8a7f203f7ff5d77805bf8480aa6`

## Fields

| Normalized field | Inferred type | Nulls | Null % | Distinct non-null |
|---|---:|---:|---:|---:|
| `type` | object | 0 | 0.0000% | 4 |
| `days_for_shipping_real` | int64 | 0 | 0.0000% | 7 |
| `days_for_shipment_scheduled` | int64 | 0 | 0.0000% | 4 |
| `benefit_per_order` | float64 | 0 | 0.0000% | 21,998 |
| `sales_per_customer` | float64 | 0 | 0.0000% | 2,927 |
| `delivery_status` | object | 0 | 0.0000% | 4 |
| `late_delivery_risk` | int64 | 0 | 0.0000% | 2 |
| `category_id` | int64 | 0 | 0.0000% | 51 |
| `category_name` | object | 0 | 0.0000% | 50 |
| `customer_city` | object | 0 | 0.0000% | 563 |
| `customer_country` | object | 0 | 0.0000% | 2 |
| `customer_email` | object | 0 | 0.0000% | 1 |
| `customer_fname` | object | 0 | 0.0000% | 782 |
| `customer_id` | int64 | 0 | 0.0000% | 20,652 |
| `customer_lname` | object | 8 | 0.0044% | 1,109 |
| `customer_password` | object | 0 | 0.0000% | 1 |
| `customer_segment` | object | 0 | 0.0000% | 3 |
| `customer_state` | object | 0 | 0.0000% | 46 |
| `customer_street` | object | 0 | 0.0000% | 7,458 |
| `customer_zipcode` | float64 | 3 | 0.0017% | 995 |
| `department_id` | int64 | 0 | 0.0000% | 11 |
| `department_name` | object | 0 | 0.0000% | 11 |
| `latitude` | float64 | 0 | 0.0000% | 11,250 |
| `longitude` | float64 | 0 | 0.0000% | 4,487 |
| `market` | object | 0 | 0.0000% | 5 |
| `order_city` | object | 0 | 0.0000% | 3,597 |
| `order_country` | object | 0 | 0.0000% | 164 |
| `order_customer_id` | int64 | 0 | 0.0000% | 20,652 |
| `order_date_dateorders` | datetime64[ns] | 0 | 0.0000% | 65,752 |
| `order_id` | int64 | 0 | 0.0000% | 65,752 |
| `order_item_cardprod_id` | int64 | 0 | 0.0000% | 118 |
| `order_item_discount` | float64 | 0 | 0.0000% | 1,017 |
| `order_item_discount_rate` | float64 | 0 | 0.0000% | 18 |
| `order_item_id` | int64 | 0 | 0.0000% | 180,519 |
| `order_item_product_price` | float64 | 0 | 0.0000% | 75 |
| `order_item_profit_ratio` | float64 | 0 | 0.0000% | 162 |
| `order_item_quantity` | int64 | 0 | 0.0000% | 5 |
| `sales` | float64 | 0 | 0.0000% | 193 |
| `order_item_total` | float64 | 0 | 0.0000% | 2,927 |
| `order_profit_per_order` | float64 | 0 | 0.0000% | 21,998 |
| `order_region` | object | 0 | 0.0000% | 23 |
| `order_state` | object | 0 | 0.0000% | 1,089 |
| `order_status` | object | 0 | 0.0000% | 9 |
| `order_zipcode` | float64 | 155,679 | 86.2397% | 609 |
| `product_card_id` | int64 | 0 | 0.0000% | 118 |
| `product_category_id` | int64 | 0 | 0.0000% | 51 |
| `product_description` | float64 | 180,519 | 100.0000% | 0 |
| `product_image` | object | 0 | 0.0000% | 118 |
| `product_name` | object | 0 | 0.0000% | 118 |
| `product_price` | float64 | 0 | 0.0000% | 75 |
| `product_status` | int64 | 0 | 0.0000% | 1 |
| `shipping_date_dateorders` | datetime64[ns] | 0 | 0.0000% | 63,701 |
| `shipping_mode` | object | 0 | 0.0000% | 4 |

## Known source-field relationships

- `benefit_per_order` duplicates `order_profit_per_order`.
- `sales_per_customer` duplicates `order_item_total`.
- `product_price` duplicates `order_item_product_price`.
- `product_description` is entirely null.
- `order_zipcode` is mostly null and is excluded from analytical exports.
