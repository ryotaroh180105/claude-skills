import os

import yaml

from journal import close_entry, list_due_for_review, next_id, parse_journal_file
from datetime import datetime, timezone

ENTRY = {
    "id": "J-001",
    "date": "2026-07-01",
    "type": "buy",
    "target": "7203.T",
    "size_pct": 5,
    "thesis": "test thesis",
    "expected": "test expected",
    "falsifier": "test falsifier",
    "ips_check": "pass",
    "review_date": "2026-07-10",
    "status": "open",
}


def write_entry(tmp_path, entry_id, overrides=None):
    data = dict(ENTRY)
    data["id"] = entry_id
    if overrides:
        data.update(overrides)
    path = tmp_path / f"{entry_id}-test.md"
    path.write_text("---\n" + yaml.safe_dump(data, allow_unicode=True) + "---\nbody\n", encoding="utf-8")
    return str(path)


def test_next_id_empty_dir(tmp_path):
    assert next_id(str(tmp_path)) == "J-001"


def test_next_id_increments(tmp_path):
    write_entry(tmp_path, "J-001")
    write_entry(tmp_path, "J-002")
    assert next_id(str(tmp_path)) == "J-003"


def test_list_due_for_review(tmp_path):
    write_entry(tmp_path, "J-001", {"review_date": "2026-07-01"})
    write_entry(tmp_path, "J-002", {"review_date": "2026-12-01"})
    today = datetime(2026, 7, 15, tzinfo=timezone.utc)
    due = list_due_for_review(str(tmp_path), today)
    assert len(due) == 1
    assert due[0]["id"] == "J-001"


def test_list_due_excludes_closed(tmp_path):
    write_entry(tmp_path, "J-001", {"review_date": "2026-07-01", "status": "closed"})
    today = datetime(2026, 7, 15, tzinfo=timezone.utc)
    due = list_due_for_review(str(tmp_path), today)
    assert due == []


def test_close_entry(tmp_path):
    path = write_entry(tmp_path, "J-001")
    close_entry(path, "期待通り")
    fm = parse_journal_file(path)
    assert fm["status"] == "closed"
    assert fm["outcome"] == "期待通り"
