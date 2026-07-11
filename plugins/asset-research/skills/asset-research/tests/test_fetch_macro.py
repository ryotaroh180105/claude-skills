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


def test_fetch_estat_datapoint_picks_max_time_not_last_index(monkeypatch):
    """F3: 返却順が時系列である保証がないため、@time最大（最新）が選ばれることを検証する。"""
    def fake_json(url):
        return {
            "GET_STATS_DATA": {
                "STATISTICAL_DATA": {
                    "DATA_INF": {
                        "VALUE": [
                            {"@time": "2026000201", "$": "1.0"},
                            {"@time": "2026000401", "$": "3.0"},
                            {"@time": "2026000301", "$": "2.0"},
                        ]
                    }
                }
            }
        }

    monkeypatch.setattr(fetch_macro, "http_get_json", fake_json)
    dp = fetch_macro.fetch_estat_datapoint("cpi_jp", "日本CPI総合", "0000020101", "%", "fake_app_id")
    assert dp.value == "3.0"
    assert dp.as_of == "2026000401"


def test_build_dashboard_without_keys(monkeypatch):
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    monkeypatch.delenv("ESTAT_APP_ID", raising=False)
    points = fetch_macro.build_dashboard()
    assert all(p.failed for p in points)
    assert len(points) == len(fetch_macro.FRED_SERIES) + len(fetch_macro.ESTAT_SERIES)
