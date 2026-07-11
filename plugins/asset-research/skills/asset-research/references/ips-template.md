# IPS（投資方針書）テンプレート（docs/designs/23-asset-research-engine.md §5.5）

```markdown
---
purpose: "老後資金形成、20年運用"
horizon_years: 20
monthly_contribution_available: true
max_acceptable_drawdown_pct: 30
allocation_ranges:
  equity:
    min_pct: 50
    max_pct: 70
  bond_cash:
    min_pct: 30
    max_pct: 50
per_ticker_cap_pct: 10
core_satellite_satellite_cap_pct: 20
nisa_usage: "つみたて投資枠を優先、成長投資枠はサテライト用途"
rebalance_condition: "レンジ逸脱時のみ。年1回上限"
pending_change_proposed_at: null
pending_change_effective_at: null
---

# 投資方針書（IPS）

本方針は起案から7日後にのみ変更が発効する（暴走的な衝動改定を防ぐため）。
```

## 検証

```bash
python ../scripts/ips_schema.py --validate <path>
```
