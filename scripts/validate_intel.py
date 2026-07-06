#!/usr/bin/env python3
"""Validate intel/ records (principles, sns-post, book-note) against the
schema defined in intel/README.md and docs/designs/03-intel-hub.md §5.

Scans only intel/principles/, intel/sns/ (excluding sns/reports/), and
intel/books/. Does not scan intel/ root files, intel/inbox/, or
intel/sns/reports/ (those are not per-record files).
"""
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
INTEL_ROOT = REPO_ROOT / "intel"

DIR_TYPE = {
    "principles": "principle",
    "sns": "sns-post",
    "books": "book-note",
}

COMMON_REQUIRED = [
    "id",
    "type",
    "collected_at",
    "source_engine",
    "relay_result_id",
    "source_urls",
    "tags",
    "confidence",
    "related",
    "contradicts",
]

ENUMS = {
    "type": {"principle", "sns-post", "book-note", "bookmark"},
    "source_engine": {"hermes", "hermes-web", "notebooklm", "manual", "inbox"},
    "confidence": {"confirmed", "unconfirmed", "superseded"},
    "domain": {"資料作成", "文章術", "SEO", "SNS運用", "技術", "法務IR", "書籍知見"},
    "platform": {"x", "note", "instagram"},
    "post_type": {
        "体験談",
        "ノウハウ",
        "意見主張",
        "実績報告",
        "質問投げかけ",
        "まとめリスト",
        "引用コメント",
        "告知",
    },
    "original_platform": {"x", "web"},
}


def iter_record_files():
    for dirname in DIR_TYPE:
        base = INTEL_ROOT / dirname
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.md")):
            if dirname == "sns" and path.is_relative_to(base / "reports"):
                continue
            yield dirname, path


def parse_frontmatter(text: str):
    if not text.startswith("---"):
        return None, "frontmatterが '---' で始まっていない"
    end = text.find("\n---", 3)
    if end == -1:
        return None, "frontmatterが '---' で閉じられていない"
    raw = text[3:end]
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        return None, f"YAMLパース失敗: {exc}"
    if not isinstance(data, dict):
        return None, "frontmatterがマッピングでない"
    return data, None


def validate_record(dirname: str, path: Path, errors: list):
    label = str(path.relative_to(REPO_ROOT))
    text = path.read_text(encoding="utf-8")
    data, err = parse_frontmatter(text)
    if err:
        errors.append(f"{label}: {err}")
        return

    for field in COMMON_REQUIRED:
        if field not in data:
            errors.append(f"{label}: 必須フィールド '{field}' が無い")

    expected_type = DIR_TYPE[dirname]
    if data.get("type") is not None and data.get("type") != expected_type:
        errors.append(
            f"{label}: type '{data.get('type')}' がディレクトリ '{dirname}/' と一致しない"
            f"（期待値: {expected_type}）"
        )

    for field, allowed in ENUMS.items():
        if field in data and data[field] is not None:
            if data[field] not in allowed:
                errors.append(
                    f"{label}: '{field}' の値 '{data[field]}' が許可されていない（{sorted(allowed)}）"
                )

    if data.get("id") != path.stem:
        errors.append(f"{label}: id '{data.get('id')}' がファイル名 '{path.stem}' と一致しない")

    if data.get("source_engine") != "manual":
        source_urls = data.get("source_urls")
        if not source_urls:
            errors.append(f"{label}: source_engine が manual 以外なのに source_urls が空")

    if expected_type == "principle":
        claim = data.get("claim")
        if not claim:
            errors.append(f"{label}: principle レコードに 'claim' が無い")
        elif len(claim) > 100:
            errors.append(f"{label}: claim が100文字を超えている（{len(claim)}文字）")


def main():
    errors = []
    count = 0
    for dirname, path in iter_record_files():
        count += 1
        validate_record(dirname, path, errors)

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        print(f"\n{len(errors)} error(s) found")
        return 1

    print(f"OK {count} records")
    return 0


if __name__ == "__main__":
    sys.exit(main())
