---
id: 20260711T190616Z-finance-analysis-oss-survey
status: ok
executed_at: 2026-07-11T19:07:21Z
duration_seconds: 40
---

1. 流用候補リポジトリ一覧

- OpenBB (OpenBB-finance/OpenBB): 金融・経済データの統合プラットフォーム。公開・有料データソースを統合し、Python/Workspace/Excel/MCPサーバー経由でAIエージェント・クオンツ・分析者に提供。株式・オプション・クリプト・経済指標など対応。ライセンス: AGPLv3。メンテ状況: 活発（最終更新2026年7月8日頃、約70k stars）。個人利用の現実性: 高い（OSSで無料、MCP対応でClaude連携容易、ただしAGPL注意）。
- agents-for-openbb (OpenBB-finance/agents-for-openbb): OpenBB Workspace向けカスタムエージェント構築ツール。ライセンス: MIT。メンテ状況: 約354 stars。個人利用の現実性: 高い（OpenBB本体と組み合わせやすい）。
- FinGPT (AI4Finance-Foundation/FinGPT): 金融特化LLMフレームワーク。センチメント分析・株価予測・RAG・ベンチマークなど。ライセンス: MIT。メンテ状況: 活発（最終更新2026年6月1日頃、約21k stars）。個人利用の現実性: 高い（MITで商用・個人OK、Hugging Faceモデル利用可能）。
- FinRobot (AI4Finance-Foundation/FinRobot): 金融分析向けオープンソースAIエージェントプラットフォーム。多エージェント（LLM+強化学習+定量分析）で投資リサーチ・取引戦略・リスク評価を自動化。FinGPTを拡張。ライセンス: Apache-2.0。メンテ状況: 活発（最終更新2026年7月7日頃、約7.5k stars）。個人利用の現実性: 高い（多エージェント構成でマクロ・業界分析向き）。
- Alpha Vantage MCP Server (berlinbra/alpha-vantage-mcp または alphavantage公式): Alpha Vantage APIをMCPサーバー化。リアルタイム株価・企業情報・為替・暗号資産取得。Claude Desktop/Cursor対応。ライセンス: 詳細未記載（API無料枠活用）。メンテ状況: アクティブ。個人利用の現実性: 高い（無料APIプランあり、MCPで即Claude連携）。
- FMP MCP Server (Financial Modeling Prep公式 MCP、またはcdtait/fmp-mcp-server): FMPの7万+データポイント（株価・財務諸表・経済指標・イベント）をMCPでClaudeなどに直接提供。ライセンス: API利用規約による（無料プランあり）。メンテ状況: 公式サポート中。個人利用の現実性: 高い（無料プラン500MB帯域、MCPでAPIラッパー不要）。

2. 元URL（根拠、各候補ごとに1つ以上）
- OpenBB: https://github.com/OpenBB-finance/OpenBB
- agents-for-openbb: https://github.com/OpenBB-finance/agents-for-openbb
- FinGPT: https://github.com/AI4Finance-Foundation/FinGPT
- FinRobot: https://github.com/ai4finance-foundation/finrobot
- Alpha Vantage MCP: https://github.com/berlinbra/alpha-vantage-mcp および https://mcp.alphavantage.co/
- FMP MCP: https://site.financialmodelingprep.com/developer/docs/mcp-server

3. 推奨組み合わせ構成（上位3案、それぞれ理由付き）
- 案1: OpenBB（データ層） + Alpha Vantage/FMP MCPサーバー + Claude Desktop。理由: OpenBBの包括的データ統合とMCPネイティブ対応により、Claudeエージェントが直接金融・経済データをツール呼び出し可能。マクロ指標・業界データ取得が容易で、個人構築の基盤として最も現実的。
- 案2: FinRobot（エージェント層） + FinGPT（LLM微調整） + World Bank/Alpha Vantage無料API。理由: FinRobotの多エージェント構成が投資リサーチ・業界構造分析に強く、FinGPTで金融特化LLMを追加。無料データソースと組み合わせれば低コストでマクロ自動化可能。
- 案3: FMP MCP Server + Claude + OpenBBデータ。理由: FMPのMCPがClaudeに財務・経済イベントデータを即提供し、OpenBBで補完。APIラッパー不要で迅速構築でき、個人利用の無料枠内でマクロ・業界分析エージェントを運用しやすい。

4. 未確認・断定できない点
取得失敗

5. 使用ツール
web_search
