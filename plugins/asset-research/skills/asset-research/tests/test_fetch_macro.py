import fetch_macro


def test_fetch_fred_datapoint_success(monkeypatch):
    def fake_json(url, timeout=30):
        return {
            "observations": [
                {"date": "2026-07-10", "value": "4.5"},
                {"date": "2026-06-10", "value": "4.2"},
            ]
        }

    monkeypatch.setattr(fetch_macro, "http_get_json", fake_json)
    dp = fetch_macro.fetch_fred_datapoint("DGS10", "米10年国債利回り", "%", "fake_key")
    assert dp.failed is False
    assert "4.5" in dp.value
    assert dp.as_of == "2026-07-10"


def test_fetch_fred_datapoint_no_observations(monkeypatch):
    monkeypatch.setattr(fetch_macro, "http_get_json", lambda url, timeout=30: {"observations": []})
    dp = fetch_macro.fetch_fred_datapoint("DGS10", "米10年国債利回り", "%", "fake_key")
    assert dp.failed is True


def test_fetch_fred_datapoint_network_error(monkeypatch):
    def raise_error(url, timeout=30):
        raise ConnectionError("boom")

    monkeypatch.setattr(fetch_macro, "http_get_json", raise_error)
    dp = fetch_macro.fetch_fred_datapoint("DGS10", "米10年国債利回り", "%", "fake_key")
    assert dp.failed is True
    assert "boom" in dp.fail_reason


def test_build_dashboard_without_keys(monkeypatch):
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    monkeypatch.delenv("ESTAT_APP_ID", raising=False)
    points = fetch_macro.build_dashboard()
    assert all(p.failed for p in points)
    assert len(points) == len(fetch_macro.FRED_SERIES) + len(fetch_macro.ESTAT_SERIES)
