"""買い/売り登録前のゲート。docs/designs/23-asset-research-engine.md §6.5。

4チェック: (1) IPS照合 (2) 24hクーリングオフ (3) FOMOチェック (4) ベンチマーク反実仮想の記載。
1つでも不合格ならジャーナル登録を拒否する（override記載がある場合のみIPS違反を通す）。

使い方:
    python gate.py --check --ips /path/ips.md --memo /path/memo.md \\
        --target 7203.T --size-pct 5 --asset-class equity \\
        --first-seen-at 2026-07-10T10:00:00Z --now 2026-07-11T11:00:00Z \\
        --momentum-1m-pct 25 --learned-via-sns
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from ips_schema import parse_frontmatter
from memo_schema import extract_sections

COOLING_OFF_HOURS = 24
FOMO_MOMENTUM_THRESHOLD_PCT = 20
MIN_BENCHMARK_SECTION_LENGTH = 15


@dataclass
class GateResult:
    passed: bool
    checks: dict = field(default_factory=dict)
    blocking_reasons: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


def parse_iso(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def check_ips_allocation(ips_text: str, asset_class: str, proposed_size_pct: float,
                          current_allocation_pct: dict) -> tuple[bool, str]:
    fm = parse_frontmatter(ips_text)
    alloc = fm.get("allocation_ranges", {})
    rng = alloc.get(asset_class)
    per_ticker_cap = fm.get("per_ticker_cap_pct")

    if per_ticker_cap is not None and proposed_size_pct > per_ticker_cap:
        return False, f"1銘柄上限{per_ticker_cap}%を超過（提案{proposed_size_pct}%）"

    if rng:
        projected = current_allocation_pct.get(asset_class, 0) + proposed_size_pct
        if not (rng["min_pct"] <= projected <= rng["max_pct"]):
            return False, (
                f"{asset_class}の配分がレンジ{rng['min_pct']}〜{rng['max_pct']}%を"
                f"逸脱見込み（実行後想定{projected}%）"
            )
    return True, "OK"


def check_cooling_off(first_seen_at: str, now: str) -> tuple[bool, str]:
    seen = parse_iso(first_seen_at)
    current = parse_iso(now)
    elapsed = current - seen
    if elapsed < timedelta(hours=COOLING_OFF_HOURS):
        remaining = timedelta(hours=COOLING_OFF_HOURS) - elapsed
        return False, f"クーリングオフ未経過（残り約{remaining.seconds // 3600}時間）"
    return True, "OK"


def check_fomo(momentum_1m_pct: float | None, learned_via_sns: bool) -> tuple[bool, str]:
    """FOMOは登録を止めない（警告のみ）。ゲート全体としては通すが警告を残す。"""
    flags = []
    if momentum_1m_pct is not None and momentum_1m_pct >= FOMO_MOMENTUM_THRESHOLD_PCT:
        flags.append(f"直近1ヶ月で{momentum_1m_pct}%上昇")
    if learned_via_sns:
        flags.append("SNSで知った銘柄")
    if flags:
        return True, "FOMO警告: " + " / ".join(flags)
    return True, "OK"


def check_benchmark_section(memo_text: str) -> tuple[bool, str]:
    sections = extract_sections(memo_text)
    content = sections.get(6, "")
    if len(content) < MIN_BENCHMARK_SECTION_LENGTH:
        return False, "ベンチマーク反実仮想（セクション6）が空欄または不十分です"
    return True, "OK"


def run_gate(ips_text: str, memo_text: str, asset_class: str, size_pct: float,
             current_allocation_pct: dict, first_seen_at: str, now: str,
             momentum_1m_pct: float | None, learned_via_sns: bool,
             override_reason: str | None = None) -> GateResult:
    result = GateResult(passed=True)

    ok, msg = check_ips_allocation(ips_text, asset_class, size_pct, current_allocation_pct)
    result.checks["ips"] = msg
    if not ok:
        if override_reason:
            result.warnings.append(f"IPS違反をoverride: {msg} / 理由: {override_reason}")
        else:
            result.passed = False
            result.blocking_reasons.append(msg)

    ok, msg = check_cooling_off(first_seen_at, now)
    result.checks["cooling_off"] = msg
    if not ok:
        result.passed = False
        result.blocking_reasons.append(msg)

    ok, msg = check_fomo(momentum_1m_pct, learned_via_sns)
    result.checks["fomo"] = msg
    if "警告" in msg:
        result.warnings.append(msg)

    ok, msg = check_benchmark_section(memo_text)
    result.checks["benchmark"] = msg
    if not ok:
        result.passed = False
        result.blocking_reasons.append(msg)

    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ips", required=True)
    parser.add_argument("--memo", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--asset-class", required=True)
    parser.add_argument("--size-pct", type=float, required=True)
    parser.add_argument("--first-seen-at", required=True)
    parser.add_argument("--now", required=True)
    parser.add_argument("--momentum-1m-pct", type=float, default=None)
    parser.add_argument("--learned-via-sns", action="store_true")
    parser.add_argument("--override-reason", default=None)
    parser.add_argument("--current-allocation-pct", type=float, default=0.0,
                         help="対象アセットクラスの現在配分%（簡易入力）")
    args = parser.parse_args()

    with open(args.ips, encoding="utf-8") as f:
        ips_text = f.read()
    with open(args.memo, encoding="utf-8") as f:
        memo_text = f.read()

    result = run_gate(
        ips_text, memo_text, args.asset_class, args.size_pct,
        {args.asset_class: args.current_allocation_pct},
        args.first_seen_at, args.now,
        args.momentum_1m_pct, args.learned_via_sns, args.override_reason,
    )

    print(f"# ゲート判定: {args.target}")
    for name, msg in result.checks.items():
        print(f"  [{name}] {msg}")
    for w in result.warnings:
        print(f"  警告: {w}")
    if result.passed:
        print("PASS: ジャーナル登録可能です")
        return 0
    print("BLOCK: 以下の理由で登録できません")
    for r in result.blocking_reasons:
        print(f"  - {r}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
