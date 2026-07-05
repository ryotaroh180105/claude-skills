---
id: 20260705T104716Z-loop-engineering-v2
status: ok
executed_at: 2026-07-05T10:50:02Z
duration_seconds: 130
---

1. 今日見るべき話題（ループエンジニアリングとは何か、なぜ話題か）
ループエンジニアリング（Loop Engineering）は、Prompt Engineeringや単発のAgentを超えた次の段階として2026年7月現在Xで急拡大中の概念。人間が毎回手動でプロンプト→レビュー→修正を繰り返すのではなく、「ループ全体を一度設計」してAgent（特にClaude Code）が自律的に計画・実行・検証・修正を繰り返す仕組みを指す。Boris Cherny（Claude Code担当）が「My job is to write loops」と発言したのが象徴で、AgentがAgentをプロンプトする時代へのシフトとして「Prompt EngineeringからLoop Engineeringへ」と話題に。生産性向上（PRの65%以上がClaude+loop由来など）の報告が相次ぎ、日本でもBusiness Insider Japanなどで「プロンプトを書かなくなる時代」「マネージャーでも活躍できる」と紹介され、Zenn/Qiitaでも拡散中。

2. 元ポスト/スレッドのURL（根拠）
- https://x.com/DAIEvolutionHub/status/2073659931778236750 （Loop Engineeringの全体像とBoris引用の主要スレッド）
- https://x.com/i/status/2073659931778236750 （同スレッドの続き、Maker-Checkerや外部状態の詳細）
- https://x.com/bcherny/status/2038454341884154269 （Boris本人の/loopコマンド言及）
- https://x.com/elorm_elom/status/2064005518343995588 （loops.elorm.xyz紹介）
- https://x.com/RoundtableSpace/status/2073478197123956973 （メインrepo言及）

3. 具体的なコツ・テクニック（箇条書き）
- Maker（実行Agent）とChecker（別モデルで検証）を分離（同一モデル自己批判は失敗しやすい）
- 外部状態管理（STATE.md、journal、.claude/配下のファイルでコンテキスト外に記憶）
- 明示的なExit Condition（pytest全パス + lint cleanなどbash exit code 0を必須に、max-turnsで無限防止）
- Verification Gateを多段に（compile → static analysis → test → fix → rerun）
- /loopや/loop 5m /babysitなどの専用コマンドで自律継続
- Token cap・human handoffゲートを最初に定義（高判断のみ人間にエスカレーション）
- Worktree分離やGitHub Actionsで安全にループ実行
- Multi-agent（spec writer + implementer + adversarial verifier）で品質向上

4. 関連する取得可能なスキル・ツール・リポジトリがあれば名前とURL
- Claude Code（Anthropic公式CLI、.claude/設定でloop対応）：https://claude.ai/code または公式ドキュメント
- loop-engineering（メインrepo、loop-init/audit CLI、Claude Code/Codex対応パターン多数）：https://github.com/cobusgreyling/loop-engineering
- loops.elorm.xyz（26以上の即コピー可能なloopテンプレート集）：https://loops.elorm.xyz
- .claude/ harnessパターン（CLAUDE.md + skills/ + commands/ + verifiers/）：複数のXスレッドで共有されているテンプレート構成

5. 未確認・断定できない点
- https://github.com/cobusgreyling/loop-engineeringのスター数や更新頻度の最新値
- Business Insider Japan記事の正確な公開日と内容詳細
- 日本語Zenn/Qiita記事の具体的なURLと推奨度
- 完全無人loopの実運用コスト爆発事例の有無と規模
- 他のモデル（Grok、Gemini、Ollama）での同等loop成功率の比較データ

6. 明日以降も追うべき項目
- Boris Chernyの新ポストやSequoiaトーク関連更新
- loop-engineering repoの新パターン追加（daily triage、changelog draftingなど）
- loops.elorm.xyzの新テンプレートや日本語対応状況
- 日本コミュニティ（Zenn/Qiita）の実践報告と失敗事例
- Claude Codeの新コマンド（/loop untilなど）の公式更新
- 観測ツール（Opikなど）やMCP統合の新repo出現
