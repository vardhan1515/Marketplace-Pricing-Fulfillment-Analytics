# Short-horizon demand forecast evaluation

Demand is weekly units sold, not order-item row count. Four categories were selected by pre-holdout volume after requiring at least 80% active-week coverage and two years of history. Sparse first or last weeks below 25% of the interior median were removed.

The final 12 active weeks of each category are evaluated with rolling one-step features. The lag model uses lags 1, 2, 3, 4, 13, and 52, rolling means, trend, and cyclical month features.

| Category | Method | Test period | WAPE | MAE units |
|---|---|---|---:|---:|
| Cardio Equipment | moving_average_4 | 2017-07-10 to 2017-09-25 | 6.83% | 16.9 |
| Cardio Equipment | lag_feature_model | 2017-07-10 to 2017-09-25 | 6.94% | 17.2 |
| Cardio Equipment | naive_previous_week | 2017-07-10 to 2017-09-25 | 9.42% | 23.3 |
| Cleats | lag_feature_model | 2017-07-10 to 2017-09-25 | 5.06% | 24.6 |
| Cleats | moving_average_4 | 2017-07-10 to 2017-09-25 | 6.40% | 31.1 |
| Cleats | naive_previous_week | 2017-07-10 to 2017-09-25 | 6.72% | 32.6 |
| Indoor/Outdoor Games | moving_average_4 | 2017-07-10 to 2017-09-25 | 8.79% | 31.7 |
| Indoor/Outdoor Games | lag_feature_model | 2017-07-10 to 2017-09-25 | 9.80% | 35.3 |
| Indoor/Outdoor Games | naive_previous_week | 2017-07-10 to 2017-09-25 | 14.21% | 51.2 |
| Women's Apparel | lag_feature_model | 2017-07-10 to 2017-09-25 | 7.34% | 30.7 |
| Women's Apparel | moving_average_4 | 2017-07-10 to 2017-09-25 | 8.54% | 35.8 |
| Women's Apparel | naive_previous_week | 2017-07-10 to 2017-09-25 | 12.13% | 50.8 |

Because category availability changes abruptly in the source data, each category is evaluated on its own last active weeks rather than treating later zero-coverage weeks as genuine zero demand.
