# Delivery-risk model evaluation

The target is calculated only for eligible orders as actual shipping days greater than scheduled shipping days. The split is chronological; the latest approximately 20% of orders form the untouched test period.

- Training orders: 50,317
- Test orders: 12,580
- Training period ends: 2017-07-10 00:17:00
- Test period begins: 2017-07-10 00:38:00
- Test late rate: 57.45%

## Results

| Model | ROC-AUC | PR-AUC | Brier | Top-decile late rate | Late orders captured |
|---|---:|---:|---:|---:|---:|
| operational__logistic_regression | 0.746 | 0.837 | 0.192 | 100.00% | 17.41% |
| operational__random_forest | 0.739 | 0.833 | 0.192 | 100.00% | 17.41% |
| stress_test_without_shipping_promise__random_forest | 0.509 | 0.580 | 0.249 | 58.43% | 10.17% |
| stress_test_without_shipping_promise__logistic_regression | 0.500 | 0.571 | 0.251 | 55.01% | 9.58% |

## Shipping-promise sensitivity

The best operational model exceeds the best stress-test model by 0.237 ROC-AUC. Shipping mode and scheduled days were removed together because they are perfectly redundant in this dataset and scheduled days are part of the target definition.

Actual shipping days, shipping date, delivery status, the supplied late flag, and financial outcomes were excluded from all model inputs.
