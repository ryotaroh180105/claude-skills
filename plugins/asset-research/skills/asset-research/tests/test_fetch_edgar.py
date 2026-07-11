import fetch_edgar


def test_get_latest_filing_found(monkeypatch):
    def fake_json(url):
        return {
            "name": "Apple Inc.",
            "filings": {
                "recent": {
                    "form": ["8-K", "10-K", "10-Q"],
                    "filingDate": ["2026-05-01", "2026-03-01", "2026-01-01"],
                    "accessionNumber": ["a", "b", "c"],
                }
            },
        }

    monkeypatch.setattr(fetch_edgar, "http_get_json", fake_json)
    report = fetch_edgar.get_latest_filing("320193")
    assert report["failed"] is False
    assert report["form"] == "10-K"
    assert report["company_name"] == "Apple Inc."


def test_get_latest_filing_not_found(monkeypatch):
    monkeypatch.setattr(
        fetch_edgar, "http_get_json",
        lambda url: {"name": "X", "filings": {"recent": {"form": ["8-K"], "filingDate": ["2026-01-01"], "accessionNumber": ["a"]}}},
    )
    report = fetch_edgar.get_latest_filing("320193")
    assert report["failed"] is True


def test_get_company_concept_success(monkeypatch):
    def fake_json(url):
        return {"units": {"USD": [
            {"end": "2025-12-31", "val": 100, "form": "10-K"},
            {"end": "2026-03-31", "val": 120, "form": "10-Q"},
        ]}}

    monkeypatch.setattr(fetch_edgar, "http_get_json", fake_json)
    report = fetch_edgar.get_company_concept("320193", "Revenues")
    assert report["failed"] is False
    assert report["value"] == 120
    assert report["period_end"] == "2026-03-31"


def test_normalize_cik():
    assert fetch_edgar.normalize_cik("320193") == "0000320193"
