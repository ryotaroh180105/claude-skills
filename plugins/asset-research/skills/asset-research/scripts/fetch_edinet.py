"""日本企業の法定開示（EDINET）取得。キー不要（Subscription-Keyのみ、無料登録）。

使い方:
    python fetch_edinet.py --code E02144 --latest

E02144 のような EDINETコードは以下で検索できる:
https://disclosure2.edinet-fsa.go.jp/week0010.aspx （EDINETコードリスト配布ページ）

注意（docs/designs/23-asset-research-engine.md §4, レッドチーム所見1）:
抽出した財務値は必ずXBRLの単位（円/千円/百万円）と連結・単体区分を併記する。
値のみを鵜呑みにせず、公表資料（決算短信・有価証券報告書）との突合を推奨する。
"""
from __future__ import annotations

import argparse
import csv
import io
import sys
import zipfile
from datetime import datetime, timedelta
from typing import Optional

from common import now_iso, require_env
from http_client import http_get_json

EDINET_LIST_URL = "https://api.edinet-fsa.go.jp/api/v2/documents.json"
EDINET_DOC_URL = "https://api.edinet-fsa.go.jp/api/v2/documents/{doc_id}"

# CSV（XBRL to CSV変換）内で財務値抽出に使う要素ID（連結優先、無ければ単体）
TARGET_ELEMENTS = {
    "売上高": ["jppfs_cor:NetSales", "jppfs_cor:OperatingRevenue1"],
    "営業利益": ["jppfs_cor:OperatingIncome"],
    "自己資本比率": ["jpcrp_cor:CapitalAdequacyRatio", "jpcrp_cor:EquityToAssetRatio"],
}


def search_documents(edinet_code: str, subscription_key: str, days_back: int = 120) -> list[dict]:
    """指定EDINETコードの提出書類を、直近days_back日から新しい順に検索する。"""
    found = []
    today = datetime.utcnow().date()
    for i in range(days_back):
        d = today - timedelta(days=i)
        url = f"{EDINET_LIST_URL}?date={d.isoformat()}&type=2&Subscription-Key={subscription_key}"
        try:
            data = http_get_json(url)
        except Exception:  # noqa: BLE001
            continue
        for doc in data.get("results", []):
            if doc.get("edinetCode") == edinet_code:
                found.append(doc)
        if found:
            break
    return found


def parse_financial_csv(csv_bytes: bytes) -> dict:
    """XBRL to CSV（Shift_JIS想定）から主要財務値を抽出する。連結優先。"""
    text = csv_bytes.decode("utf-16", errors="ignore")
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    rows = list(reader)
    result: dict[str, dict] = {}
    for label, element_ids in TARGET_ELEMENTS.items():
        for row in rows:
            elem = row.get("要素ID", "")
            if elem in element_ids:
                context = row.get("コンテキストID", "")
                is_consolidated = "NonConsolidated" not in context
                result[label] = {
                    "value": row.get("値"),
                    "unit": row.get("単位", "unknown"),
                    "consolidated": is_consolidated,
                    "element_id": elem,
                }
                break
    return result


def build_report(edinet_code: str, subscription_key: str) -> dict:
    docs = search_documents(edinet_code, subscription_key)
    if not docs:
        return {"edinet_code": edinet_code, "failed": True, "reason": "no documents found in search window"}
    latest = docs[0]
    return {
        "edinet_code": edinet_code,
        "doc_id": latest.get("docID"),
        "doc_description": latest.get("docDescription"),
        "submit_date": latest.get("submitDateTime"),
        "filer_name": latest.get("filerName"),
        "retrieved_at": now_iso(),
        "failed": False,
    }


def render_report(report: dict) -> str:
    if report.get("failed"):
        return f"EDINET: 未検証（FETCH_FAILED: {report['reason']}）"
    lines = [
        f"# EDINET最新開示: {report.get('filer_name', report['edinet_code'])}",
        f"書類ID: {report['doc_id']}",
        f"書類種別: {report['doc_description']}",
        f"提出日時: {report['submit_date']}",
        f"  [source: EDINET docID={report['doc_id']}, retrieved: {report['retrieved_at']}, tier: 一次]",
        "",
        "財務値の抽出は書類ダウンロード（別途 --extract-financials）が必要です。"
        "抽出値は必ず単位・連結区分を併記し、公表資料との突合を推奨します。",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", required=True, help="EDINETコード（例: E02144）")
    parser.add_argument("--latest", action="store_true")
    args = parser.parse_args()

    key = require_env(
        "EDINET_SUBSCRIPTION_KEY",
        "https://api.edinet-fsa.go.jp/",
        "EDINET API v2 の利用登録（無料）で発行されるSubscription-Keyです。",
    )
    report = build_report(args.code, key)
    print(render_report(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
