"""分析メモの8セクション検証。docs/designs/23-asset-research-engine.md §5.3。

bear case・反証条件・ベンチマーク反実仮想が空欄なら保存を拒否する。
出典URLの実到達性・ドメイン独立性も検査する（レッドチーム所見2）。

使い方:
    python memo_schema.py --validate /path/to/memo.md
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from dataclasses import dataclass
from urllib.parse import urlparse

REQUIRED_SECTIONS = {
    1: "問い",
    2: "事実",
    3: "Bull case",
    4: "Bear case",
    5: "反証条件",
    6: "ベンチマーク反実仮想",
    7: "コスト・税制",
    8: "結論と確信度",
}
MANDATORY_NONEMPTY = {4, 5, 6}
MIN_CONTENT_LENGTH = 15


@dataclass
class MemoValidationResult:
    ok: bool
    errors: list[str]
    warnings: list[str]


def extract_sections(text: str) -> dict[int, str]:
    pattern = re.compile(r"^(\d+)\.\s+.+$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    sections = {}
    for i, m in enumerate(matches):
        num = int(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[num] = text[start:end].strip()
    return sections


def extract_urls(text: str) -> list[str]:
    return re.findall(r"https?://[^\s\)\]]+", text)


def check_url_reachable(url: str, timeout: int = 10) -> bool:
    try:
        req = urllib.request.Request(url, method="HEAD",
                                      headers={"User-Agent": "asset-research/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status < 400
    except Exception:  # noqa: BLE001
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "asset-research/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status < 400
        except Exception:  # noqa: BLE001
            return False


def domain_of(url: str) -> str:
    return urlparse(url).netloc


def validate_memo(text: str, check_urls: bool = False) -> MemoValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    sections = extract_sections(text)

    for num, label in REQUIRED_SECTIONS.items():
        if num not in sections:
            errors.append(f"セクション{num}（{label}）が見つかりません")
            continue
        content = sections[num]
        if num in MANDATORY_NONEMPTY and len(content) < MIN_CONTENT_LENGTH:
            errors.append(
                f"セクション{num}（{label}）が空欄または不十分です"
                f"（{MIN_CONTENT_LENGTH}文字以上必須。保存不可: 反証が書けない=判断材料不足）"
            )

    fact_section = sections.get(2, "")
    urls = extract_urls(fact_section)
    if not urls:
        warnings.append("事実セクションに出典URLが1件もありません")
    else:
        domains = {domain_of(u) for u in urls}
        if len(domains) < 2 and len(urls) >= 2:
            warnings.append(
                "事実セクションの出典が単一ドメインに偏っています"
                "（独立2ソース裏取りルール。三次由来の複製に注意）"
            )
        if check_urls:
            for u in urls:
                if not check_url_reachable(u):
                    errors.append(f"出典URLに到達できません: {u}")

    return MemoValidationResult(ok=not errors, errors=errors, warnings=warnings)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate", required=True)
    parser.add_argument("--check-urls", action="store_true", help="出典URLの実到達を確認する（ネットワーク要）")
    args = parser.parse_args()

    with open(args.validate, encoding="utf-8") as f:
        text = f.read()
    result = validate_memo(text, check_urls=args.check_urls)
    if result.ok:
        print("OK: 分析メモは保存可能です")
        for w in result.warnings:
            print(f"  警告: {w}")
        return 0
    print("NG: 保存不可")
    for e in result.errors:
        print(f"  - {e}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
