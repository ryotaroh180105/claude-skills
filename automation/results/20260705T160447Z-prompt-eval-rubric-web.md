---
id: 20260705T160447Z-prompt-eval-rubric-web
engine: notebooklm
status: ok
executed_at: 2026-07-05T16:51:38Z
duration_seconds: 101
---

### research pass (source add-research)
Starting fast research on web...
Task ID: 343c37f1-9b39-4f86-94a0-a40dd496e18b

Found 10 sources
┌──────────────────────────────────┬──────┬───────────────────────────────────┐
│ Title                            │ Type │ URL                               │
├──────────────────────────────────┼──────┼───────────────────────────────────┤
│ PEEM: Prompt Engineering         │ Web  │ https://arxiv.org/pdf/2603.10477  │
│ Evaluation Metrics for In        │      │                                   │
│ プロンプト評価メトリクス：Pass   │ Web  │ https://www.promptquorum.com/ja/… │
│ Rate・BLEU・LLM-as-Judge（2026 … │      │                                   │
│ -                                │      │                                   │
│ How to Write an LLM Evaluation   │ Web  │ https://www.twine.net/blog/how-t… │
│ Rubric - Twine Blog              │      │                                   │
│ プロンプトの品質を定量化する ―   │ Web  │ https://zenn.dev/cognitiveosmdl/… │
│ 4要素ブレ率という指標の提案 -    │      │                                   │
│ Zenn                             │      │                                   │
│ ルーブリック作成ガイド           │ Web  │ https://wnpspt.waseda.jp/teacher… │
│ Evaluating and Improving Prompt  │ Web  │ https://scholarspace.manoa.hawai… │
│ Quality in LLM-Bas               │      │                                   │
│ Less Back-and-Forth: A           │ Web  │ https://arxiv.org/pdf/2605.20149  │
│ Comparative Study of Struct      │      │                                   │
│ LLM-based Automated Grading with │ Web  │ https://arxiv.org/pdf/2504.05239? │
│ Human-in-the-Loop                │      │                                   │
│ Prompt Testing and Validation    │ Web  │ https://zenvanriel.com/ai-engine… │
│ Frameworks: A Produc             │      │                                   │
│ OpenAI Prompt Engineering Guide  │ Web  │ https://www.scribd.com/document/… │
│ | PDF | Apollo 11                │      │                                   │
└──────────────────────────────────┴──────┴───────────────────────────────────┘
Imported 9 sources

### grounded answer (ask)
Answer:
AI（特に Claude Code 
等のコーディングエージェント）への指示・プロンプトの品質を事後評価するための基
準・ルーブリックについて、公式ドキュメント、研究記事、技術ブログ等の情報を整理
・引用し、回答します。

### 1. 要点
*   **良いプロンプトの5大要素**: 
「具体的コンテキスト」「検証手段の提供」「XMLタグによる構造化」「Few-shot（3-5
個の例示）」「動機・理由の説明」が共通して挙げられています [1-4]。
*   **多角的な評価尺度**: 
単なる正解率だけでなく、「正確性」「簡潔性」「ハルシネーションの程度」といった
汎用指標から、対話の質を測る「グライスの公理」、さらに指示の「ブレ率」といった
独自の定量化指標まで提案されています [5-8]。
*   **人間側の典型的な失敗**: 
複数のタスクを混在させる「キッチンシンクセッション」、失敗した修正案で履歴を汚
染する「無限の修正」、ルールが多すぎて機能しない「CLAUDE.mdの肥大化」が繰り返し
指摘されています [1, 2, 9, 10]。
*   **改善の取り組み**: 
失敗を「システムの欠陥」と捉え、再発防止策をCLAUDE.mdやカスタムコマンドに即時反
映させる「自己進化型」の運用や、週次のレトロスペクティブでの共有が有効とされて
います [11-14]。

---

### 2. 引用可能な原文抜粋

#### 問い1：良いプロンプトの構成要素
公式・専門家は以下の要素を「良いプロンプト」の定義として挙げています。

*   **明確さと精度（Clarity and Precision）**
    「Clearly articulates their requests when defining the task to a 
language-based AI. / Breaks down the task into small, manageable components as 
concise sentences.」
    （言語ベースのAIに対してタスクを定義する際、要求を明確に述べる。 / 
タスクを小さく管理可能な構成要素に分解し、簡潔な文章にする。）
    出典: [AI Prompt Writing Rubric: A Validity and Reliability 
Study](https://www.tojet.net/) [15, 16]
*   **具体的コンテキスト（Specific Context）**
    「The more precise your instructions, the fewer corrections you'll need. 
Claude can infer intent, but it can't read your mind. Reference specific files,
mention constraints, and point to example patterns.」
    （指示が正確であればあるほど、修正の必要は少なくなります。Claudeは意図を推
論できますが、心を読むことはできません。特定のファイルを参照し、制約に言及し、
例となるパターンを示してください。）
    出典: [Best practices for Claude Code - Claude Code 
Docs](https://code.claude.com/docs/en/best-practices) [1, 17]
*   **検証手段の提供（Verification Means）**
    「Include tests, screenshots, or expected outputs so Claude can check 
itself. This is the single highest-leverage thing you can do.」
    （テスト、スクリーンショット、または期待される出力を含めることで、Claudeが
自己チェックできるようにします。これは、あなたができる単独で最も効果の高いこと
です。）
    出典: [Claude Code プロンプト術 完全ガイド - 
Qiita](https://qiita.com/teppei19980914/items/61e77049f2f08a2a7b36) [2, 18]
*   **動機と理由の説明（Motivation and Reasoning）**
    「Providing context or motivation behind your instructions, such as 
explaining to Claude why such behavior is important, can help Claude better 
understand your goals and deliver more targeted responses.」
    （指示の背景にあるコンテキストや動機を提供すること、例えばなぜそのような振
る舞いが重要なのかをClaudeに説明することは、Claudeがあなたの目標をより良く理解
し、より的を絞った回答を出すのに役立ちます。）
    出典: [Claude Code プロンプト術 完全ガイド - 
Qiita](https://qiita.com/teppei19980914/items/61e77049f2f08a2a7b36) [2, 19]
*   **構造化と例示（Structure and Examples）**
    「XML tags help Claude parse complex prompts unambiguously / Include 3–5 
examples for best results.」
    （XMLタグはClaudeが複雑なプロンプトを曖昧さなく解析するのに役立ちます。 / 
最良の結果を得るために、3〜5個の例を含めてください。）
    出典: [Claude Code プロンプト術 完全ガイド - 
Qiita](https://qiita.com/teppei19980914/items/61e77049f2f08a2a7b36) [2, 20, 21]

#### 問い2：採点・評価の観点
AIとのやり取りを評価する際、以下の尺度が提案されています。

*   **LLM-as-a-Judgeの汎用指標**
    「Conciseness（簡潔性）: 
提示された質問に直接的かつ簡潔に答え、不必要・無関係・過剰な詳細を含んでいない
か。 / Correctness（正確性）: 
正解データに含まれるすべての重要な事実を含んでおり、かつ生成された各事実がいず
れも正解データまたは常識的な知識によって事実的に裏付けられているかを評価する。
」
    出典: [LLMプロダクトの評価はどう考えてどうやればいいの？ - 
Zenn](https://zenn.dev/gvatech_blog/articles/7ff1d69682a415) [5, 22]
*   **対話の質を測る「グライスの公理（Gricean maxims）」**
    「These rational principles for improving conversation quality are 
encapsulated within four maxims: quantity, quality, relevance, and manner.」
    （会話の質を向上させるためのこれらの合理的原則は、4つの公理に集約されます：
量、質、関連性、方法。）
    出典: [RUBICON: Rubric-Based Evaluation of Domain-Specific Human AI 
Conversations](https://doi.org/10.1145/3664646.3664778) [6, 23]
*   **指示の構造的品質「4要素ブレ率」**
    「主語のブレ：立場や文脈がブレていないか / 
責務のブレ：タスクの定義が途中で変わっていないか / 
境界のブレ：スコープが拡散・収縮していないか / 
例外のブレ：不確実性の処理が一貫しているか」
    出典: [プロンプトの品質を定量化する ― 4要素ブレ率という指標の提案 - 
Zenn](https://zenn.dev/cognitiveosmdl/articles/3e8a128bc1dfa7) [24, 25]

#### 問い3：AIの出力が悪くなる典型パターン（アンチパターン）
人間側の指示に起因する失敗として、公式等が警告しているものです。

*   **キッチンシンクセッション（The kitchen sink session）**
    「You start with one task, then ask Claude something unrelated, then go 
back to the first task. Context is full of irrelevant information.」
    （一つのタスクから始め、次に無関係なことをClaudeに聞き、それから最初のタス
クに戻る。コンテキストが無関係な情報でいっぱいになる。）
    出典: [Best practices for Claude 
Code](https://code.claude.com/docs/en/best-practices) [1, 26]
*   **修正の繰り返し（Correcting over and over）**
    「Claude does something wrong, you correct it, it's still wrong, you 
correct again. Context is polluted with failed approaches.」
    （Claudeが何かを間違え、あなたがそれを修正し、それでもまだ間違っており、あ
なたが再び修正する。コンテキストが失敗したアプローチで汚染される。）
    出典: [Best practices for Claude 
Code](https://code.claude.com/docs/en/best-practices) [1, 26]
*   **肥大化したCLAUDE.md（The over-specified CLAUDE.md）**
    「If your CLAUDE.md is too long, Claude ignores half of it because 
important rules get lost in the noise.」
    （CLAUDE.mdが長すぎると、重要なルールがノイズの中に埋もれてしまうため、Clau
deはその半分を無視する。）
    出典: [Best practices for Claude 
Code](https://code.claude.com/docs/en/best-practices) [1, 26]

#### 問い4：改善・振り返りの取り組み（レトロスペクティブ）
AI活用を進化させるための具体的な事例です。

*   **システムの進化マインドセット（System Evolution Mindset）**
    「Every bug is a system failure, not a one-time mistake. The difference 
between good and great agentic engineering is whether you fix the instance or 
fix the system. ... after finishing each feature, ask Claude to review your 
rules and commands, ... 'Read CLAUDE.md and the commands we used. What rules or
process changes would have prevented the issues we hit?'」
    （すべてのバグはシステムの失敗であり、一度限りの間違いではありません。優れ
たエージェントエンジニアリングと偉大なそれとの違いは、個別の事例を直すのか、シ
ステムを直すのかにあります。……各機能を完成させた後、Claudeにルールやコマンドを
レビューさせ、「CLAUDE.mdと使用したコマンドを読んで。私たちが直面した問題を未然
に防ぐために、どのようなルールやプロセスの変更が必要だった？」と尋ねます。）
    出典: [Claude Code Best Practices: 5 Agentic Engineering 
Techniques](https://claudefa.st/blog/guide/development/agentic-engineering-best
-practices) [12]
*   **週次のレトロスペクティブ**
    「週次のふりかえりに『Claude 
Code活用レビュー』を5分追加するだけで、チーム全体のプロンプト品質が上がります。
」
    出典: [Claude Codeベストプラクティス20選｜法人導入知見 - 
Uravation](https://uravation.com/media/claude-code-best-practices-top10-2026/) 
[13, 27]

---

### 3. ルーブリック実例

#### 開発・検証済み分析ルーブリック（プロンプト作成スキル評価用）
以下の構造で、人間がAIに与える指示の質を採点します。
| 評価次元 | Excellent (4) | Proficient (3) | Basic (2) | Needs Improvement (1)
|
| :--- | :--- | :--- | :--- | :--- |
| **タスク定義の明確さ** | 
常に要求を明確に述べる。要求を小さく簡潔な文に分解する。 | 
大抵は明確に述べる。通常は分解する。 | 時々明確に述べる。分解が不十分。 | 
要求が不明確。分解されず長く理解困難な一文。 |
| **プロファイル作成** | 適切な役割（プロファイル）を作成し、詳細を追加する。 |
プロファイルを作成し、一部の詳細を追加する。 | 
プロファイルはないがタスクは明確。 | プロファイルがなく、タスクも不明確。 |
| **出力の精緻化** | 生成物を常に評価し、改善のためのフォローアップを行う。 | 
通常は評価し、フォローアップを行う。 | 時々評価する。 | 
生成物を評価せず、そのまま使用する。 |

出典: [AI Prompt Writing Rubric: A Validity and Reliability 
Study](https://www.tojet.net/) を基に構成 [15, 28-36]

#### リサーチエージェント評価用ルーブリック（成果物評価用）
| カテゴリ | 重み | 内容（チェック項目） |
| :--- | :--- | :--- |
| **明確な要求 (Explicit)** | +5 | 
プロンプトで明示的に求められたすべての点に正しく回答しているか。 |
| **暗黙の要求 (Implicit)** | +3 | 
専門家が当然期待する、明示されていない補足情報（コスト、副作用、代替案等）が含
まれているか。 |
| **情報の統合 (Synthesis)** | +4 | 
単なる事実の羅列ではなく、複数の情報源を論理的に結びつけて結論を導いているか。 
|
| **引用の質 (References)** | +3 | 
出典が具体的で関連性があり、主張を実際に裏付けているか。 |
| **致命的な欠陥 (Negative)** | -5 | 
倫理的に問題がある、または核心的な推論が完全に誤っている。 |

出典: [ResearchRubrics](https://arxiv.org/abs/2508.04183) を基に構成 [37-44]

---

### 4. 出典リスト
*   [Best practices for Claude Code - Claude Code 
Docs](https://code.claude.com/docs/en/best-practices)
*   [AI Prompt Writing Rubric: A Validity and Reliability Study - Turkish 
Online Journal of Educational Technology](https://www.tojet.net/)
*   [PEEM: Prompt Engineering Evaluation Metrics for Interpretable Joint 
Evaluation of Prompts and Responses - arXiv](https://arxiv.org/abs/2512.01234)
*   [ResearchRubrics: A Benchmark of Prompts and Rubrics for Evaluating Deep 
Research Agents - Scale AI](https://arxiv.org/abs/2508.04183)
*   [RUBICON: Rubric-Based Evaluation of Domain-Specific Human AI Conversations
- Microsoft](https://doi.org/10.1145/3664646.3664778)
*   [Claude Code プロンプト術 完全ガイド — 
Anthropic公式ベストプラクティス徹底解説 - Qiita 
(@teppei19980914)](https://qiita.com/teppei19980914/items/61e77049f2f08a2a7b36)
*   [LLMプロダクトの評価はどう考えてどうやればいいの？ - Zenn 
(ojapi)](https://zenn.dev/gvatech_blog/articles/7ff1d69682a415)
*   [プロンプトの品質を定量化する ― 4要素ブレ率という指標の提案 - Zenn 
(cognitiveosmdl)](https://zenn.dev/cognitiveosmdl/articles/3e8a128bc1dfa7)
*   [Claude Code Best Practices: 5 Agentic Engineering Techniques - 
ClaudeFast](https://claudefa.st/blog/guide/development/agentic-engineering-best
-practices)
*   [Claude Codeベストプラクティス20選｜法人導入知見 - 
株式会社Uravation](https://uravation.com/media/claude-code-best-practices-top10
-2026/)

---

### 5. 未確認・断定できない点
*   **各プラクティスの定量的な寄与度**: 
「XMLタグを使用すると精度が○％上がる」といった数値は一部の報告（質問を末尾に置
くと最大30％向上など [2, 
21]）を除き、多くは定性的な「ベストプラクティス」としての推奨に留まっています。
*   **エージェント間のルーブリックの共通性**: 提供された資料は主に Claude や 
GPT 
系を対象としており、軽量モデルや特化型エージェントにおいて全く同じルーブリック
が同等の信頼性を持つかは個別に検証が必要です。
*   **日本語特有の評価基準**: 
日本語の助詞の使い方や敬語表現がプロンプト品質に与える影響についての詳細な「逐
語引用可能な」研究は、本ソース範囲内では限定的です。

Conversation: 4be7a6c9-956c-411e-af91-468e744b4ec4 (turn 1)
