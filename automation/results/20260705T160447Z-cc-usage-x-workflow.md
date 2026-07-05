---
id: 20260705T160447Z-cc-usage-x-workflow
engine: hermes
status: ok
executed_at: 2026-07-05T16:51:38Z
duration_seconds: 100
---

1. 今日見るべき話題（発見した実践知の要点）

Claude Codeの運用で最も強調されているのは「プロンプト力より運用設計」。CLAUDE.mdをプロジェクト永続メモリとして短く保ち（150-200行以内）、Plan Modeを非自明タスクで必ず使い、/compactでコンテキスト劣化を防ぎ、/rewindで失敗修正ではなくクリーンリセットを優先する。サブエージェントは機能特化型を10-30個作り、メイン（Planner）と並列実行させるパターンが主流。初心者アンチパターンは「chatbotモード」（毎回同じ説明を繰り返す）と「修正前進」（失敗を直しながら進める）で、上級者はCLAUDE.mdのGotchasセクションとphase-gated計画で防いでいる。日本語コミュニティでも「.claude/フォルダ整備＋CLAUDE.md＋Plan Mode＋auto_compact」の初期セットアップが1ヶ月後の速度を3倍変えると指摘されている。

2. 元ポスト/スレッドのURL（根拠。主張ごとに1つ）

- CLAUDE.mdの短さ・Gotchasセクション：https://x.com/i/status/2068884177383047439
- Plan ModeのShift+Tabとエラー80%削減効果：https://x.com/Atenov_D/status/2051623265685180587
- サブエージェントの機能特化と10-30個運用：https://x.com/heynavtoor/status/2050251853523456224
- /compactの60%使用時実行とauto_compact：https://x.com/u1/status/2073295840962302016
- サブエージェント階層（Planner→Sonnet並列）とコマンド優先：https://x.com/SteinAmour/status/2073799752018456640
- アンチパターン（chatbotモードとcontext rot）：https://x.com/swadeshkumar_/status/2040446579036082495
- 日本語コミュニティのCLAUDE.md設計例：https://x.com/yuruo_xx/status/2073771088408973587

3. 具体的なテクニック・プロンプト例（投稿内で共有されていた原文をなるべくそのまま「」で引用）

- CLAUDE.md設計：「プロジェクトの目的・非機能要件、アーキテクチャ原則・優先順位、コーディング規約、Hook（必ず実行させる処理）、トーン・禁止事項、参照すべき別ファイルへのリンク」を入れ、「絶対に短く（目標150-200行以内）」「Gotchasセクションにモデルの recurring failure modes をログ」。
- Plan Mode：「まだ書かないで。計画だけ立てて、質問して、承認を得てから実装して」「Shift+Tab または /plan でいきなりコードを書かせてはいけません」。
- Compact運用：「通知が来たら /compact-prep → /compact」「/status で使用量を確認しながら定期実行」。
- サブエージェント：「メイン（Planner）：Fable/Opusで全体計画・orchestrate」「サブエージェント：Sonnetなどで個別実装・レビュー・テストを並列化」「feature-specific sub-agents rather than generic ones」。
- プロンプト衛生：「Give problems, not commands. Make it reason out loud and ask questions until it's highly confident」「Rewind > correct」。
- 日本語例：「リプ下書きを生成したら、必ず会長くんのトンマナと照合せよ」のような1行Hookルール。

4. アンチパターン集（悪い例→良い例の形で）

- 悪い：「毎回同じ説明を繰り返すchatbotモードでCLAUDE.mdなし」→ 良い：「.claude/フォルダ作成＋CLAUDE.md（/init活用）で永続メモリ化」。
- 悪い：「失敗したら修正前進でcontext rotを放置」→ 良い：「/rewindで失敗前のクリーン状態に戻す」。
- 悪い：「長時間セッションで300-400kトークン超えまで放置」→ 良い：「/compactを60%使用時や通知で実行、auto_compactオン」。
- 悪い：「いきなり実装させてPlan Modeをスキップ」→ 良い：「Shift+Tabで計画・質問・承認ループを必須化」。
- 悪い：「汎用的なBackend Engineerサブエージェントを使う」→ 良い：「Payment Flow Specialistのような機能特化型にし、コマンドを優先」。
- 悪い：「CLAUDE.mdを長文で詰め込み無視される」→ 良い：「150-200行以内のcheat sheet＋Gotchasセクションに定期監査」。
- 悪い：「vanillaで小タスクでも複雑ワークフローを強いる」→ 良い：「小タスクはvanilla、複雑タスクのみsubagent/harnessを使う」。

5. 未確認・断定できない点

- 具体的なCLAUDE.mdテンプレート全文や日本語投稿者の実例スレッドの生テキストはツール結果の要約ベースで完全引用できず。
- /clearと/compactの正確なトークン閾値（60%など）は複数の投稿で言及されているが、モデルバージョンによる差異は未確認。
- サブエージェントの最大階層（5階層程度）や具体的な.skills/hooks配置パスはコミュニティ傾向として出てきたが、公式ドキュメントとの整合は未確認。
- 日本語投稿の生URL（@kawai_designなど）は要約内で言及されたが、個別ポストの直接内容は検索結果の合成に基づく。

6. 明日以降も追うべき項目

- 「claude-code-best-practice」リポジトリの最新更新とBoris Cherny関連スレッド。
- /ecc（Everything Claude Code）やSpec Kit、Matt Pocock-styleワークフローの具体的なコマンド例。
- 日本語ユーザー（@kawai_design、@akaoniudetate、@tsuntsun2914など）のCLAUDE.md実例スレッドとHook設定例。
- Git worktrees＋subagent並列運用の失敗事例と成功パターン。
- 2026年新コマンド（/fast、/model、/memory）の実践報告とcontext hygieneのトークン実測値。
- 初心者から上級者への移行事例（特に「plan modeを習慣化するまで」の壁）。
