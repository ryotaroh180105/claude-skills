"""asset-research 共通ユーティリティ。§5.2 出典付与形式・tier格付け・FETCH_FAILED処理。"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

TIER_PRIMARY = "一次"
TIER_SECONDARY = "二次"
TIER_TERTIARY = "三次"

STALE_DAYS = 7


class FetchError(Exception):
    """データ取得に失敗した際に送出する。呼び出し側は FETCH_FAILED として扱う。"""


@dataclass
class DataPoint:
    name: str
    value: Optional[str]
    unit: str
    source: str
    tier: str
    retrieved_at: str = field(default_factory=lambda: now_iso())
    as_of: Optional[str] = None
    stale: bool = False
    failed: bool = False
    fail_reason: Optional[str] = None

    def render(self) -> str:
        if self.failed:
            return (
                f"{self.name}: 未検証（FETCH_FAILED: {self.fail_reason}）"
            )
        stale_tag = " [STALE]" if self.stale else ""
        as_of = f"（{self.as_of}時点）" if self.as_of else ""
        return (
            f"{self.name}{as_of}: {self.value}{self.unit}{stale_tag}\n"
            f"  [source: {self.source}, retrieved: {self.retrieved_at}, tier: {self.tier}]"
        )


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def is_stale(as_of_date: str, today: Optional[datetime] = None) -> bool:
    today = today or datetime.now(timezone.utc)
    try:
        d = datetime.strptime(as_of_date[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return False
    return (today - d).days > STALE_DAYS


def require_env(key: str, issue_url: str, notes: str = "") -> str:
    """APIキー未設定時は発行URLを提示して停止する（無言で失敗しない）。"""
    val = os.environ.get(key)
    if not val:
        msg = (
            f"環境変数 {key} が未設定です。\n"
            f"発行URL: {issue_url}\n"
            f"{notes}\n"
            f"取得後、~/.asset-research/.env に {key}=<値> を書くか、"
            f"このセッションの環境変数に設定してください。"
        )
        print(msg, file=sys.stderr)
        raise FetchError(f"{key} not set")
    return val


def percentile_position(current: float, series: list[float]) -> Optional[float]:
    """過去10年レンジ内での現在値の百分位（0-100）。系列が空なら None。"""
    if not series:
        return None
    sorted_series = sorted(series)
    below = sum(1 for v in sorted_series if v <= current)
    return round(100 * below / len(sorted_series), 1)


def reconcile_prices(primary: Optional[float], secondary: Optional[float], threshold_pct: float = 1.0):
    """価格2系統突合。乖離threshold_pct%超なら値を出さずPRICE_MISMATCHを返す。

    投信などstooq側に気配が無い銘柄は2系統突合が構造的に不可能なため、
    primaryのみ取得できた場合は値を捨てずSINGLE_SOURCEとして返す
    （secondaryのみの場合は引き続きFETCH_FAILED）。
    """
    if primary is None and secondary is None:
        return None, "FETCH_FAILED"
    if primary is None:
        return None, "FETCH_FAILED"
    if secondary is None:
        return primary, "SINGLE_SOURCE"
    if primary == 0:
        return None, "PRICE_MISMATCH"
    diff_pct = abs(primary - secondary) / abs(primary) * 100
    if diff_pct > threshold_pct:
        return None, "PRICE_MISMATCH"
    return primary, None


def detect_corporate_action(prev_close: float, curr_close: float, tolerance_pct: float = 2.0) -> Optional[str]:
    """前日比が典型的な分割比率（1/2, 1/3, 2/3, 1/5, 1/10等）近傍ならCORPORATE_ACTIONを返す。"""
    if prev_close == 0:
        return None
    ratio = curr_close / prev_close
    split_ratios = [0.5, 1 / 3, 2 / 3, 0.2, 0.1, 2.0, 3.0, 5.0, 10.0]
    for r in split_ratios:
        if abs(ratio - r) / r * 100 <= tolerance_pct:
            return "CORPORATE_ACTION"
    return None
