---
id: 20260710T111222Z-ai-office-implementation
engine: hermes
status: ok
executed_at: 2026-07-10T12:17:09Z
duration_seconds: 132
---

**1. 調査で分かったこと（実装アプローチの選択肢）**

複数のAIエージェント（Claude Code、CrewAI/LangGraph/AutoGenベースのLLMエージェントなど）の同時実行状況・タスク・ログを1画面でリアルタイム可視化するダッシュボードの自作は、既存OSSをベースにするか、最小構成でスクラッチ構築する2つの主なアプローチが現実的。

- **既存OSSダッシュボードを活用・拡張**: builderz-labs/mission-controlのようなself-hosted orchestration dashboardをベースに、Kanbanビュー・ライブフィード・コスト追跡を拡張。multiagent-visibility-toolのようなリアルタイムトレース/可視化ツールを組み合わせる。TheColony系やopen-multi-agentのようなプロジェクトも参考（PixiJSやWebSocketを使ったシミュレーション/ダッシュボード例あり）。
- **最小構成スクラッチ構築（FastAPI + Next.js中心）**: バックエンドでエージェントをサブプロセス/フレームワーク経由で実行し、構造化イベントをWebSocketでプッシュ。フロントでエージェントカード・ライブログ・ワークフローダイアグラムを表示。Agent-Dashboard（Lokesh-shiva）やcmhh22/agent-dashboard、yusuf-eren/openai-agents-js-ui-starterのようなテンプレートが近い。
- **可視化・状態管理**: 各エージェントの状態（running/completed/error）、タスク進捗、ツール呼び出し履歴を階層スパン（reasoning/tool/LLM呼び出し）として集約。リアルタイム更新はWebSocketが主流。
- **ログ集約**: フレームワーク（LangGraph/CrewAI）固有のトレースやカスタムJSONイベント（timestamp, agent_id, event_type, content, metadata）で集約。AgentTraceのようなスキーマ提案やOpenTelemetry活用例あり。Claude Code系はCLIラッパーやtmux/Zellijセッション監視でstdout/イベントを捕捉。
- **全体傾向**: 普遍的なログ標準は存在せず、フレームワーク依存 or カスタムJSON/OpenTelemetryが一般的。個人開発ではNext.js/FastAPI + WebSocketの組み合わせが最も再現性が高い。

**2. 参考URL（根拠、リポジトリ・記事URL）**

- https://github.com/builderz-labs/mission-control （self-hosted AI agent orchestration dashboard、Next.js/SQLite中心）
- https://github.com/hit1001/multiagent-visibility-tool （multi-agentリアルタイムトレース・可視化・デバッグ）
- https://github.com/Lokesh-shiva/Agent-Dashboard （React + FastAPI + WebSocket + Rechartsのmulti-agent analytics dashboard）
- https://github.com/cmhh22/agent-dashboard （Angular/FastAPI/LangChain + WebSocket streaming）
- https://github.com/yusuf-eren/openai-agents-js-ui-starter （Next.js + WebSocketでagent output/tool approval/handoff可視化）
- https://github.com/vstorm-co/full-stack-ai-agent-template （FastAPI + Next.js WebSocket streamingテンプレート）
- https://github.com/untra/operator （multi-agent orchestrationのリアルタイムダッシュボード要素、TUI寄りだが参考）
- 関連記事: GitHub Agent HQ/Mission Control系解説、LangGraph/CrewAI/AutoGen比較記事群（observability/dashboard言及）

**3. 実装に使える技術要素・切り口**

- **フロントエンド可視化**: Next.js/React 18/19 + TypeScript + Tailwind/shadcn/ui、Recharts/Chart.js/D3.js（メトリクス・タイムライン）、React Flow or Mermaid（ワークフローダイアグラム）、PixiJS（高度なエージェントシミュレーション可視化）。
- **バックエンド状態管理・ログ収集**: FastAPI（Python、WebSocketネイティブ、エージェント実行に強い）または Next.js API/Node。エージェントはLangGraph/CrewAI/AutoGenまたはサブプロセス（Claude Code CLIラッパー）で起動。イベントをRedis/キュー経由 or 直接WebSocketで集約。
- **リアルタイム更新**: WebSocket（FastAPI/Next.js双方で容易）。SSEも代替可。エージェント側で構造化イベント（JSON: {agent_id, timestamp, type: "task_start/tool_call/message", payload}）を発行。
- **集約・オーケストレーション**: LangGraph（グラフ可視化・トレース強い）、CrewAI（role-based crew + 企業版dashboard）、AutoGen（柔軟）。ログは階層スパン（cognitive/operational/contextual）やOpenTelemetry。Claude Codeなどは専用モニター（tmux/cmuxラッパー）でセッション状態を捕捉。
- **最小スタート切り口**: Next.js + FastAPIテンプレートをクローン → WebSocketエンドポイント追加 → エージェントをバックグラウンド実行しイベントemit → フロントでライブ更新UI（カード + ログストリーム + 簡易グラフ）。

**4. 未確認・断定できない点**

- 各OSSリポジトリの正確な内部実装詳細（具体的なWebSocketメッセージフォーマットやClaude Code統合方法）は検索スニペットのみで、コード全文未確認。
- 普遍的な「エージェントログ標準フォーマット」の採用状況（AgentTrace提案は学術寄り）。実務ではフレームワーク固有 or カスタムJSONが主流だが、相互運用性は低い可能性。
- 大規模（数十エージェント同時）時のスケーラビリティ（WebSocket接続数、ログ量）や具体的なコスト/パフォーマンス数値。
- 最新のClaude Code専用モニタリングツールの成熟度（トピック検索で言及多数だが詳細未深掘り）。

**5. 明日以降も追うべき項目**

- 主要リポジトリのREADME/コード詳細確認（mission-control、multiagent-visibility-tool、Agent-Dashboard）。
- Langfuse/Phoenix/Arize Phoenixなどのself-hosted LLM observabilityツールとの統合可能性。
- React Flow + LangGraph可視化例や、Claude Code / OpenCode専用dashboard（claude-code-monitor系）の最新動向。
- WebSocket vs SSEの性能比較、またはRedis Streamsを使ったログ集約パターン。
- 個人最小構成のサンプルコード（FastAPI WebSocket + 複数サブプロセスエージェント）の動作検証。

**6. 使用ツール**  
web_search

（複数回のWeb検索により上記情報を収集）
