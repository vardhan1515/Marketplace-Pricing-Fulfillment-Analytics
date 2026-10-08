import pandas as pd

from src.delivery_diagnostics import _prior_seven_day_count


def test_prior_seven_day_count_uses_only_strictly_earlier_orders() -> None:
    frame = pd.DataFrame(
        {
            "order_id": [1, 2, 3, 4],
            "order_date": pd.to_datetime(
                [
                    "2020-01-01 10:00",
                    "2020-01-01 10:00",
                    "2020-01-05 10:00",
                    "2020-01-10 10:00",
                ]
            ),
            "order_region": ["A", "A", "A", "A"],
        }
    )
    counts = _prior_seven_day_count(frame, "order_region")
    assert counts.tolist() == [0, 0, 2, 1]

