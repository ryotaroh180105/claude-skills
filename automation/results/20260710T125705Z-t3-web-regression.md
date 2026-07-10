---
id: 20260710T125705Z-t3-web-regression
status: ok
executed_at: 2026-07-10T13:01:20Z
duration_seconds: 35
---

1. 要点（出典URL付き）
GitHub Actionsの標準GitHubホストランナー（ubuntu-latestなど）について、公式ドキュメントに以下の記載がある：GitHub Actionsの利用は、パブリックリポジトリで標準GitHubホストランナーを使用する場合、およびセルフホストランナーの場合に無料。プライベートリポジトリの場合、各プランごとに無料の分（minutes）とストレージの割り当てがあり、毎月リセットされる（例: GitHub Freeプランで2,000分、500 MBアーティファクトストレージ、10 GBキャッシュ）。超過時は課金対象。
出典: https://docs.github.com/billing/managing-billing-for-github-actions/about-billing-for-github-actions （および https://docs.github.com/en/actions/reference/limits のストレージ/分テーブルも同内容を確認）

2. 未確認・断定できない点
- 具体的なubuntu-latestインスタンスのスペック詳細や、同時実行ジョブ数上限の最新値
- 2026年7月時点でのプラン別無料枠の変更有無（スニペットベースのため全文未取得）
- 特定リポジトリ種別（public/private）ごとの例外や追加制限の全容

3. 使用ツール（自己申告）
web_search

使用ツール: web_search
