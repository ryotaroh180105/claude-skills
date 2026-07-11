"""米企業の法定開示（SEC EDGAR）取得。キー不要（User-Agent必須、10req/s制限）。

使い方:
    python fetch_edgar.py --cik 0000320193 --latest        # Apple の例
    python fetch_edgar.py --cik 0000320193 --concept Revenues

CIK番号は https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany で検索できる。
"""
from __future__ import annotations

import argparse
import sys

from common import now_iso
from http_client import http_get_json

SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
CONCEPT_URL = "https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{tag}.json"


def normalize_cik(cik: str) -> str:
    return cik.zfill(10)


def get_latest_filing(cik: str, form_types=("10-K", "10-Q")) -> dict:
    url = SUBMISSIONS_URL.format(cik=normalize_cik(cik))
    try:
        data = http_get_json(url)
    except Exception as e:  # noqa: BLE001
        return {"failed": True, "reason": str(e)}
    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])
    for i, form in enumerate(forms):
        if form in form_types:
            return {
                "failed": False,
                "company_name": data.get("name"),
                "form": form,
                "filing_date": dates[i] if i < len(dates) else None,
                "accession_number": accessions[i] if i < len(accessions) else None,
                "retrieved_at": now_iso(),
            }
    return {"failed": True, "reason": f"no {form_types} filing found in recent submissions"}


def get_company_concept(cik: str, tag: str) -> dict:
    url = CONCEPT_URL.format(cik=normalize_cik(cik), tag=tag)
    try:
        data = http_get_json(url)
    except Exception as e:  # noqa: BLE001
        return {"failed": True, "reason": str(e), "tag": tag}
    units = data.get("units", {})
    usd_values = units.get("USD", [])
    if not usd_values:
        return {"failed": True, "reason": "no USD unit values", "tag": tag}
    latest = sorted(usd_values, key=lambda x: x.get("end", ""))[-1]
    return {
        "failed": False,
        "tag": tag,
        "value": latest.get("val"),
        "unit": "USD",
        "period_end": latest.get("end"),
        "form": latest.get("form"),
        "retrieved_at": now_iso(),
    }


def render(report: dict, kind: str) -> str:
    if report.get("failed"):
        return f"EDGAR {kind}: 未検証（FETCH_FAILED: {report['reason']}）"
    if kind == "filing":
        return (
            f"# EDGAR最新開示: {report['company_name']}\n"
            f"書類種別: {report['form']} / 提出日: {report['filing_date']}\n"
            f"accession番号: {report['accession_number']}\n"
            f"  [source: SEC EDGAR, retrieved: {report['retrieved_at']}, tier: 一次]"
        )
    return (
        f"{report['tag']}: {report['value']} {report['unit']}"
        f"（期末: {report['period_end']}, form: {report['form']}）\n"
        f"  [source: SEC EDGAR companyconcept, retrieved: {report['retrieved_at']}, tier: 一次]"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cik", required=True)
    parser.add_argument("--latest", action="store_true")
    parser.add_argument("--concept", help="us-gaap タグ名（例: Revenues, OperatingIncomeLoss）")
    args = parser.parse_args()

    if args.concept:
        print(render(get_company_concept(args.cik, args.concept), "concept"))
    else:
        print(render(get_latest_filing(args.cik), "filing"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
