from memo_schema import extract_sections, extract_urls, validate_memo

VALID_MEMO = """# テーマ 分析メモ
---
date: 2026-07-15
type: 銘柄
---
1. 問い
何を判断したいのか。

2. 事実
実質GDP成長率: +0.4%
  [source: https://example.com/a, retrieved: 2026-07-15T10:00Z, tier: 一次]
別ソース [source: https://another-domain.example/b]

3. Bull case
強気の仮説がここに十分な長さで書かれている。

4. Bear case
弱気の仮説もここに十分な長さで書かれている。

5. 反証条件
何が観測されたら見立てが間違いかを測定可能な形で書く。

6. ベンチマーク反実仮想
全世界インデックス積立と比べてこの行動が勝る理由をここに書く。

7. コスト・税制
NISA枠の話。

8. 結論と確信度
ウォッチ。確信度中。
"""


def test_extract_sections_all_present():
    sections = extract_sections(VALID_MEMO)
    assert set(sections.keys()) == {1, 2, 3, 4, 5, 6, 7, 8}


def test_extract_urls():
    urls = extract_urls(VALID_MEMO)
    assert len(urls) == 2


def test_validate_memo_valid():
    result = validate_memo(VALID_MEMO)
    assert result.ok


def test_validate_memo_empty_bear_case_rejected():
    broken = VALID_MEMO.replace(
        "4. Bear case\n弱気の仮説もここに十分な長さで書かれている。\n",
        "4. Bear case\nなし\n",
    )
    result = validate_memo(broken)
    assert not result.ok
    assert any("Bear case" in e for e in result.errors)


def test_validate_memo_missing_falsifier_rejected():
    broken = VALID_MEMO.replace(
        "5. 反証条件\n何が観測されたら見立てが間違いかを測定可能な形で書く。\n",
        "5. 反証条件\n特になし\n",
    )
    result = validate_memo(broken)
    assert not result.ok
    assert any("反証条件" in e for e in result.errors)


def test_validate_memo_missing_section():
    broken = VALID_MEMO.split("6. ベンチマーク反実仮想")[0]
    result = validate_memo(broken)
    assert not result.ok


def test_validate_memo_single_domain_warning():
    single_domain = VALID_MEMO.replace(
        "別ソース [source: https://another-domain.example/b]", ""
    ).replace(
        "  [source: https://example.com/a, retrieved: 2026-07-15T10:00Z, tier: 一次]",
        "  [source: https://example.com/a, retrieved: 2026-07-15T10:00Z, tier: 一次]\n"
        "  [source: https://example.com/c]",
    )
    result = validate_memo(single_domain)
    assert result.ok
    assert any("単一ドメイン" in w for w in result.warnings)
