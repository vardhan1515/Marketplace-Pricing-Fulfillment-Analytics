# Delivery diagnostics and promise feasibility

All features are available at order time. Prior-seven-day load counts use strictly earlier timestamps, excluding simultaneous and future orders.

## Global classification

| Model | ROC-AUC | PR-AUC | Brier | Top-decile lift |
|---|---:|---:|---:|---:|
| enriched_operational__random_forest | 0.773 | 0.855 | 0.178 | 1.74x |
| enriched_operational__logistic_regression | 0.748 | 0.839 | 0.195 | 1.74x |
| shipping_mode_only_rule | 0.744 | 0.786 | 0.188 | 1.74x |
| enriched_without_shipping_promise__random_forest | 0.522 | 0.592 | 0.247 | 1.06x |
| enriched_without_shipping_promise__logistic_regression | 0.522 | 0.590 | 0.249 | 1.03x |

The best enriched operational model has ROC-AUC 0.773; the best enriched model without shipping-promise fields has ROC-AUC 0.522.

## Within-mode classification

| Mode | Model | Orders | Late rate | ROC-AUC | PR-AUC | Top-decile lift |
|---|---|---:|---:|---:|---:|---:|
| Same Day | global__enriched_operational__random_forest | 702 | 53.28% | 1.000 | 1.000 | 1.88x |
| Same Day | mode_specific__random_forest | 702 | 53.28% | 1.000 | 1.000 | 1.88x |
| Same Day | mode_specific__logistic_regression | 702 | 53.28% | 1.000 | 1.000 | 1.88x |
| Same Day | global__enriched_without_shipping_promise__random_forest | 702 | 53.28% | 0.873 | 0.884 | 1.82x |
| Second Class | global__enriched_without_shipping_promise__random_forest | 2,470 | 80.24% | 0.508 | 0.808 | 1.01x |
| Second Class | mode_specific__logistic_regression | 2,470 | 80.24% | 0.487 | 0.792 | 0.94x |
| Second Class | mode_specific__random_forest | 2,470 | 80.24% | 0.483 | 0.794 | 0.98x |
| Second Class | global__enriched_operational__random_forest | 2,470 | 80.24% | 0.483 | 0.795 | 1.01x |
| Standard Class | mode_specific__random_forest | 7,508 | 39.57% | 0.500 | 0.398 | 1.00x |
| Standard Class | mode_specific__logistic_regression | 7,508 | 39.57% | 0.499 | 0.396 | 0.98x |
| Standard Class | global__enriched_without_shipping_promise__random_forest | 7,508 | 39.57% | 0.498 | 0.394 | 0.99x |
| Standard Class | global__enriched_operational__random_forest | 7,508 | 39.57% | 0.496 | 0.396 | 0.96x |

First Class is omitted from within-mode AUC because every eligible First Class order is late.

Same Day is the exception: order hour perfectly separates the source outcome in the test period. Orders before noon have zero actual shipping days; orders from noon onward have one. Order hour is available at placement, so this is not leakage, but the perfect cutoff is likely a data-generation rule and requires validation on operational data.

## Delay-days regression

| Model | MAE days | RMSE days | R² |
|---|---:|---:|---:|
| enriched_operational | 0.976 | 1.272 | 0.281 |
| shipping_mode_mean_rule | 0.984 | 1.269 | 0.284 |
| enriched_without_shipping_promise | 1.206 | 1.507 | -0.009 |

## Calibration and intervention workload

- Best operational expected calibration error: 3.58%
- Best no-promise expected calibration error: 4.66%

| Model | Contacted | Orders contacted | Late capture | Contact precision |
|---|---:|---:|---:|---:|
| enriched_operational__random_forest | 5% | 629 | 8.70% | 100.00% |
| enriched_operational__random_forest | 10% | 1,258 | 17.41% | 100.00% |
| enriched_operational__random_forest | 20% | 2,516 | 33.82% | 97.14% |
| enriched_operational__random_forest | 30% | 3,774 | 47.99% | 91.89% |
| enriched_operational__random_forest | 40% | 5,032 | 60.55% | 86.96% |
| enriched_operational__random_forest | 50% | 6,290 | 67.46% | 77.50% |
| enriched_without_shipping_promise__random_forest | 5% | 629 | 5.15% | 59.14% |
| enriched_without_shipping_promise__random_forest | 10% | 1,258 | 10.59% | 60.81% |
| enriched_without_shipping_promise__random_forest | 20% | 2,516 | 20.95% | 60.17% |
| enriched_without_shipping_promise__random_forest | 30% | 3,774 | 31.37% | 60.07% |
| enriched_without_shipping_promise__random_forest | 40% | 5,032 | 41.44% | 59.52% |
| enriched_without_shipping_promise__random_forest | 50% | 6,290 | 51.43% | 59.09% |

## Promise feasibility

| Mode | Current promise | Current on-time | P80 actual | P90 actual | P95 actual | Promise for 90% | Resulting on-time |
|---|---:|---:|---:|---:|---:|---:|---:|
| First Class | 1 days | 0.00% | 2.0 | 2.0 | 2.0 | 2 days | 100.00% |
| Same Day | 0 days | 51.63% | 1.0 | 1.0 | 1.0 | 1 days | 100.00% |
| Second Class | 2 days | 20.01% | 6.0 | 6.0 | 6.0 | 6 days | 100.00% |
| Standard Class | 4 days | 60.15% | 6.0 | 6.0 | 6.0 | 6 days | 100.00% |

The promise scenarios are descriptive feasibility calculations, not forecasts of how operations or customers would respond to changed promises.
