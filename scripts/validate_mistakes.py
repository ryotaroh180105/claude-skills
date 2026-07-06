#!/usr/bin/env python3
"""MISTAKES.md のスキーマ検証（機械 Verifier）。

docs/mistakes-db-design.md のスキーマと Stop Rules（ルール行20行上限）を
機械的に強制する。登録者(Doer)の自己申告に頼らないための CI チェック。
"""
import re
import sys
from pathlib import Path

CATEGORIES = "誤答|手順ミス|仕様誤解|確認漏れ|破壊操作|その他"
RULE_RE = re.compile(rf"^- \[M-(\d{{3}})\]\[({CATEGORIES})\] .+")
ENTRY_RE = re.compile(r"^### M-(\d{3}): .+", re.M)
MAX_RULES = 20
REQUIRED_FIELDS = ["- 登録日: ", "- 事象: ", "- 根本原因: ", "- 再発防止: ", "- 再発: ", "- ステータス: "]


def strip_fenced_blocks(text: str) -> str:
    return re.sub(r"^```.*?^```$", "", text, flags=re.S | re.M)


def main() -> int:
    path = Path(__file__).resolve().parent.parent / "MISTAKES.md"
    errors = []
    text = path.read_text(encoding="utf-8")

    if text.count("<!-- rules:start -->") != 1 or text.count("<!-- rules:end -->") != 1:
        print("ERROR: rules:start / rules:end マーカーは各1個必要")
        return 1

    rules_section = text.split("<!-- rules:start -->")[1].split("<!-- rules:end -->")[0]
    rule_lines = [l for l in rules_section.splitlines() if l.startswith("- ")]
    rule_ids = []
    for line in rule_lines:
        m = RULE_RE.match(line)
        if not m:
            errors.append(f"ルール行の書式違反: {line}")
        else:
            rule_ids.append(m.group(1))
    if len(rule_lines) > MAX_RULES:
        errors.append(f"ルール行が上限 {MAX_RULES} 行を超過: {len(rule_lines)} 行。統合・昇格・廃止で削減する")

    log_text = strip_fenced_blocks(text.split("## 記録ログ", 1)[1]) if "## 記録ログ" in text else ""
    if not log_text:
        errors.append("「## 記録ログ」セクションが無い")

    entry_ids = ENTRY_RE.findall(strip_fenced_blocks(text))
    dupes = {i for i in entry_ids if entry_ids.count(i) > 1}
    if dupes:
        errors.append(f"ログエントリ ID 重複: {sorted('M-' + d for d in dupes)}")

    for rid in rule_ids:
        if rid not in entry_ids:
            errors.append(f"ルール行 M-{rid} に対応するログエントリが無い")

    entries = re.split(r"^### ", log_text, flags=re.M)[1:]
    for entry in entries:
        title = entry.splitlines()[0]
        for field in REQUIRED_FIELDS:
            if field not in entry:
                errors.append(f"エントリ「{title}」に必須フィールド「{field.strip('- :')}」が無い")

    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        return 1
    print(f"OK: rules={len(rule_lines)}/{MAX_RULES}, entries={len(entry_ids)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
