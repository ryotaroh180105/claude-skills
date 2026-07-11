from gate import check_benchmark_section, check_cooling_off, check_fomo, check_ips_allocation, run_gate

IPS_TEXT = """---
purpose: "test"
horizon_years: 20
monthly_contribution_available: true
max_acceptable_drawdown_pct: 30
allocation_ranges:
  equity:
    min_pct: 50
    max_pct: 70
per_ticker_cap_pct: 10
core_satellite_satellite_cap_pct: 20
nisa_usage: "test"
rebalance_condition: "test"
---
"""

MEMO_WITH_BENCHMARK = """1. 問い
test

6. ベンチマーク反実仮想
全世界インデックス積立と比べてこの行動が勝る理由を十分に書く。

7. コスト・税制
test
"""

MEMO_WITHOUT_BENCHMARK = """1. 問い
test

6. ベンチマーク反実仮想
なし

7. コスト・税制
test
"""


def test_check_ips_allocation_within_range():
    ok, msg = check_ips_allocation(IPS_TEXT, "equity", 5, {"equity": 55})
    assert ok


def test_check_ips_allocation_exceeds_range():
    ok, msg = check_ips_allocation(IPS_TEXT, "equity", 8, {"equity": 65})
    assert not ok
    assert "レンジ" in msg


def test_check_ips_allocation_exceeds_ticker_cap():
    ok, msg = check_ips_allocation(IPS_TEXT, "equity", 15, {"equity": 30})
    assert not ok
    assert "1銘柄上限" in msg


def test_check_cooling_off_not_elapsed():
    ok, msg = check_cooling_off("2026-07-10T10:00:00Z", "2026-07-10T20:00:00Z")
    assert not ok


def test_check_cooling_off_elapsed():
    ok, msg = check_cooling_off("2026-07-10T10:00:00Z", "2026-07-11T11:00:00Z")
    assert ok


def test_check_fomo_flags_momentum():
    ok, msg = check_fomo(25.0, False)
    assert ok
    assert "FOMO警告" in msg


def test_check_fomo_no_flags():
    ok, msg = check_fomo(5.0, False)
    assert ok
    assert msg == "OK"


def test_check_benchmark_section_present():
    ok, _ = check_benchmark_section(MEMO_WITH_BENCHMARK)
    assert ok


def test_check_benchmark_section_missing():
    ok, _ = check_benchmark_section(MEMO_WITHOUT_BENCHMARK)
    assert not ok


def test_run_gate_full_pass():
    result = run_gate(
        IPS_TEXT, MEMO_WITH_BENCHMARK, "equity", 5, {"equity": 55},
        "2026-07-10T10:00:00Z", "2026-07-11T11:00:00Z", 5.0, False,
    )
    assert result.passed


def test_run_gate_blocks_on_cooling_off():
    result = run_gate(
        IPS_TEXT, MEMO_WITH_BENCHMARK, "equity", 5, {"equity": 55},
        "2026-07-10T10:00:00Z", "2026-07-10T20:00:00Z", 5.0, False,
    )
    assert not result.passed


def test_run_gate_blocks_on_missing_benchmark():
    result = run_gate(
        IPS_TEXT, MEMO_WITHOUT_BENCHMARK, "equity", 5, {"equity": 55},
        "2026-07-10T10:00:00Z", "2026-07-11T11:00:00Z", 5.0, False,
    )
    assert not result.passed


def test_run_gate_ips_violation_without_override_blocks():
    result = run_gate(
        IPS_TEXT, MEMO_WITH_BENCHMARK, "equity", 20, {"equity": 60},
        "2026-07-10T10:00:00Z", "2026-07-11T11:00:00Z", 5.0, False,
    )
    assert not result.passed


def test_run_gate_ips_violation_with_override_passes():
    result = run_gate(
        IPS_TEXT, MEMO_WITH_BENCHMARK, "equity", 20, {"equity": 60},
        "2026-07-10T10:00:00Z", "2026-07-11T11:00:00Z", 5.0, False,
        override_reason="意図的にレンジ超過を許容",
    )
    assert result.passed
    assert any("override" in w for w in result.warnings)
