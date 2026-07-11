"""IPS（投資方針書）のスキーマ検証。docs/designs/23-asset-research-engine.md §5.5。

使い方:
    python ips_schema.py --validate /path/to/ips.md
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import yaml

REQUIRED_FIELDS = [
    "purpose",
    "horizon_years",
    "monthly_contribution_available",
    "max_acceptable_drawdown_pct",
    "allocation_ranges",
    "per_ticker_cap_pct",
    "core_satellite_satellite_cap_pct",
    "nisa_usage",
    "rebalance_condition",
]


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str]


def parse_frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        raise ValueError("frontmatter (---...---) が見つかりません")
    return yaml.safe_load(m.group(1)) or {}


def validate_ips(text: str) -> ValidationResult:
    errors = []
    try:
        fm = parse_frontmatter(text)
    except ValueError as e:
        return ValidationResult(ok=False, errors=[str(e)])

    for field in REQUIRED_FIELDS:
        if field not in fm or fm[field] in (None, "", []):
            errors.append(f"必須項目が未入力: {field}")

    alloc = fm.get("allocation_ranges", {})
    if isinstance(alloc, dict):
        for asset_class, rng in alloc.items():
            if not isinstance(rng, dict) or "min_pct" not in rng or "max_pct" not in rng:
                errors.append(f"allocation_ranges.{asset_class} に min_pct/max_pct がありません")
            elif rng["min_pct"] > rng["max_pct"]:
                errors.append(f"allocation_ranges.{asset_class}: min_pct > max_pct")

    change_effective = fm.get("pending_change_effective_at")
    if change_effective:
        try:
            eff = datetime.strptime(change_effective, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            proposed = fm.get("pending_change_proposed_at")
            if proposed:
                prop = datetime.strptime(proposed, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                if eff - prop < timedelta(days=7):
                    errors.append("IPS変更は起案から7日後にのみ発効できます（衝動改定防止）")
        except ValueError:
            errors.append("pending_change_effective_at / pending_change_proposed_at の日付形式が不正です")

    return ValidationResult(ok=not errors, errors=errors)


def check_allocation_in_range(current_pct: dict, ips_text: str) -> list[str]:
    """現在の配分（asset_class: pct）がIPSレンジ内かを確認し、逸脱を返す。"""
    fm = parse_frontmatter(ips_text)
    alloc = fm.get("allocation_ranges", {})
    violations = []
    for asset_class, pct in current_pct.items():
        rng = alloc.get(asset_class)
        if not rng:
            continue
        if not (rng["min_pct"] <= pct <= rng["max_pct"]):
            violations.append(
                f"{asset_class}: 現在{pct}% がレンジ{rng['min_pct']}〜{rng['max_pct']}%を逸脱"
            )
    return violations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate", required=True)
    args = parser.parse_args()

    with open(args.validate, encoding="utf-8") as f:
        text = f.read()
    result = validate_ips(text)
    if result.ok:
        print("OK: IPSは有効です")
        return 0
    print("NG: IPSに不備があります")
    for e in result.errors:
        print(f"  - {e}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
