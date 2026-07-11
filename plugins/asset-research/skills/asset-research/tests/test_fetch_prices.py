import fetch_prices


def test_to_stooq_symbol_japan():
    assert fetch_prices.to_stooq_symbol("7203.T") == "7203.jp"


def test_to_stooq_symbol_us():
    assert fetch_prices.to_stooq_symbol("AAPL") == "aapl.us"


def test_build_price_report_matching_sources(monkeypatch):
    monkeypatch.setattr(fetch_prices, "fetch_yfinance_close", lambda t, p: (100.0, 99.0, [99.0, 100.0]))
    monkeypatch.setattr(fetch_prices, "fetch_stooq_close", lambda t: 100.2)
    report = fetch_prices.build_price_report("7203.T", "1y")
    assert report["flag"] is None
    assert report["reconciled_value"] == 100.0


def test_build_price_report_mismatch(monkeypatch):
    monkeypatch.setattr(fetch_prices, "fetch_yfinance_close", lambda t, p: (100.0, 99.0, [99.0, 100.0]))
    monkeypatch.setattr(fetch_prices, "fetch_stooq_close", lambda t: 150.0)
    report = fetch_prices.build_price_report("7203.T", "1y")
    assert report["flag"] == "PRICE_MISMATCH"


def test_build_price_report_corporate_action(monkeypatch):
    monkeypatch.setattr(fetch_prices, "fetch_yfinance_close", lambda t, p: (50.0, 100.0, [100.0, 50.0]))
    monkeypatch.setattr(fetch_prices, "fetch_stooq_close", lambda t: 50.0)
    report = fetch_prices.build_price_report("7203.T", "1y")
    assert report["corporate_action"] == "CORPORATE_ACTION"


def test_render_report_mismatch_message():
    report = {"ticker": "7203.T", "flag": "PRICE_MISMATCH", "yfinance_close": 100.0,
              "stooq_close": 150.0, "corporate_action": None, "reconciled_value": None,
              "retrieved_at": "x"}
    text = fetch_prices.render_report(report)
    assert "PRICE_MISMATCH" in text
