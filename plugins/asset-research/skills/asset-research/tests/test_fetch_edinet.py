import fetch_edinet


def test_search_documents_found_first_day(monkeypatch):
    def fake_json(url):
        return {"results": [{"edinetCode": "E02144", "docID": "S100ABCD",
                              "docDescription": "有価証券報告書",
                              "submitDateTime": "2026-07-01 09:00",
                              "filerName": "テスト株式会社"}]}

    monkeypatch.setattr(fetch_edinet, "http_get_json", fake_json)
    docs = fetch_edinet.search_documents("E02144", "fake_key", days_back=5)
    assert len(docs) == 1
    assert docs[0]["docID"] == "S100ABCD"


def test_search_documents_no_match(monkeypatch):
    monkeypatch.setattr(fetch_edinet, "http_get_json", lambda url: {"results": []})
    docs = fetch_edinet.search_documents("E99999", "fake_key", days_back=3)
    assert docs == []


def test_build_report_success(monkeypatch):
    monkeypatch.setattr(
        fetch_edinet, "search_documents",
        lambda code, key, days_back=120: [{"docID": "S100X", "docDescription": "四半期報告書",
                                            "submitDateTime": "2026-07-01", "filerName": "テスト社"}],
    )
    report = fetch_edinet.build_report("E02144", "fake_key")
    assert report["failed"] is False
    assert report["doc_id"] == "S100X"


def test_build_report_no_documents(monkeypatch):
    monkeypatch.setattr(fetch_edinet, "search_documents", lambda code, key, days_back=120: [])
    report = fetch_edinet.build_report("E02144", "fake_key")
    assert report["failed"] is True


def test_parse_financial_csv():
    header = "要素ID\tコンテキストID\t値\t単位\n"
    row = "jppfs_cor:NetSales\tCurrentYearDuration_ConsolidatedMember\t1000000\t円\n"
    csv_bytes = (header + row).encode("utf-16")
    result = fetch_edinet.parse_financial_csv(csv_bytes)
    assert "売上高" in result
    assert result["売上高"]["value"] == "1000000"
    assert result["売上高"]["consolidated"] is True
