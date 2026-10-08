from src.data_utils import normalize_column_name, normalize_columns


def test_normalize_column_name() -> None:
    assert normalize_column_name("order date (DateOrders)") == "order_date_dateorders"
    assert normalize_column_name("Order Item Discount Rate") == "order_item_discount_rate"


def test_normalize_columns_rejects_collisions() -> None:
    try:
        normalize_columns(["A B", "A-B"])
    except ValueError as error:
        assert "duplicate" in str(error).lower()
    else:
        raise AssertionError("Expected a normalized-column collision.")

