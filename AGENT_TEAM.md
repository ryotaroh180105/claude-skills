# AGENT_TEAM.md — マルチエージェント運用規約

## 1. 適用範囲

- 本規約は、このリポジトリで Agent ツール（サブエージェント）を1体以上起動する
  セッションに適用する。サブエージェントを使わない単独セッションでは、
  章3の所有権表のみ尊重し、章4の宣言プロトコルは不要。
- ユーザー（Ryo）本人の直接編集は常に最優先で、本規約の制約を受けない。

## 2. 役割定義とフレームワーク選択

### 役割表

| 役割 | 担当モデル/主体 | 責務 | 禁止事項 |
|---|---|---|---|
| リーダー（ディレクター） | Fable 5（〜2026-07-07）/ Opus 4.8（以降） = メインセッション | 要件定義、デザイン方向性の言語化、タスク分割と割当、全体QA、コミット/push、red-team 指摘の採択/棄却 | 実装の丸抱え（設計書を書かずに自分で実装し続けること） |
| 実行部隊（implementer） | Sonnet 5（Agent ツール `model: sonnet`）/ Codex（外部・任意） | 割当プロンプトと設計書どおりの実装。並列稼働可 | コミット/push、許可リスト外の書込、仕様の独自変更 |
| レッドチーム（red-team） | `.claude/agents/red-team.md`（model: inherit） | 失敗シナリオ3件＋早期警報サインの提示（章6） | 一切の書込、実装 |

### Claude Agent Teams / Claude Agent SDK 使い分け基準（この2条件だけで判定する）

| 判定条件 | 採用フレームワーク | 例 |
|---|---|---|
| 人間（Ryo）が同一セッション内で承認・方向修正に参加する、または1セッションで完結する | Claude Agent Teams（Claude Code 内蔵の Agent ツール。本規約の管轄） | LP作成、設計書レビュー、週次のSNS投稿バッチ |
| 人間不在で時刻トリガーにより繰り返し無人稼働する | Claude Agent SDK（Python）。本規約はファイル所有権のみ適用し、実装・設計は docs/designs/03-intel-hub.md（未作成）に委ねる | SNS収集・分析の日次無人実行 |

両方に該当する場合（対話で作った手順を後で無人化）は、まず Agent Teams で運用を安定させ、
loop-engineering スキルでループ設計書を作ってから SDK 化を検討する。

## 3. ファイル所有権表

スキーマ（4列固定）:

| 列名 | 値域 |
|---|---|
| パス | リポジトリルート相対の glob |
| 所有ロール | `leader` / `implementer（割当制）` / `user` |
| 並列書込 | `不可` / `割当時のみ可（同時1エージェント）` |
| 備考 | 自由記述1行 |

| パス | 所有ロール | 並列書込 | 備考 |
|---|---|---|---|
| CLAUDE.md | user | 不可 | 変更はユーザー承認必須 |
| MISTAKES.md | leader | 不可 | ミス記録はリーダーが同一セッション内で追記 |
| ROADMAP.md | leader | 不可 | 候補追記もリーダー経由 |
| marketplace.json | leader | 不可 | リリース操作の一部のためリーダー専有 |
| AGENT_TEAM.md | user | 不可 | 規約自体の変更はユーザー承認必須 |
| .claude/** | leader | 不可 | settings.json・hooks・agents 定義を含む |
| docs/** | leader | 不可 | 設計書・運用ドキュメント |
| plugins/** | implementer（割当制） | 割当時のみ可（同時1エージェント） | 割当単位は plugins/<プラグイン名>/ ディレクトリ |
| scripts/** | implementer（割当制） | 割当時のみ可（同時1エージェント） | 割当単位はファイル |
| sns/** | implementer（割当制） | 割当時のみ可（同時1エージェント） | 割当単位は sns/<アカウント名>/ ディレクトリ |

備考: 未収載パスは leader 所有とみなす。

## 4. 共有ファイル変更の宣言プロトコル

1. リーダーは Agent 起動前に、各実行エージェントに書き込ませるファイルの絶対パス一覧を確定し、所有権表と照合する。`leader` / `user` 所有のパスは実行エージェントに割り当てない。
2. 割当プロンプトの先頭に次の2行を必ず書く。
   `書込許可: <絶対パスまたはディレクトリのリスト>`
   `上記以外のファイルは変更禁止。変更が必要になったら変更せず最終報告で申告すること。`
3. 同一ファイル（または同一割当単位ディレクトリ）を2体以上の実行エージェントに同時に割り当てない。重なる場合は直列実行にする。
4. 実行エージェントは、許可リスト外の変更が必要と判明した時点でそのファイルに触れず、最終報告に「追加変更が必要: <パス> <理由1行>」を書いて返す。リーダーが自分で変更するか、再割当する。
5. 全エージェント完了後、リーダーが `git status` で変更ファイル一覧を許可リストの和集合と照合してからコミットする。リスト外の変更があれば revert し、MISTAKES.md に記録する。

## 5. オーケストレーター権限

- リーダー（メインセッション）のみが行えること: Agent の起動、所有権表で
  「leader」のファイルの書込、git commit / push、完了判定、成果物のマージ。
- 実行エージェント（implementer）が行えないこと: git commit / push、
  割当プロンプトの「書込許可:」リスト外のファイル変更、別エージェントの起動。
- red-team が行えないこと: あらゆるファイルの変更（読取専用）。

## 6. レッドチーム運用

- 必須実行タイミング（3つ）: ① docs/designs/ に新規設計書を書き終えた時
  ② marketplace.json への追記を含むコミット（新スキルのリリース）の前
  ③ ユーザーが「反証して」「レッドチームにかけて」と言った時。
- 起動方法: Agent ツールで subagent_type: red-team、プロンプトは
  「<対象ファイルの絶対パス> を読み、この計画が失敗するシナリオを
  確率が高い順に3つ挙げ、各シナリオの早期警報サインを提示せよ」。
- リーダーは各指摘に対し「採択（対応内容1行）」または「棄却（理由1行）」を
  同セッションの応答内に明記する。無言で流すことを禁止する。

## 7. チーム構成テンプレート

### 構成例1: 納品品質LP作成チーム

| 役割 | 主体 | 参照スキル | 書込許可 |
|---|---|---|---|
| ディレクター | リーダー（メインセッション） | lp-builder（ヒアリング・構成の型）、biz-ops-guard | docs/**、成果物マージ先 |
| デザイナー | Agent（general-purpose, model: sonnet） | lp-builder のコピー/構成指針（Frontend Design スキルは未導入のため lp-builder で代替） | 案件作業ディレクトリ内の design-spec.md 1ファイル |
| コーダー | Agent（general-purpose, model: sonnet）×最大2並列。Codex 併用は任意 | lp-builder の実装手順 | 案件作業ディレクトリ内の index.html（1体目）/ 画像・アセット（2体目）。同一ファイル重複禁止 |
| レッドチーム | red-team | — | なし（読取専用）。納品前に必須実行 |

### 構成例2: SNS運用・資産化チーム

| 役割 | 主体 | 参照スキル | 書込許可 |
|---|---|---|---|
| ディレクター | リーダー（メインセッション） | sns-ops-team（オーケストレーション手順） | sns/<アカウント名>/sns-strategy.md |
| リサーチャー | hermes-relay 経由の NotebookLM / Hermes x_search（CLAUDE.md の調査ルールどおり。Claude 自身の WebSearch は使わない） | hermes-x-search | automation/queries/pending/（hermes-relay ブランチ側） |
| アナリスト | Agent（general-purpose, model: sonnet） | twitter-intel（分析観点） | sns/<アカウント名>/ 配下の分析メモ1ファイル |
| ライター | Agent（general-purpose, model: sonnet） | sns-ops-team の執筆工程（voice-profile-extractor は未実装のため sns-strategy.md の文体欄で代替） | sns/<アカウント名>/post-queue.md |
| レッドチーム | red-team | — | なし（読取専用）。炎上リスク観点は red-team のユーザー視点ペルソナで実施 |

sns-ops-team との関係（確定）: sns-ops-team は置き換えない。同スキルの企画→リサーチ→執筆→レビュー→キュー出力の手順・テンプレはそのまま Doer として使い、AGENT_TEAM.md は「誰がどのファイルに書けるか」「誰が Agent を起動するか」だけを上位規約として統制する。矛盾が生じた場合は AGENT_TEAM.md が優先し、sns-ops-team 側の改修要否をユーザーに確認する。

### 構成例3: スキル量産チーム（docs/designs/15-agent-team-operations.md §5.3 が正）

複数の新スキル／設計書を、設計（Opus）→ 批判（red-team）→ 実装（Sonnet 並列）→ 統合（リーダー）の4フェーズで量産する構成。

| 役割 | 主体 | 参照スキル | 書込許可 |
|---|---|---|---|
| 設計 | リーダー（メインセッション = Opus）。並列で複数設計をこなす場合は設計対象ごとに別セッション | skill-design-rigor（計画ゲート・自己反証）、TEMPLATE.md | `docs/designs/**` |
| 実装1..N | Agent（general-purpose, model: sonnet）×N 並列 | repo-skill-creator（スキル雛形・導入確認）、対象設計書 | `plugins/<プラグイン名>/`（1体1ディレクトリ。重複禁止）／必要なら `scripts/<ファイル>` |
| レビュー | Agent（subagent_type: red-team） | — | なし（読取専用）。設計書完成時と marketplace.json 追記前に必須 |
| 統合 | リーダー（メインセッション） | model-switcher | `marketplace.json`、`ROADMAP.md`、`docs/designs/**`（ステータス更新）、`MISTAKES.md` |

起動順序（4フェーズ固定）:
1. **並列設計** — リーダー（Opus）が設計対象ごとに TEMPLATE.md で設計書を書く。1設計 = 1ファイル `docs/designs/NN-*.md`。
2. **red-team** — 各設計書完成時に `subagent_type: red-team` を対象パスを渡して起動し、失敗シナリオ3件に採択/棄却を明記（本ファイル章6）。
3. **並列実装** — 設計書ごとに Agent（model: sonnet）を割当。書込許可は `plugins/<各スキル名>/` に限定し、同一ディレクトリを2体に渡さない。実装セッションの開始プロンプトは 00設計書 §5.2 の定型文を使う。
4. **統合** — リーダーが `git status` を許可リスト和集合と照合（本ファイル章4 手順5）→ `python scripts/validate_skills.py` 通過確認 → marketplace.json へ一括登録 → red-team（リリース前）→ コミット/push。

実例と詳細（2026-07-06の初回適用・コミットハッシュ対応）は docs/designs/15-agent-team-operations.md §5.3 を参照。
