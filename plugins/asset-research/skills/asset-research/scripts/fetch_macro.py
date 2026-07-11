"""マクロダッシュボード取得。FRED（米指標）+ e-Stat（日本統計）。

使い方:
    python fetch_macro.py --dashboard

APIキー:
    FRED_API_KEY   https://fred.stlouisfed.org/docs/api/api_key.html で無料発行
    ESTAT_APP_ID   https://www.e-stat.go.jp/api/ で無料発行
"""
from __future__ import annotations

import argparse
import sys
from typing import Optional

from common import DataPoint, FetchError, is_stale, percentile_position, require_env
from http_client import http_get_json

FRED_SERIES = {
    "DGS10": ("米10年国債利回り", "%"),
    "DGS2": ("米2年国債利回り", "%"),
    "T10Y2Y": ("米10年-2年 イールドスプレッド", "%"),
    "CPIAUCSL": ("米CPI（全項目）", ""),
    "UNRATE": ("米失業率", "%"),
    "VIXCLS": ("VIX指数", ""),
    "DTWEXBGS": ("米ドル名目実効レート", ""),
}

ESTAT_SERIES = {
    "cpi_jp": ("日本CPI総合", "0000020101", "%"),
    "gdp_real_jp": ("日本実質GDP成長率", "0003109763", "%"),
}


def fetch_fred_series(series_id: str, api_key: str) -> list[tuple[str, float]]:
    url = (
        "https://api.stlouisfed.org/fred/series/observations"
        f"?series_id={series_id}&api_key={api_key}&file_type=json"
        "&sort_order=desc&limit=3650"
    )
    data = http_get_json(url)
    obs = data.get("observations", [])
    out = []
    for o in obs:
        v = o.get("value")
        if v is None or v == ".":
            continue
        out.append((o["date"], float(v)))
    return out


def fetch_fred_datapoint(series_id: str, name: str, unit: str, api_key: str) -> DataPoint:
    try:
        series = fetch_fred_series(series_id, api_key)
    except Exception as e:  # noqa: BLE001 — 取得失敗は種類を問わずFETCH_FAILEDにする
        return DataPoint(name=name, value=None, unit=unit,
                          source=f"FRED series={series_id}", tier="一次",
                          failed=True, fail_reason=str(e))
    if not series:
        return DataPoint(name=name, value=None, unit=unit,
                          source=f"FRED series={series_id}", tier="一次",
                          failed=True, fail_reason="no observations")
    latest_date, latest_val = series[0]
    hist_values = [v for _, v in series]
    pct = percentile_position(latest_val, hist_values)
    pct_note = f" (過去10年百分位: {pct}%ile)" if pct is not None else ""
    return DataPoint(
        name=name,
        value=f"{latest_val}{pct_note}",
        unit=unit,
        source=f"FRED series={series_id}",
        tier="一次",
        as_of=latest_date,
        stale=is_stale(latest_date),
    )


def fetch_estat_datapoint(key: str, name: str, stats_data_id: str, unit: str, app_id: str) -> DataPoint:
    url = (
        "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData"
        f"?appId={app_id}&statsDataId={stats_data_id}&limit=100"
    )
    try:
        data = http_get_json(url)
        values = data["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]
        if isinstance(values, dict):
            values = [values]
        latest = values[-1]
        latest_val = float(latest["$"])
        latest_date = str(latest.get("@time", ""))
    except Exception as e:  # noqa: BLE001
        return DataPoint(name=name, value=None, unit=unit,
                          source=f"e-Stat statsDataId={stats_data_id}", tier="一次",
                          failed=True, fail_reason=str(e))
    return DataPoint(
        name=name,
        value=str(latest_val),
        unit=unit,
        source=f"e-Stat statsDataId={stats_data_id}",
        tier="一次",
        as_of=latest_date,
    )


def build_dashboard() -> list[DataPoint]:
    points: list[DataPoint] = []
    try:
        fred_key = require_env(
            "FRED_API_KEY",
            "https://fred.stlouisfed.org/docs/api/api_key.html",
            "St. Louis連銀の無料アカウントで即時発行できます。",
        )
    except FetchError:
        fred_key = None
    if fred_key:
        for sid, (name, unit) in FRED_SERIES.items():
            points.append(fetch_fred_datapoint(sid, name, unit, fred_key))
    else:
        for sid, (name, unit) in FRED_SERIES.items():
            points.append(DataPoint(name=name, value=None, unit=unit,
                                     source=f"FRED series={sid}", tier="一次",
                                     failed=True, fail_reason="FRED_API_KEY not set"))

    try:
        estat_key = require_env(
            "ESTAT_APP_ID",
            "https://www.e-stat.go.jp/api/",
            "政府統計の総合窓口（e-Stat）のアプリケーションIDを無料発行できます。",
        )
    except FetchError:
        estat_key = None
    if estat_key:
        for key, (name, stats_id, unit) in ESTAT_SERIES.items():
            points.append(fetch_estat_datapoint(key, name, stats_id, unit, estat_key))
    else:
        for key, (name, stats_id, unit) in ESTAT_SERIES.items():
            points.append(DataPoint(name=name, value=None, unit=unit,
                                     source=f"e-Stat statsDataId={stats_id}", tier="一次",
                                     failed=True, fail_reason="ESTAT_APP_ID not set"))
    return points


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dashboard", action="store_true")
    args = parser.parse_args()
    if not args.dashboard:
        parser.print_help()
        return 0

    points = build_dashboard()
    print("# マクロダッシュボード")
    print()
    for p in points:
        print(p.render())
        print()
    print(
        "百分位はタイミングシグナルではありません。この数値を根拠にIPSの配分レンジ外へ"
        "動かす提案はしません（詳細: docs/designs/23-asset-research-engine.md §6.2）。"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
