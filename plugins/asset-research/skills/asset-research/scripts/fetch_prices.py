"""株価・投信基準価額・為替の時系列取得。yfinance + stooq の2系統突合。

使い方:
    python fetch_prices.py --ticker 7203.T --period 1y
    python fetch_prices.py --ticker AAPL --period 1y

設計上の理由（docs/designs/23-asset-research-engine.md §4, レッドチーム所見1）:
単一ソースの誤値（分割・調整の不一致等）を「出典付き」の体裁で信じてしまう事故を防ぐため、
2系統が乖離1%を超えたら値を出さず PRICE_MISMATCH とする。
"""
from __future__ import annotations

import argparse
import sys
from typing import Optional

from common import detect_corporate_action, now_iso, reconcile_prices
from http_client import http_get_text

try:
    import yfinance as yf
except ImportError:  # yfinanceは非公式・突然壊れる前提のためoptional依存にする
    yf = None


def to_stooq_symbol(ticker: str) -> str:
    if ticker.upper().endswith(".T"):
        return f"{ticker[:-2]}.jp"
    return ticker.lower() + ".us"


def fetch_stooq_close(ticker: str) -> Optional[float]:
    symbol = to_stooq_symbol(ticker)
    url = f"https://stooq.com/q/l/?s={symbol}&f=sd2t2ohlcv&h&e=csv"
    try:
        text = http_get_text(url)
        lines = text.strip().splitlines()
        if len(lines) < 2:
            return None
        row = lines[1].split(",")
        close = row[6]
        if close in ("N/D", ""):
            return None
        return float(close)
    except Exception:  # noqa: BLE001
        return None


def fetch_yfinance_close(
    ticker: str, period: str
) -> tuple[Optional[float], Optional[float], list[float], list[str]]:
    if yf is None:
        return None, None, [], []
    try:
        hist = yf.Ticker(ticker).history(period=period)
        if hist.empty:
            return None, None, [], []
        closes = hist["Close"].tolist()
        dates = [str(d.date()) for d in hist.index]
        latest = closes[-1]
        prev = closes[-2] if len(closes) > 1 else latest
        return latest, prev, closes, dates
    except Exception:  # noqa: BLE001
        return None, None, [], []


def build_price_report(ticker: str, period: str) -> dict:
    yf_close, yf_prev, series, dates = fetch_yfinance_close(ticker, period)
    stooq_close = fetch_stooq_close(ticker)

    value, mismatch_flag = reconcile_prices(yf_close, stooq_close)
    corp_action = None
    if yf_close is not None and yf_prev is not None:
        corp_action = detect_corporate_action(yf_prev, yf_close)

    return {
        "ticker": ticker,
        "yfinance_close": yf_close,
        "stooq_close": stooq_close,
        "reconciled_value": value,
        "flag": mismatch_flag,
        "corporate_action": corp_action,
        "retrieved_at": now_iso(),
        "series_length": len(series),
        "dates": dates,
        "closes": series,
    }


def render_report(report: dict) -> str:
    lines = [f"# 価格レポート: {report['ticker']}"]
    if report["flag"] == "PRICE_MISMATCH":
        lines.append(
            f"PRICE_MISMATCH: yfinance={report['yfinance_close']} vs stooq={report['stooq_close']}"
            "（乖離1%超のため値を採用しません。手動確認してください）"
        )
    elif report["flag"] == "SINGLE_SOURCE":
        lines.append(
            f"終値（単一ソース・突合不可）: {report['reconciled_value']}\n"
            f"  [source: yfinance, retrieved: {report['retrieved_at']}, tier: 二次]\n"
            "単一ソースのため分析メモの『事実』セクションには使用不可（tier: 二次・未突合）"
        )
    elif report["flag"] == "FETCH_FAILED" or report["reconciled_value"] is None:
        lines.append("値: 未検証（FETCH_FAILED: 片方または両方のソース取得に失敗）")
    else:
        lines.append(
            f"終値（未調整）: {report['reconciled_value']}\n"
            f"  [source: yfinance+stooq 突合一致, retrieved: {report['retrieved_at']}, tier: 二次]"
        )
    if report["corporate_action"]:
        lines.append(
            "CORPORATE_ACTION: 前日比が典型的な分割比率に近似しています。"
            "株式分割・配当落ちの可能性があるため、調整後/調整前の別を確認してください。"
        )
    return "\n".join(lines)


def render_csv(report: dict) -> str:
    """終値系列をdate,close形式で出力し、末尾に出典・取得日時のコメント行を付ける。"""
    lines = ["date,close"]
    for d, c in zip(report["dates"], report["closes"]):
        lines.append(f"{d},{c}")
    lines.append(f"# [source: yfinance, retrieved: {report['retrieved_at']}, tier: 二次]")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--period", default="1y")
    parser.add_argument("--csv", action="store_true", help="終値系列をdate,close形式のCSVで出力する")
    args = parser.parse_args()

    report = build_price_report(args.ticker, args.period)
    if args.csv:
        print(render_csv(report))
    else:
        print(render_report(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
