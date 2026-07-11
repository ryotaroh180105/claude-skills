import pytest

from ips_schema import check_allocation_in_range, validate_ips

VALID_IPS = """---
purpose: "test"
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
nisa_usage: "test"
rebalance_condition: "test"
---
# body
"""


def test_validate_ips_valid():
    result = validate_ips(VALID_IPS)
    assert result.ok
    assert result.errors == []


def test_validate_ips_missing_field():
    broken = VALID_IPS.replace('purpose: "test"\n', "")
    result = validate_ips(broken)
    assert not result.ok
    assert any("purpose" in e for e in result.errors)


def test_validate_ips_invalid_range():
    broken = VALID_IPS.replace("min_pct: 50\n    max_pct: 70", "min_pct: 80\n    max_pct: 70")
    result = validate_ips(broken)
    assert not result.ok
    assert any("min_pct > max_pct" in e for e in result.errors)


def test_validate_ips_no_frontmatter():
    result = validate_ips("no frontmatter here")
    assert not result.ok


def test_validate_ips_change_rule_violation():
    broken = VALID_IPS.replace(
        "---\n# body",
        'pending_change_proposed_at: "2026-07-10"\n'
        'pending_change_effective_at: "2026-07-11"\n---\n# body',
    )
    result = validate_ips(broken)
    assert not result.ok
    assert any("7日後" in e for e in result.errors)


def test_check_allocation_in_range_violation():
    violations = check_allocation_in_range({"equity": 80}, VALID_IPS)
    assert len(violations) == 1
    assert "equity" in violations[0]


def test_check_allocation_in_range_ok():
    violations = check_allocation_in_range({"equity": 60}, VALID_IPS)
    assert violations == []
