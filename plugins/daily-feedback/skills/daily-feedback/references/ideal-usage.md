# 理想の Claude / Claude Code の使い方 — 評価基準リファレンス
（daily-feedback の3軸分析が参照する基準集。出典付き。2026-07-05 リサーチ実施）

## ① プロンプティング力

### 原則

- **明確さと精度**: 「Clearly articulates their requests when defining the task
  to a language-based AI. / Breaks down the task into small, manageable
  components as concise sentences.」（言語ベースのAIに対してタスクを定義する際、
  要求を明確に述べる。タスクを小さく管理可能な構成要素に分解し、簡潔な文章にする。）
  出典: [AI Prompt Writing Rubric: A Validity and Reliability Study - TOJET](https://www.tojet.net/)

- **具体的コンテキスト**: 「The more precise your instructions, the fewer
  corrections you'll need. Claude can infer intent, but it can't read your
  mind. Reference specific files, mention constraints, and point to example
  patterns.」（指示が正確であればあるほど、修正の必要は少なくなります。Claudeは
  意図を推論できますが、心を読むことはできません。特定のファイルを参照し、制約に
  言及し、例となるパターンを示してください。）
  出典: [Best practices for Claude Code - Claude Code Docs](https://code.claude.com/docs/en/best-practices)

- **検証手段の提供**: 「Include tests, screenshots, or expected outputs so
  Claude can check itself. This is the single highest-leverage thing you can
  do.」（テスト、スクリーンショット、期待される出力を含めることで、Claudeが
  自己チェックできるようにする。これは単独で最も効果の高いことです。）
  出典: [Claude Code プロンプト術 完全ガイド - Qiita](https://qiita.com/teppei19980914/items/61e77049f2f08a2a7b36)、
  [Best practices for Claude Code - Claude Code Docs](https://code.claude.com/docs/en/best-practices)（「信頼してから検証するギャップ」への対策として同旨）

- **動機・理由の説明**: 「Providing context or motivation behind your
  instructions, such as explaining to Claude why such behavior is important,
  can help Claude better understand your goals and deliver more targeted
  responses.」（指示の背景にある動機を提供すること、なぜその振る舞いが重要かを
  説明することは、Claudeが目標をより良く理解し、的を絞った回答を出す助けになる。）
  出典: [Claude Code プロンプト術 完全ガイド - Qiita](https://qiita.com/teppei19980914/items/61e77049f2f08a2a7b36)

- **構造化と例示**: 「XML tags help Claude parse complex prompts unambiguously
  / Include 3–5 examples for best results.」（XMLタグはClaudeが複雑なプロンプト
  を曖昧さなく解析するのに役立つ。最良の結果を得るために3〜5個の例を含める。）
  出典: [Claude Code プロンプト術 完全ガイド - Qiita](https://qiita.com/teppei19980914/items/61e77049f2f08a2a7b36)

### 良いプロンプト/悪いプロンプトの実例（Before→After）

- **テストの作成**
  ❌「add tests for foo.py」
  ✅「write a test for foo.py covering the edge case where the user is logged
  out. avoid mocks.」
  出典: [Best practices for Claude Code - Claude Code Docs](https://code.claude.com/docs/en/best-practices)

- **バグの修正**
  ❌「fix the login bug」
  ✅「users report that login fails after session timeout. check the auth
  flow in src/auth/, especially token refresh. write a failing test that
  reproduces the issue, then fix it」
  出典: [Best practices for Claude Code - Claude Code Docs](https://code.claude.com/docs/en/best-practices)

- **既存パターンの参照**
  ❌「add a calendar widget」
  ✅「look at how existing widgets are implemented on the home page to
  understand the patterns. HotDogWidget.php is a good example. follow the
  pattern to implement a new calendar widget...」
  出典: [Best practices for Claude Code - Claude Code Docs](https://code.claude.com/docs/en/best-practices)

### アンチパターン

- **キッチンシンクセッション**: 「You start with one task, then ask Claude
  something unrelated, then go back to the first task. Context is full of
  irrelevant information.」（1つのタスクで始め、無関係なことを尋ね、また最初の
  タスクに戻る。コンテキストが無関係な情報でいっぱいになる。）
  出典: [Best practices for Claude Code - Claude Code Docs](https://code.claude.com/docs/en/best-practices)

- **終わりのない修正の繰り返し**: 「Claude does something wrong, you correct
  it, it's still wrong, you correct again. Context is polluted with failed
  approaches.」（Claudeが間違え、修正し、まだ間違っており、また修正する。
  コンテキストが失敗したアプローチで汚染される。）
  出典: [Best practices for Claude Code - Claude Code Docs](https://code.claude.com/docs/en/best-practices)

- **信頼してから検証するギャップ**: 「Claude produces a plausible-looking
  implementation that doesn't handle edge cases. Fix: Always provide
  verification (tests, scripts, screenshots).」（もっともらしく見える実装を
  生成するがエッジケースを処理しない。対策：常に検証手段を提供する。）
  出典: [Best practices for Claude Code - Claude Code Docs](https://code.claude.com/docs/en/best-practices)

- **chatbotモード（毎回同じ説明の繰り返し）**: CLAUDE.md未整備のまま同じ背景説明
  を毎セッション繰り返す運用。X実践知として「.claude/フォルダ作成＋CLAUDE.md
  （/init活用）で永続メモリ化」が対策として挙げられている。
  出典（X）: https://x.com/swadeshkumar_/status/2040446579036082495

## ② コスト最適化

### モデル使い分け基準

- Sonnet 5が「安くて賢いスイートスポット」として主流。Haiku 4.5を軽量タスク・
  スクリーニングに、Opus 4.8/Fable 5を複雑計画・最終レビューに限定する階層運用。
  出典（X）: https://x.com/gensou_ai_/status/2073770131625574499、
  https://x.com/hanakoxbt/status/2073795018465087903

- orchestratorが判断してsubagentに安いモデルを委譲: 「For all coding tasks use
  your judgement to decide an appropriate lower power model and run that in a
  subagent.」
  出典（X）: https://x.com/i/status/2073774668159553737

- サブエージェントのモデルを環境変数で最安に固定する手法:
  「CLAUDE_CODE_SUBAGENT_MODEL=claude-haiku」
  出典（X）: https://x.com/eng_khairallah1/status/2048696032473522638

- 計画はOpus、実装はSonnetの`opusplan`的な使い分け（「planだけOpus、それ以外は
  基本Sonnet」）が推奨されているが、**未確認**: 具体的なコスト削減額はコードベース
  規模に依存し公式には数値化されていない。
  出典（X）: https://x.com/Mar_3simai/status/2073802937818824884／
  出典（NotebookLM要約, 未確認欄）: [Claude Code Best Practices - ClaudeFast](https://claudefa.st/blog/guide/development/agentic-engineering-best-practices)

### キャッシュ・コンテキスト管理

- 「prompt caching... can cut input costs by 90%」（プロンプトキャッシュは入力
  コストを90%削減しうる）
  出典（X）: https://x.com/Mar_3simai/status/2073802937818824884

- 「CLAUDE.md (or SKILL.md) files for persistent context... instead of
  rebuilding knowledge every session」（永続コンテキストとしてCLAUDE.md/SKILL.md
  を使い、毎セッションの知識再構築を避ける）
  出典（X）: https://x.com/Mar_3simai/status/2073802937818824884

- 「Grep before fetching and use selective tools (don't load 50 files for a
  30-line change)」（取得前にGrepし、選択的にツールを使う。30行の変更のために
  50ファイルを読み込まない）
  出典（X）: https://x.com/sairahul1/status/2073388319023755718

- コンテキストウィンドウ管理は根本原則: 「Most best practices are based on one
  constraint: Claude's context window fills up fast, and performance degrades
  as it fills. The context window is the most important resource to manage.」
  出典: [Best practices for Claude Code - Claude Code Docs](https://code.claude.com/docs/en/best-practices)

### 数値の目安（**未確認点あり**）

- CLAUDE.mdは150-200行以内を目安とする実践知（公式の厳密な行数基準ではない）。
  出典（X）: https://x.com/i/status/2068884177383047439
- 「/compactを60%使用時や通知で実行、auto_compactオン」という運用目安。
  **未確認**: モデルバージョンによる閾値の差異は未確認。
  出典（X）: https://x.com/u1/status/2073295840962302016
- 失敗事例: Deep-researchをFable 5 rawで実行し102 agents起動・224万subagent
  tokens・455 tool callsで、14分でMax 5xの93%を消費。教訓は「明示的に安いモデル
  への委譲を指示すること」。
  出典（X）: https://x.com/i/status/2073649148688306394
- 失敗事例: 高effort（Extra High）で複雑タスクを実行し2000万トークン消費。
  effortレベルと出力上限の事前制御が必要。
  出典（X）: https://x.com/eng_khairallah1/status/2048696032473522638
- **未確認**: Fable 5の正確なAPI価格（$10/M input / $50/M output 相当という
  言及あり）は投稿間で微妙に差異があり本リファレンスでは断定しない。

## ③ 運用場面の判断力

### セッション運用（/clear・compact・1タスク1セッション）

- 基本ワークフロー: 「Separate research and planning from implementation to
  avoid solving the wrong problem. The recommended workflow has four phases:
  1. Explore, 2. Plan, 3. Implement, 4. Commit」（研究と計画を実装から分離し、
  間違った問題を解決することを避ける。推奨ワークフローは探索・計画・実装・
  コミットの4フェーズ。）
  出典: [Best practices for Claude Code - Claude Code Docs](https://code.claude.com/docs/en/best-practices)

- コンテキスト・リセット（計画と実行の分離）: 「The Context Reset: planning and
  execution should happen in separate conversations. ... A fresh context with
  just the plan document means Claude starts execution with a clean mental
  model. No baggage from the planning phase.」（計画と実行は別々の会話で行う。
  計画書だけの新鮮なコンテキストで、実行をクリーンなメンタルモデルから開始する。）
  出典: [Claude Code Best Practices: 5 Agentic Engineering Techniques - ClaudeFast](https://claudefa.st/blog/guide/development/agentic-engineering-best-practices)

- 2回失敗したらやり直す鉄則: 「If you've corrected Claude more than twice on
  the same issue in one session, the context is cluttered with failed
  approaches. Run /clear and start fresh with a more specific prompt that
  incorporates what you learned.」（同じ問題を1セッションで2回以上修正したら、
  コンテキストは失敗したアプローチで乱雑。/clearして学びを反映した新しいプロンプト
  で始める。）
  出典: [Best practices for Claude Code - Claude Code Docs](https://code.claude.com/docs/en/best-practices)

- 修正よりリセット: 「Rewind > correct」という運用知。/rewindで失敗前のクリーン
  状態に戻すことを、修正の繰り返しより優先する。
  出典（X）: https://x.com/SteinAmour/status/2073799752018456640

### 機能の使い所（Plan mode・サブエージェント・スキル・フック・CLAUDE.md）

- Plan modeを非自明タスクで必ず使う: 「まだ書かないで。計画だけ立てて、質問して、
  承認を得てから実装して」「Shift+Tab または /plan でいきなりコードを書かせては
  いけません」。X実践知ではエラー削減効果も報告されているが、**未確認**: 具体的
  な削減率（80%等）は公式の定量データではなくX個別報告。
  出典（X）: https://x.com/Atenov_D/status/2051623265685180587

- サブエージェントによる調査の分離: 「Use subagents for investigation: They're
  useful for tasks that read many files or need specialized focus without
  cluttering your main conversation.」（多くのファイルを読む、あるいはメインの
  会話を乱さず特化した焦点が必要なタスクにサブエージェントを使う。）
  出典: [Best practices for Claude Code - Claude Code Docs](https://code.claude.com/docs/en/best-practices)

- 機能特化型サブエージェントを10-30個運用し、汎用サブエージェントより優先する
  （「feature-specific sub-agents rather than generic ones」）。
  出典（X）: https://x.com/heynavtoor/status/2050251853523456224

- コマンド化の鉄則: 「If you prompt something twice, it should be a command.
  Each command takes five minutes to write and saves hundreds of prompts over
  a project's lifetime.」（何かを2回プロンプトしたら、それはコマンドにするべき。
  各コマンドは書くのに5分かかるが、プロジェクトの存続期間中に何百ものプロンプト
  を節約できる。）
  出典: [Claude Code Best Practices: 5 Agentic Engineering Techniques - ClaudeFast](https://claudefa.st/blog/guide/development/agentic-engineering-best-practices)

- CLAUDE.mdは「憲法」として最小限に保つ: 「For each line, ask: "Would removing
  this cause Claude to make mistakes?" If not, cut it. Bloated CLAUDE.md files
  cause Claude to ignore your actual instructions!」（各行について「これを削除
  するとClaudeが間違いを犯すか？」と問い、そうでなければ削除する。膨らんだ
  CLAUDE.mdはClaudeに実際の指示を無視させる。）
  出典: [Best practices for Claude Code - Claude Code Docs](https://code.claude.com/docs/en/best-practices)

- CLAUDE.mdのGotchasセクションに recurring failure modes をログする運用知。
  出典（X）: https://x.com/i/status/2068884177383047439

- システム進化マインドセット: 「Every bug is a system failure, not a one-time
  mistake. ... after finishing each feature, ask Claude to review your rules
  and commands, ... 'Read CLAUDE.md and the commands we used. What rules or
  process changes would have prevented the issues we hit?'」（すべてのバグは
  システムの失敗であり一度限りの間違いではない。各機能完成後にClaudeへルールや
  コマンドをレビューさせ、再発防止のプロセス変更を問う。）
  出典: [Claude Code Best Practices: 5 Agentic Engineering Techniques - ClaudeFast](https://claudefa.st/blog/guide/development/agentic-engineering-best-practices)

- 週次のレトロスペクティブ: 「週次のふりかえりに『Claude Code活用レビュー』を
  5分追加するだけで、チーム全体のプロンプト品質が上がります。」
  出典: [Claude Codeベストプラクティス20選｜法人導入知見 - Uravation](https://uravation.com/media/claude-code-best-practices-top10-2026/)

## 採点ルーブリック（5点満点×3軸）

daily-feedback の SKILL.md 本体で使う採点基準。TOJETのタスク定義明確さ
ルーブリック、ResearchRubricsの重み付け（明確な要求+5／暗黙の要求+3／情報の統合
+4／引用の質+3／致命的欠陥-5）、グライスの公理（量・質・関連性・方法）、4要素
ブレ率（主語・責務・境界・例外のブレ）を材料に、daily-feedbackの3軸に翻訳した
具体的な状態記述。

### ① プロンプティング力

- **5点**: 依頼のほぼ全てで成果物・制約・完了条件を明確に述べ、ファイルパス・
  エラー全文・期待動作を最初から提供している（TOJETの「常に要求を明確に述べる」
  相当）。テストや期待出力など検証手段を自ら指定している。訂正（`user_interruptions`）
  がほぼ発生していない。1プロンプト1目的が守られている。
- **3点**: 大抵は明確だが、時々ファイルパスや制約が後出しになり1〜2往復の訂正が
  発生している（TOJETの「大抵は明確に述べる」相当）。検証手段の指定はまれ。
  複数依頼を1プロンプトに詰め込む場面が散見される。
- **1点**: 「いい感じにして」等、成果物・制約・完了条件のない丸投げが目立つ
  （TOJETの「要求が不明確」相当）。キッチンシンクセッションや、同じ問題への
  2回超の訂正（無限の修正ループ）が発生している。根拠となる引用ができない場合は
  この軸を「データ不足で評価不能」とする。

### ② コスト最適化

- **5点**: タスクの難易度に応じてモデルを使い分けている（定型処理はHaiku/
  Sonnet、計画や難問のみOpus/Fableに限定）。`cache_hit_pct` が高くセッションの
  切り方が適切。`compactions` がほぼ発生していない。出力トークンが突出せず
  簡潔。委譲時に安いモデルを明示指定している。
- **3点**: モデル選定に改善余地があるが、その他の管理（キャッシュ活用、セッション切り方）
  は優良な場合も含む。一部のタスクでモデル選定がタスク難易度と不整合
  （定型処理を上位モデルで実行等）だが、`cache_hit_pct` が高い、`compactions` が
  少ないなど、セッション管理が優秀な場合は3点（「モデル偏重だが他で補償」）。一方、
  モデル選定が適切でも `cache_hit_pct` がやや低い、`compactions` が数回発生している
  場合も3点（「バランスとれてやや低め」）。
- **1点**: ほぼ全タスクを最上位モデル（Opus/Fable）で実行し、かつセッション管理が
  不適切（`cache_hit_pct` <50%、`compactions` 3回超、出力トークン突出など）。
  または委譲プロンプトなしにサブエージェントを暴走させている（102 agents事例・
  高effort暴走事例に類する兆候）。

### ③ 運用場面の判断力

- **5点**: 非自明タスクでは必ずPlan mode・設計壁打ちを経てから実装している
  （Explore→Plan→Implement→Commitの4フェーズ相当）。大量・定型作業をサブ
  エージェントに委譲している。既存スキルの守備範囲はスキルを発動して使っている。
  同じ問題を2回超修正せず `/clear` で仕切り直している。繰り返し依頼はコマンド化・
  スキル化・Routine化を自ら提案または実行している。
- **3点**: 一部のタスクでPlan modeやサブエージェント委譲を使っているが、漏れが
  ある（大きい変更をいきなり実装する場面が時々ある）。既存スキルの活用に気づいて
  いない依頼が散見される。
- **1点**: 大きな変更でもPlan modeなしにいきなり実装し手戻りが発生している。
  大量作業をメインセッションで直列実行している（Agent tool未使用）。既存スキルの
  守備範囲を素の指示で毎回やり直している。同型の依頼を繰り返しても自動化を
  提案していない。

## 出典リスト

- [Best practices for Claude Code - Claude Code Docs](https://code.claude.com/docs/en/best-practices)（[日本語版](https://code.claude.com/docs/ja/best-practices)）
- [Claude Code Best Practices: 5 Agentic Engineering Techniques - ClaudeFast](https://claudefa.st/blog/guide/development/agentic-engineering-best-practices)
- [Claude Code プロンプト術 完全ガイド — Anthropic公式ベストプラクティス徹底解説 - Qiita (@teppei19980914)](https://qiita.com/teppei19980914/items/61e77049f2f08a2a7b36)
- [Claude Codeベストプラクティス20選｜法人導入知見 - 株式会社Uravation](https://uravation.com/media/claude-code-best-practices-top10-2026/)
- [AI Prompt Writing Rubric: A Validity and Reliability Study - TOJET](https://www.tojet.net/)
- [ResearchRubrics: A Benchmark of Prompts and Rubrics for Evaluating Deep Research Agents](https://arxiv.org/abs/2508.04183)
- [RUBICON: Rubric-Based Evaluation of Domain-Specific Human AI Conversations](https://doi.org/10.1145/3664646.3664778)
- [プロンプトの品質を定量化する ― 4要素ブレ率という指標の提案 - Zenn (cognitiveosmdl)](https://zenn.dev/cognitiveosmdl/articles/3e8a128bc1dfa7)
- X（Hermes x_search 経由。2026-07-05調査）:
  https://x.com/i/status/2068884177383047439 、 https://x.com/Atenov_D/status/2051623265685180587 、
  https://x.com/heynavtoor/status/2050251853523456224 、 https://x.com/u1/status/2073295840962302016 、
  https://x.com/SteinAmour/status/2073799752018456640 、 https://x.com/swadeshkumar_/status/2040446579036082495 、
  https://x.com/hanakoxbt/status/2073795018465087903 、 https://x.com/i/status/2073774668159553737 、
  https://x.com/Mar_3simai/status/2073802937818824884 、 https://x.com/sairahul1/status/2073388319023755718 、
  https://x.com/zephyr_z9/status/2041855450166259963 、 https://x.com/i/status/2073649148688306394 、
  https://x.com/gensou_ai_/status/2073770131625574499 、 https://x.com/eng_khairallah1/status/2048696032473522638

**注記**: `cc-cost-ops-web.md`（NotebookLM, Web全般の運用コスト調査）は初回・再実行
（v2, 2026-07-06実行）とも実機の NotebookLM 認証切れ（`notebooklm login` 要再認証）
によりエラースタブのため本リファレンスでは未使用。統合内容自体は X 由来の
`cc-cost-x-tips.md`（本ファイル ②コスト最適化節に反映済み）でカバーされているため、
NotebookLM 側の再実行は必須ではない。実機で再認証済みなら追加裏取りとして歓迎。
