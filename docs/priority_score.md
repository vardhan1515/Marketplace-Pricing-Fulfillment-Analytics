# Priority score and action rules

## Formula

At order level:

```text
profit_exposure = predicted_late_probability × max(order_profit, 0)
```

At category-region level, the score is the sum of order-level profit exposure. It is a prioritization index measured in risk-weighted profit dollars, not an estimate of loss caused by lateness.

## Deterministic action rules

Cells with fewer than 20 test orders default to Monitor. Among sufficiently supported cells:

1. **Reprice or cap discounts:** negative margin, or both bottom-quartile margin and top-quartile negative-profit rate.
2. **Change shipping mode:** top-quartile predicted late risk, after applying the pricing rule.
3. **Add capacity (validate):** at least median risk and top-quartile order volume, after the prior rules.
4. **Monitor:** all remaining cells.

The capacity action is a hypothesis requiring external capacity data; this dataset contains no direct capacity measure.

## Generated action counts

- Monitor: 115 cells
- Change shipping mode: 26 cells
- Reprice or cap discounts: 24 cells
- Add capacity (validate): 10 cells
