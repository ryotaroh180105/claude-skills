"""意思決定ジャーナルの登録・レビュー抽出・クローズ。docs/designs/23-asset-research-engine.md §5.4。

使い方:
    python journal.py --list-due --journal-dir /path/to/invest-journal/journal --today 2026-07-15
    python journal.py --close J-001 --journal-dir ... --outcome "期待通り、学び: ..."
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys
from datetime import datetime, timezone

import yaml

REQUIRED_JOURNAL_FIELDS = [
    "id", "date", "type", "target", "size_pct", "thesis",
    "expected", "falsifier", "ips_check", "review_date", "status",
]


def parse_journal_file(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        raise ValueError(f"{path}: frontmatterが見つかりません")
    fm = yaml.safe_load(m.group(1)) or {}
    fm["_path"] = path
    return fm


def validate_journal_entry(fm: dict) -> list[str]:
    errors = []
    for field in REQUIRED_JOURNAL_FIELDS:
        if field not in fm or fm[field] in (None, ""):
            errors.append(f"必須項目が未入力: {field}")
    ips_check = str(fm.get("ips_check", ""))
    if ips_check != "pass" and not ips_check.startswith("override("):
        errors.append("ips_check は pass または override(理由) のみ有効")
    return errors


def next_id(journal_dir: str) -> str:
    existing = glob.glob(os.path.join(journal_dir, "J-*.md"))
    nums = []
    for path in existing:
        m = re.search(r"J-(\d+)", os.path.basename(path))
        if m:
            nums.append(int(m.group(1)))
    n = max(nums, default=0) + 1
    return f"J-{n:03d}"


def list_due_for_review(journal_dir: str, today: datetime) -> list[dict]:
    due = []
    for path in glob.glob(os.path.join(journal_dir, "J-*.md")):
        fm = parse_journal_file(path)
        if fm.get("status") != "open":
            continue
        review_date = fm.get("review_date")
        if not review_date:
            continue
        rd = datetime.strptime(str(review_date), "%Y-%m-%d").replace(tzinfo=timezone.utc)
        if rd <= today:
            due.append(fm)
    return due


def close_entry(path: str, outcome: str) -> None:
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        raise ValueError(f"{path}: frontmatterが見つかりません")
    fm = yaml.safe_load(m.group(1)) or {}
    fm["status"] = "closed"
    fm["outcome"] = outcome
    body = m.group(2)
    new_text = "---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False) + "---\n" + body
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--journal-dir", required=True)
    parser.add_argument("--list-due", action="store_true")
    parser.add_argument("--today", help="YYYY-MM-DD（省略時は本日）")
    parser.add_argument("--close", help="ジャーナルID（例: J-001）")
    parser.add_argument("--outcome", help="--close 使用時の結果・学び")
    args = parser.parse_args()

    if args.list_due:
        today = (
            datetime.strptime(args.today, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if args.today else datetime.now(timezone.utc)
        )
        due = list_due_for_review(args.journal_dir, today)
        if not due:
            print("レビュー期日到来分はありません")
            return 0
        for fm in due:
            print(f"{fm['id']}: {fm['target']} (review_date={fm['review_date']})")
        return 0

    if args.close:
        matches = glob.glob(os.path.join(args.journal_dir, f"{args.close}-*.md"))
        if not matches:
            print(f"見つかりません: {args.close}", file=sys.stderr)
            return 1
        close_entry(matches[0], args.outcome or "")
        print(f"クローズしました: {args.close}")
        return 0

    print("次のID:", next_id(args.journal_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
