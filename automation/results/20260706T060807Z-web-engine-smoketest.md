---
id: 20260706T060807Z-web-engine-smoketest
engine: hermes
status: ok
executed_at: 2026-07-06T06:14:59Z
duration_seconds: 121
---

**1. 要点（3〜5個、各項目に出典URL）**

- Claude Codeの`/loop`コマンドは、CLIセッション内でプロンプトを指定した間隔（1分〜最大3日）で繰り返し実行するスケジューラー機能で、セッションスコープ内で動作し、セッション終了時に停止する。出典: https://www.developersdigest.tech/blog/claude-code-loops / https://www.mindstudio.ai/blog/what-is-claude-code-loop-command-recurring-tasks
- 「Loop Engineering」とは、ユーザーが手動でプロンプトを繰り返し入力するのではなく、`/loop`やスケジュール、worktree、分離されたサブエージェント、検証ループなどを組み合わせたシステム全体を設計する手法で、Boris Cherny（Claude Code責任者）やPeter Steinbergerらが提唱。出典: https://addyosmani.com/blog/loop-engineering/ / https://docs.anthropic.com/en/docs/claude-code/common-workflows
- 効果的なループのベストプラクティスとして、自己検証（テスト/ビルド/リントの自動実行）、明確な成功条件の明記、worktreeによる並列セッション分離、CLAUDE.mdなどのコンテキストファイルの活用が挙げられる。出典: https://www.anthropic.com/engineering/claude-code-best-practices / https://docs.anthropic.com/en/docs/claude-code/common-workflows
- エージェントの基盤ループ（agentic loop）は「Receive prompt → Use tools → Process results → Repeat」のサイクルで、`/loop`はこの基盤ループを時間ベースで繰り返す上位レイヤーとして機能する。出典: https://code.claude.com/docs/en/agent-sdk/agent-loop
- 実践例として、PRレビュー自動化、ビルド失敗の継続監視、日次Git履歴サマリー作成などが挙げられ、外部cronよりセッションコンテキストを維持できる点が利点。出典: https://www.developersdigest.tech/blog/claude-code-loops

**2. 引用可能な原文抜粋（「」で逐語引用 + 出典URL）**

- 「Claude Code Loops are a native scheduling feature that lets you run recurring prompts at set intervals - from every minute to every three days. Unlike wrapping Claude Code in external cron jobs, loops maintain session context between runs, so the agent remembers what it did in previous iterations and can build on that work.」 出典: https://www.developersdigest.tech/blog/claude-code-loops
- 「The `/loop` command in Claude Code is a session-level scheduler. You give it a prompt and a cadence, and it queues that prompt to repeat at the interval you specify — without you having to reinitiate it manually each time.」 出典: https://www.mindstudio.ai/blog/what-is-claude-code-loop-command-recurring-tasks
- 「Loop engineering is replacing yourself as the person who prompts the agent. You design the system that does it instead.」 出典: https://addyosmani.com/blog/loop-engineering/
- 「When you start an agent, the SDK runs the same execution loop that powers Claude Code: Claude evaluates your prompt, calls tools to take action, receives the results, and repeats until the task is complete.」 出典: https://code.claude.com/docs/en/agent-sdk/agent-loop
- 「When writing prompts for scheduled tasks, be explicit about what success looks like and what to do with results. The task runs autonomously, so it can’t ask clarifying questions.」 出典: https://docs.anthropic.com/en/docs/claude-code/common-workflows

**3. 未確認・断定できない点**

- `/loop`の具体的なコマンド構文（例: `/loop 5m "prompt"`の正確な形式）や上限（3日）の公式詳細は検索スニペットのみで、公式ドキュメント全文が確認できなかった。
- 「Loop Engineering」という用語の公式定義やAnthropic公式ドキュメントでの言及はなく、主にAddy Osmani氏やMedium/ブログ記事での解釈・提唱に基づく。
- 実際のコスト、安定性（APIスパイク回避の10%オフセットなど）、worktreeとの組み合わせ時の具体的な失敗ケースはユーザー体験談中心で、公式ベンチマークは未確認。
- 2026年6-7月時点の機能であり、それ以降の変更やデスクトップアプリ版との違いは検索結果に含まれていない。

**4. 使用ツール:**  
web_search

（web_extractはAPI未設定のため実行失敗し、検索結果のスニペット・抜粋のみで統合）
