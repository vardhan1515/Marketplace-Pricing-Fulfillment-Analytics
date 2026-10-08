# Management memo: pricing and fulfillment priorities

## Decision 1 — Audit shipping promises before deploying the risk model

Late delivery affects 57.45% of the chronological test orders. The enriched operational model achieves 0.773 ROC-AUC, compared with 0.744 for a shipping-mode-only rule, and every order in its highest-risk decile is late. Removing shipping mode and scheduled days reduces the best ROC-AUC to 0.522. Within-mode AUC is approximately 0.50 for Standard and Second Class, confirming that broad order characteristics add little signal. Same Day is an exception because order hour perfectly separates zero-day from one-day fulfillment in this dataset. Operations should first validate service-level definitions and the Same Day noon cutoff before changing promises or routing policy.

## Decision 2 — Target loss-making items; do not impose a blanket discount cap

Eligible transactions generated $31.64 million in net sales, $3.81 million in profit, and a 12.03% weighted margin. Although 18.69% of order items lose money, none of the observed overall discount bands has a negative weighted margin. A fixed-volume 20% cap produces an accounting increase of $87,954 across 19,202 affected items, but this excludes customer demand response. Use the category-level loss rate and margin grid to select a small cap pilot; do not treat the scenario as a causal profit forecast.

## Decision 3 — Use category-specific short-horizon forecasting rules

No single forecasting method wins across all four high-volume categories. The lag model produces the lowest WAPE for Cleats (5.06%) and Women's Apparel (7.34%), while the four-week moving average wins for Cardio Equipment (6.83%) and Indoor/Outdoor Games (8.79%). Planning should use the winning validated method by category and refresh weekly. Capacity recommendations remain provisional because the dataset contains no direct inventory or capacity fields.

## Guardrails

The data ends in early 2018 and may be synthetic or simulated. It contains no competitor prices, reviews, inventory, capacity, or measured financial cost of lateness. Results should be treated as analytical evidence for testing, not production policy.

