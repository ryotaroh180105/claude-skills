from datetime import datetime, timezone

from common import detect_corporate_action, is_stale, percentile_position, reconcile_prices


def test_percentile_position_basic():
    assert percentile_position(50, [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]) == 50.0


def test_percentile_position_empty_series():
    assert percentile_position(50, []) is None


def test_reconcile_prices_matching():
    value, flag = reconcile_prices(100.0, 100.5)
    assert value == 100.0
    assert flag is None


def test_reconcile_prices_mismatch():
    value, flag = reconcile_prices(100.0, 120.0)
    assert value is None
    assert flag == "PRICE_MISMATCH"


def test_reconcile_prices_missing_secondary_is_single_source():
    """F5: secondaryが取れない場合（投信等）はprimaryを捨てずSINGLE_SOURCEとして返す。"""
    value, flag = reconcile_prices(100.0, None)
    assert value == 100.0
    assert flag == "SINGLE_SOURCE"


def test_reconcile_prices_missing_primary_is_fetch_failed():
    value, flag = reconcile_prices(None, 100.0)
    assert value is None
    assert flag == "FETCH_FAILED"


def test_detect_corporate_action_split_2_to_1():
    assert detect_corporate_action(200.0, 100.0) == "CORPORATE_ACTION"


def test_detect_corporate_action_normal_move():
    assert detect_corporate_action(100.0, 101.5) is None


def test_is_stale_recent():
    today = datetime(2026, 7, 15, tzinfo=timezone.utc)
    assert is_stale("2026-07-14", today) is False


def test_is_stale_old():
    today = datetime(2026, 7, 15, tzinfo=timezone.utc)
    assert is_stale("2026-06-01", today) is True
