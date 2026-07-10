---
id: 20260710T111221Z-ai-office-x-trend
engine: hermes
status: ok
executed_at: 2026-07-10T12:17:08Z
duration_seconds: 131
---

**1. 今日見るべき話題**  
日本語圏では「AI社員」概念が爆発的に広がり、役割分担された複数AI（CFO・マーケ・開発など）をSlackで自律稼働させる事例が多数共有されている。英語圏では「AI employees / AI office」のビジュアライゼーションが注目で、My Virtual Office（エージェントがオフィス内を歩き回る2DリアルタイムUI）、Orbitagents（Claudeエージェント専用ライブダッシュボード・組織図）、Alook（階層型AI会社シミュレーター）などのOSS/ツールデモがバズ。QAチームやeコマース自動操縦の複数エージェント動画・ダッシュボード事例も活発。全体として「ログではなく可視化・観測可能性」がトレンド。

**2. 元ポスト/スレッドのURL（根拠）**  
- https://x.com/s_yudai_gifts/status/2075553166452527512（月5,000円で6体AI社員運用）  
- https://x.com/yuruo_xx/status/2075552583595196580（非エンジニアのAI社員活用）  
- https://x.com/kemorie71/status/2075551218915856559（AI社員の手順書失敗談）  
- https://x.com/DanKornas/status/2074551386390294909 および https://x.com/i/status/2074551386390294909（My Virtual Officeデモ・画像）  
- https://x.com/i/status/2074750734780792925（Orbitagentsダッシュボード）  
- https://x.com/i/status/2075123210870296723（Alook階層型AI会社）  
- https://x.com/i/status/2075357157671780473（7エージェントeコマースダッシュボード）  
- https://x.com/ClawHire/status/2075271517634498868、https://x.com/polsia/status/2075135376898105419 など（商用AI社員サービス）  
- https://x.com/i/status/2073989549815202089（Marktechpost OSSチュートリアル）  
その他リスク議論や@komatsufree / @ichiaimarketer の投稿群も関連。

**3. 言及されているツール・サービス・OSS名の一覧（分かる範囲で概要も）**  
- **My Virtual Office**（OSS、GitHub: eliautobot/my-virtual-office）：2Dブラウザ仮想オフィス。エージェントが歩き回り、リアルタイムステータス・ツール使用・チャット表示。OpenClaw/Hermes Agents/Codex/Claude Code対応、Docker自前ホスト、AGPL。  
- **Orbitagents**：Claudeエージェント専用OS/ダッシュボード。朝のレポート、ライブアクティビティ追跡、組織図、衝突検知。  
- **Alook**（ローカルファースト）：階層型AI会社シミュレーター。役割・マネージャー・インボックス定義、エージェント間メール連携、Claude Code/Codex/OpenCode対応。  
- **Marktechpost AI Agent Tutorial Library**（OSS、2.7K+ stars）：LangGraph/CrewAI/AutoGen/SmolAgentsなど複数エージェント実装のColabノートブック＋解説集。メモリ・推論・MCP・Agentic RAGなど網羅。  
- **ditto**（OSS）：Claude Code/Codexログから`you.md`プロファイル生成、他のエージェントがスタイルを即理解。  
- **Polsia / ClawHire / AIAGENTNET**（サービス）：役割別AI社員（受付・営業・経理など）提供、FlowPilot/AgentBayなど。  
- **その他フレームワーク/統合**：CrewAI、AutoGen、LangGraph（チーム指向）、FuseBase Dashboard MCP（ClaudeがDB/ダッシュボード直接操作）、LensDNA OS（リアルタイムブラウザ操作）、OpenTag（GitHub/Slack埋め込み）、OKX AI Agent Marketplace（オンチェーンエージェント経済）。  
- 日本語圏：Claude Projects/Code + SOUL.md/AGENTS.md/USER.mdテンプレート、Slack自動報告。

**4. 未確認・断定できない点**  
- 具体的なGitHubリポジトリの最新star数・コミット状況や本番稼働事例の詳細（スクリーンショット/動画の正確性）。  
- Orbitagents/Alook/My Virtual Officeの商用版有無や課金モデル、実際のユーザー数。  
- 日本語事例の多くがテンプレート販売（Brain）かどうかの確認。  
- MCPプロトコルやHermes Agentsなどの正確な実装詳細・互換性。  
- 動画デモの公開URLや長さ、実際に動いているかどうかの最新検証。

**5. 明日以降も追うべき項目**  
- @komatsufree / @ichiaimarketer / @s_yudai_gifts などのアカウント新投稿（失敗談・テンプレート更新）。  
- My Virtual Office / Alook / Orbitagents のGitHub更新と新デモ動画。  
- 「AI agents dashboard」「Claude employees visualization」「MCP AI office」などの追加検索。  
- 商用サービス（Polsia/ClawHire）のローンチ状況とユーザー反応。  
- 日本語 vs 英語圏の違い（コスト・文化面）とリスク議論の深掘り。  
- 新規OSS（Marktechpost系チュートリアル追加）やCrewAI/LangGraphのオフィス用途事例。

**6. 使用ツール**  
x_search（4回の並列クエリ：日本語キーワード、英語ビジュアライゼーション、multi-agent dashboard/Claude/GPT、OSS/implementation/demo）。
