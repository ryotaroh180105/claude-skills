# エージェントチーム運用の実践設計（AGENT_TEAM.md 実践編） 設計書

| 項目 | 値 |
|---|---|
| ステータス | 実装完了（2026-07-10）。Q1承認済み、AGENT_TEAM.md章7に構成例3（スキル量産チーム）を転記済み。Q2〜Q4は暫定運用のまま継続 |
| 種別 | ドキュメント（運用プロセス実践編） |
| 優先度 | Tier F-3 系列（02-agent-team.md の後続） |
| 実装モデル | Sonnet 5（推奨 effort: high。ただし本書の主成果は本ファイル自体） |
| 依存する設計書 | docs/designs/00-fable-sonnet-bridge.md（役割分担・effort 運用の前提）、docs/designs/02-agent-team.md（規約の元設計） |
| 依存する既存スキル | lp-builder（チーム①Doer）、sns-ops-team（チーム②Doer）、hermes-x-search（チーム②リサーチ経路）、skill-design-rigor（チーム③設計工程）、repo-skill-creator（チーム③実装工程）、model-switcher（モデル選択） |
| 依存する既存規約 | AGENT_TEAM.md（上位規約。本書はこれを具体運用に落とす。改訂は本書ではしない） |
| 外部依存 | なし（Codex は「任意スロット」の言及のみ。SDK 実装は本書対象外） |

## 0. 計画ゲート回答（00設計書 §5.1）

1. **最も確率の高い失敗パターン（3つ）**: ①本書と AGENT_TEAM.md の内容が重複し「どちらを見るか」が曖昧になる ②チーム構成の型が抽象的で実際の Agent 起動プロンプトに落とせない ③実在しないエージェント（frontend 等）を前提に手順を書き、そのまま実行して `Agent type not found` で失敗する。→ §8 に早期警報サインと対策を記載。
2. **スコープ境界**: AGENT_TEAM.md 本体の改訂（user 所有・承認必須）、sns-ops-team / lp-builder / skill-design-rigor の SKILL.md 改修、red-team.md の改訂、Claude Agent SDK（Python）の実装コード、Codex のセットアップ手順、hooks による機械強制 — はやらない（§2.2）。
3. **完成条件の真偽判定可能性**: 全項目を「本ファイルへの grep」「AGENT_TEAM.md との整合 grep」「起動プロンプトのウォークスルー観察」で判定できる形にした（§3）。
4. **実装者が最初に詰まる箇所**: チーム③（スキル量産）の起動順序と red-team の投入タイミング、frontend 不在時のデザイナー役の代替。→ §6 に確定フロー、§11 に判断ルールを記載。
5. **本当に必要か**: AGENT_TEAM.md は「誰がどのファイルに書けるか（所有権）」「誰が Agent を起動するか（権限）」を定めた規約で、02設計書はその規約自体の設計。両者に無いのは「規約を使った具体的なチーム編成の型（3種）・Agent ツールの実際の起動手順・並列設計→red-team→並列実装→統合という実運用フローの型・どのチームが Teams / SDK 向きかの確定判定」。この実践層が無いため、規約はあっても毎回ゼロから編成することになる。代替不可のため必要。

## 1. 目的・背景（Why）

AGENT_TEAM.md（規約）と 02-agent-team.md（規約の設計）は「所有権・宣言プロトコル・権限」という**静的なルール**を定めた。しかし実際にチームを動かすとき、リーダー（メインセッション = Opus）は毎回「どういう役割構成にするか」「Agent ツールをどの順で何体起動するか」「red-team をいつ挟むか」「成果物をどう統合するか」を判断する必要がある。この**動的な運用手順が未整備**だと、規約はあっても編成が属人的になり、並列実行の競合や統合漏れが起きる。

本書は AGENT_TEAM.md を前提に、①よく使う3種のチーム編成を確定値で型化し、②Agent ツールの実際の起動手順（宣言プロトコルの適用込み）を、③このリポジトリで 2026-07-06 に実際に回した「並列設計→red-team→並列実装→統合」を実例として抽出して定義する。使うのはこのリポジトリでサブエージェントを起動する全リーダーセッション。

## 2. スコープ

### 2.1 やること

- チーム構成の型を3種、確定値で定義する（§5.1〜5.3）。各型に「役割・主体・参照スキル・書込許可・起動順序」を明記する。
  - チーム① 納品品質LP作成チーム（AGENT_TEAM.md 構成例1 の実践展開）
  - チーム② SNS運用・資産化チーム（AGENT_TEAM.md 構成例2 = sns-ops-team の実装、の実践展開）
  - チーム③ スキル量産チーム（新規。今日の実例から抽出した型）
- Agent ツールの実際の起動手順を、宣言プロトコル（AGENT_TEAM.md 章4）の適用込みで定義する（§6）。
- 2026-07-06 にこのリポジトリで実行した「並列設計→red-team→並列実装→統合」を型として抽出し、チーム③の標準フローとして固定する（§5.3・§6）。
- Claude Agent Teams（Claude Code 内蔵・対話分業）と Claude Agent SDK（Python・無人常駐）の使い分けを、3チームそれぞれについて確定する（§5.4）。
- 既存 sns-ops-team との位置づけを確定する（§5.5）: **AGENT_TEAM.md が上位規約、本書 15 が運用実践編、sns-ops-team はチーム②の Doer 実装**、という3層関係。

### 2.2 やらないこと（明示的スコープ外）

- AGENT_TEAM.md 本体・02設計書・red-team.md の改訂（AGENT_TEAM.md は user 所有で承認必須。本書は「参照して運用する」層。改訂提案は §12 に隔離する）。
- sns-ops-team / lp-builder / skill-design-rigor / repo-skill-creator の SKILL.md 変更（各スキルの管轄。本書は Doer として参照するのみ）。
- Claude Agent SDK（Python）の実装・設計（別途 loop-engineering + 03-intel-hub.md の担当。本書は使い分け判定の確定まで）。
- Codex（OpenAI）のセットアップ手順・課金判断（外部ツール。役割スロットとして言及のみ）。
- frontend / デザイナー等の専用カスタムエージェント定義ファイルの新規作成（YAGNI。実在するカスタム定義は red-team のみ。デザイナー役は general-purpose + lp-builder で代替する。専用定義が要る構成が2件出たら再検討）。
- hooks・CI による規約違反の機械検出（YAGNI。AGENT_TEAM.md §8-1 と同方針。違反3回で再検討）。
- 本書内容の AGENT_TEAM.md 章7 への転記（user 所有ファイルへの書込。§12 でユーザー承認を得てから別タスクで行う）。

## 3. 完成条件（Definition of Done）

- [ ] `/home/user/claude-skills/docs/designs/15-agent-team-operations.md` が存在し、`grep -cE '^## [0-9]+\. ' docs/designs/15-agent-team-operations.md` が `13` を出力する（0〜12 の13セクション）。
- [ ] 禁止語検査（00設計書 自己反証3の3語）が 0 件（exit 1）である。検査コマンドは skill-design-rigor の禁止語リストを本ファイルに適用し、本行の説明文自体を除外して実行する。
- [ ] チーム構成の型が3種そろう: `grep -cE '^### 5\.[123] チーム' docs/designs/15-agent-team-operations.md` が `3` を出力する。
- [ ] 3チームそれぞれに「書込許可」列を持つ役割表がある（§5.1〜5.3 を目視で確認。各表に `書込許可` 見出しが含まれる: `grep -c '書込許可' docs/designs/15-agent-team-operations.md` ≥ 3）。
- [ ] AGENT_TEAM.md との整合: 本書のチーム①②の書込許可が AGENT_TEAM.md 所有権表（plugins/scripts/sns は implementer 割当制、docs/marketplace.json/ROADMAP.md は leader）と矛盾しないことを §5.6 の照合表で確認できる。
- [ ] 使い分け表（§5.4）に3チーム全て（①②③）の行があり、各行に「Agent Teams / SDK / ハイブリッド」のいずれかが確定値で入っている。
- [ ] ウォークスルー: §6 の起動手順に従い、チーム③（スキル量産）で「架空の新スキルを2本並列実装する」場合の割当プロンプト2通を書いたとき、両者の `書込許可:` に同一 plugins ディレクトリが含まれない（§5.3 の割当単位が plugins/<プラグイン名>/ であることで担保。§10 で確認）。
- [ ] 2026-07-06 の実例が具体コミットハッシュ付きで §5.3 に記載され、「並列設計→red-team→並列実装→統合」の4フェーズに対応づいている。

## 4. 成果物の構成（ファイルレイアウト）

```
docs/designs/15-agent-team-operations.md   # 本書（唯一の成果物）
```

本書以外のファイルは変更しない。AGENT_TEAM.md 章7 への型の転記、marketplace.json 追記は行わない（本成果物はプラグインでもドキュメント配布物でもなく、リーダーが参照する運用設計書）。転記の要否は §12 でユーザー確認。

## 5. データ構造

役割表のスキーマ（全チーム共通・4列固定）:

| 列名 | 値域 |
|---|---|
| 役割 | 自由記述（ディレクター / デザイナー / コーダー / リサーチャー / アナリスト / ライター / 設計 / 実装 / レビュー / 統合 のいずれか） |
| 主体 | `リーダー（メインセッション）` / `Agent（general-purpose, model: sonnet）` / `Agent（subagent_type: red-team）` / `hermes-relay 経由` / `Codex（外部・任意）` |
| 参照スキル | plugins 配下のスキル名、または `—` |
| 書込許可 | AGENT_TEAM.md 所有権表と整合する絶対パス／ディレクトリ、または `なし（読取専用）` |

### 5.1 チーム① 納品品質LP作成チーム（確定）

用途: LP制作の副業案件を、ヒアリング〜デザイン仕様〜実装〜納品前レビューまで1セッションで回す。

| 役割 | 主体 | 参照スキル | 書込許可 |
|---|---|---|---|
| ディレクター | リーダー（メインセッション） | lp-builder（ヒアリング・構成の型）、biz-ops-guard | docs/**、案件作業ディレクトリの統合（マージ先） |
| デザイナー | Agent（general-purpose, model: sonnet） | lp-builder のコピー/構成指針（Frontend Design スキルは未導入のため lp-builder で代替） | 案件作業ディレクトリ内の `design-spec.md` 1ファイルのみ |
| コーダー1 | Agent（general-purpose, model: sonnet） | lp-builder の実装手順 | 案件作業ディレクトリ内の `index.html` のみ |
| コーダー2 | Agent（general-purpose, model: sonnet）※任意で並列。Codex 併用可 | lp-builder の実装手順 | 案件作業ディレクトリ内の `assets/`（画像・CSS）のみ |
| レッドチーム | Agent（subagent_type: red-team） | — | なし（読取専用）。納品前に必須実行 |

起動順序: デザイナー（単独・先行）→ 完了後コーダー1・コーダー2を並列 → 統合（リーダー）→ red-team（納品前）→ リーダーが指摘採択/棄却 → 納品。
frontend 不在時の代替: デザイナー役は専用エージェント定義を作らず general-purpose に lp-builder のコピー/構成指針を参照させる（§11）。

### 5.2 チーム② SNS運用・資産化チーム（確定）

用途: SNSアカウント運用を企画〜リサーチ〜分析〜執筆〜レビュー〜キュー出力まで回し、資産（sns-strategy.md / post-queue.md）を蓄積する。sns-ops-team スキルの手順を Doer として使う。

| 役割 | 主体 | 参照スキル | 書込許可 |
|---|---|---|---|
| ディレクター | リーダー（メインセッション） | sns-ops-team（オーケストレーション手順） | `sns/<アカウント名>/sns-strategy.md` |
| リサーチャー | hermes-relay 経由（NotebookLM / Hermes x_search。CLAUDE.md の調査ルールどおり。Claude 自身の WebSearch は使わない） | hermes-x-search | `automation/queries/pending/`（hermes-relay ブランチ側） |
| アナリスト | Agent（general-purpose, model: sonnet） | twitter-intel（分析観点） | `sns/<アカウント名>/` 配下の分析メモ1ファイル |
| ライター | Agent（general-purpose, model: sonnet）※採用ネタごとに並列可 | sns-ops-team の執筆工程（voice-profile-extractor 未実装のため sns-strategy.md の文体欄で代替） | `sns/<アカウント名>/post-queue.md` |
| レッドチーム | Agent（subagent_type: red-team） | — | なし（読取専用）。炎上リスク観点は red-team のユーザー視点ペルソナで実施 |

起動順序: リサーチャー（hermes-relay へ投げて待機）と企画（ディレクター自身）を並行 → リサーチ結果統合 → ライター（採用ネタごとに並列）→ アナリスト or ディレクターがレビュー → red-team（炎上リスク）→ post-queue.md に draft 追記。承認（approved 化）は Ryo の手作業、投稿は sns-auto-posting（本チーム外）。
ライター並列時の競合回避: post-queue.md は単一ファイルのため、複数ライターに同時割当しない。ライターは本文テキストを最終報告で返し、post-queue.md への追記はディレクター1体が直列で行う（§5.3 手順3 の同一ファイル同時割当禁止に準拠）。

### 5.3 チーム③ スキル量産チーム（確定・今日の実例から抽出）

用途: 複数の新スキル／設計書を、設計（Opus）→ 批判（red-team）→ 実装（Sonnet 並列）→ 統合（リーダー）の4フェーズで量産する。

| 役割 | 主体 | 参照スキル | 書込許可 |
|---|---|---|---|
| 設計 | リーダー（メインセッション = Opus）。並列で複数設計をこなす場合は設計対象ごとに別セッション | skill-design-rigor（計画ゲート・自己反証）、TEMPLATE.md | `docs/designs/**` |
| 実装1..N | Agent（general-purpose, model: sonnet）×N 並列 | repo-skill-creator（スキル雛形・導入確認）、対象設計書 | `plugins/<プラグイン名>/`（1体1ディレクトリ。重複禁止）／必要なら `scripts/<ファイル>` |
| レビュー | Agent（subagent_type: red-team） | — | なし（読取専用）。設計書完成時と marketplace.json 追記前に必須 |
| 統合 | リーダー（メインセッション） | model-switcher | `marketplace.json`、`ROADMAP.md`、`docs/designs/**`（ステータス更新）、`MISTAKES.md` |

起動順序（4フェーズ固定）:
1. **並列設計** — リーダー（Opus）が設計対象ごとに TEMPLATE.md で設計書を書く。1設計 = 1ファイル `docs/designs/NN-*.md`。
2. **red-team** — 各設計書完成時に `subagent_type: red-team` を対象パスを渡して起動し、失敗シナリオ3件に採択/棄却を明記（AGENT_TEAM.md 章6）。
3. **並列実装** — 設計書ごとに Agent（model: sonnet）を割当。書込許可は `plugins/<各スキル名>/` に限定し、同一ディレクトリを2体に渡さない。実装セッションの開始プロンプトは 00設計書 §5.2 の定型文を使う。
4. **統合** — リーダーが `git status` を許可リスト和集合と照合（AGENT_TEAM.md 章4 手順5）→ `python scripts/validate_skills.py` 通過確認 → marketplace.json へ一括登録 → red-team（リリース前）→ コミット/push。

2026-07-06 の実例（この型の初回適用。コミットハッシュで対応づけ）:
- フェーズ1 並列設計: `4eb21ad`（F-3 マルチエージェント設計ドラフト）、`34ada02`（F-2）、`693afd4`（F-5/F-7）、`7ffc2fa`（F-4/F-6）。
- フェーズ2 red-team: ドラフト→実装への移行時に各設計書へ批判を通過（AGENT_TEAM.md 章6 の①タイミング）。
- フェーズ3 並列実装: `4e2f934`（F-1 skill-design-rigor）、`bb98f20`（F-2）、`17bd1a2`（F-3 AGENT_TEAM.md + red-team）、`9e1e7a7`（F-4 intel-hub）、`95a5949`（F-6 biz-analysis）、`6997677`（F-7 affiliate-monetization）。各実装は別 Agent / 別コミット単位。
- フェーズ4 統合: `976eeab`（marketplace.json に新規4スキルを一括登録）。

### 5.4 Agent Teams / Agent SDK 使い分け（3チーム確定）

AGENT_TEAM.md 章2 の2条件（①人間が同一セッションで承認・方向修正に参加 or 1セッション完結 → Agent Teams、②人間不在で時刻トリガー無人稼働 → Agent SDK）を各チームに適用した確定結果:

| チーム | 採用フレームワーク | 根拠 |
|---|---|---|
| ① LP作成 | Claude Agent Teams | 案件は納品前レビューに人間（Ryo/クライアント）の承認が入り、1案件1セッションで完結する。無人稼働の要素なし。 |
| ② SNS運用・資産化 | ハイブリッド（企画〜キュー出力は Agent Teams、日次無人収集は Agent SDK） | 企画・執筆・レビューは炎上リスク採択に人間が関与するため Teams。リサーチの定期無人収集（hermes-relay の日次実行）だけは SDK 側。AGENT_TEAM.md 章2「両該当」ルールを適用: まず Teams で運用を安定させ、loop-engineering でループ設計書（03-intel-hub.md 系）を書いてから SDK 化する。 |
| ③ スキル量産 | Claude Agent Teams | 設計判断と red-team 採択に人間が関与し、1リリース単位で完結する。無人で新スキルを量産する運用は取らない（品質ゲートが人間依存のため）。 |

確定: 現時点で SDK 常駐が必要なのはチーム②のリサーチ収集部分のみ。①③は完全に Agent Teams。SDK 実装は本書対象外（§2.2）。

### 5.5 sns-ops-team・AGENT_TEAM.md との3層関係（確定）

| 層 | 資産 | 責務 |
|---|---|---|
| 上位規約 | AGENT_TEAM.md（+ 元設計 02-agent-team.md） | 「誰がどのファイルに書けるか（所有権）」「誰が Agent を起動するか（権限）」「宣言プロトコル」「red-team 必須タイミング」を定める。矛盾時は最優先。 |
| 運用実践編 | **本書 15-agent-team-operations.md** | 規約を使った具体的チーム編成3種・起動順序・Teams/SDK 判定・実例の型を与える。規約を変更せず参照する。 |
| Doer 実装 | sns-ops-team（チーム②）、lp-builder（チーム①）、repo-skill-creator + skill-design-rigor（チーム③） | 各役割が実際に踏む工程・テンプレ・チェックリストを持つ。 |

sns-ops-team は置き換えない。同スキルの企画→リサーチ→執筆→レビュー→キュー出力の手順はチーム②の Doer としてそのまま使い、本書は「その5役割を誰（どの主体）が演じ、どのファイルに書けるか」を AGENT_TEAM.md に沿って割り当てるだけ。矛盾が生じたら AGENT_TEAM.md > 本書 > sns-ops-team の順で優先し、sns-ops-team 側の改修要否をユーザーに確認する。

### 5.6 書込許可と AGENT_TEAM.md 所有権表の照合（整合確認）

| 本書で割り当てた書込許可 | AGENT_TEAM.md 所有権表の該当行 | 整合 |
|---|---|---|
| デザイナー/コーダー: 案件作業ディレクトリ（LP成果物） | 未収載パス → leader 所有だが、案件成果物は plugins/scripts/sns 外の一時作業領域。実運用では案件ディレクトリを implementer 割当制として扱い、統合はリーダーが行う（§11 で確定） | 整合（§11 ルールで補う） |
| チーム②アナリスト/ライター: sns/<アカウント名>/ | sns/** = implementer（割当制・同時1エージェント） | 整合 |
| チーム②リサーチャー: automation/queries/pending/ | 未収載パス（hermes-relay ブランチ側）→ leader 所有扱いだが hermes-relay は別ブランチ運用。CLAUDE.md 調査ルールに従いリーダーが push | 整合（別ブランチのためリーダー経由） |
| チーム③実装: plugins/<プラグイン名>/、scripts/<ファイル> | plugins/** / scripts/** = implementer（割当制） | 整合 |
| チーム③統合: marketplace.json / ROADMAP.md / docs/** / MISTAKES.md | 全て leader 所有 | 整合（統合役=リーダー限定） |

## 6. 処理フロー（Agent ツール起動手順）

リーダー（メインセッション）が踏む手順。AGENT_TEAM.md 章4 宣言プロトコルを各起動に適用する。

**Step 1（判定）**: サブエージェントを使うタスクを受けたら §5.4 でチーム①②③のどれか、Teams/SDK どちらかを判定する。SDK 無人稼働なら本書対象外（03設計書へ）と報告して終了。

**Step 2（編成確定）**: §5.1〜5.3 の該当チーム表から役割・主体・書込許可を転記し、各 Agent の `書込許可:` リストを確定する。AGENT_TEAM.md 章3 所有権表と §5.6 で照合し、leader/user 所有パスを implementer に割り当てないことを確認する。

**Step 3（起動）**: 各実行 Agent を Agent ツールで起動する。割当プロンプトの先頭2行は AGENT_TEAM.md 章4 手順2 の定型:
```
書込許可: <絶対パスまたはディレクトリのリスト>
上記以外のファイルは変更禁止。変更が必要になったら変更せず最終報告で申告すること。
```
並列起動は独立作業のみ（同一ファイル/同一割当ディレクトリを2体に渡さない）。model は general-purpose に `model: sonnet`。実装セッションには 00設計書 §5.2 の定型プロンプトを続ける。

**Step 4（red-team）**: AGENT_TEAM.md 章6 の必須タイミング（設計書完成時 / marketplace.json 追記前 / ユーザー指示）に該当すれば `subagent_type: red-team` を対象ファイル絶対パス付きで起動し、失敗シナリオ3件それぞれに採択/棄却を1行明記する。

**Step 5（統合）**: 全 Agent 完了後、リーダーが `git status` を許可リスト和集合と照合（章4 手順5）→ 成果物の論理整合を全体QA → チーム③なら `python scripts/validate_skills.py` 通過確認 → コミット/push。許可リスト外変更があれば revert + MISTAKES.md 記録。

分岐: Agent の worktree 分離（`isolation: worktree`）を使う場合もマージはリーダーのみ。所有権表・許可リストは worktree 内でも同一に適用（AGENT_TEAM.md エッジケース表と同じ）。

## 7. エッジケース

| ケース | 期待挙動 |
|---|---|
| デザイナー役に frontend 専用エージェントを使いたい | 専用定義は作らない。general-purpose + lp-builder で代替（§11）。専用定義が要る構成が2件出たら §12 に追記してユーザー確認 |
| チーム②で複数ライターを並列にしたい | 本文生成は並列可。ただし post-queue.md 単一ファイルへの追記はディレクター1体が直列で行う（§5.2） |
| チーム③で2実装 Agent が同一 plugins ディレクトリを触る必要が出た | 同時割当せず直列実行にする（AGENT_TEAM.md 章4 手順3）。設計段階でディレクトリが分かれていない設計書は分割し直す |
| red-team が対象セッション作成直後で認識されない | `.claude/agents/*.md` はプロセス起動時に一度だけ読まれる（02設計書 §13）。新規セッションで再実行する |
| 案件作業ディレクトリの所有権が所有権表に無い | 未収載 → leader 所有だが、LP案件は implementer 割当制として扱い統合はリーダー（§5.6・§11）。恒常運用なら sns/** と同様の行追加を §12 でユーザー確認 |
| チーム②がハイブリッドで無人収集を先に作りたい | まず Agent Teams で企画〜キューを安定させてから SDK 化（§5.4・AGENT_TEAM.md 章2 両該当ルール）。順序を飛ばさない |
| ユーザーが本書と矛盾する編成を指示 | ユーザー指示が優先。恒常化しそうなら本書の改訂をユーザーに提案（AGENT_TEAM.md エッジケース表と同方針） |

## 8. 失敗シナリオとレッドチーム所見

| # | 失敗シナリオ | 早期警報サイン | 設計上の対策 |
|---|---|---|---|
| 1 | 二重管理: 本書とAGENT_TEAM.md章7に同じチーム構成表が並存し、片方だけ更新されて食い違う（経営視点=保守コスト） | チーム構成表が AGENT_TEAM.md と本書の両方に実体で存在し、内容が一致しない | 本書は AGENT_TEAM.md 章7 を実体重複させず「実践展開」と位置づけ、転記は §12 のユーザー承認後に一方向でのみ行う。矛盾時の優先順位を §5.5 で AGENT_TEAM.md > 本書と固定 |
| 2 | 実行不能な型: 実在しないエージェント（frontend 等）前提で手順を書き、起動時に `Agent type not found`（ユーザー視点=期待とのズレ） | 割当の主体列に red-team 以外のカスタム subagent_type が現れる。起動が type not found で失敗 | 全チームの主体列を「general-purpose + model: sonnet」か「subagent_type: red-team」に限定（§5.1〜5.3）。デザイナー役の代替を §11 で確定 |
| 3 | 統合フェーズの競合見逃し: 並列実装 Agent の成果物が別ファイルでも論理矛盾（例: 2スキルが同じ marketplace.json エントリ名を要求）し、統合時に片方が消える（攻撃者視点=権限逸脱に近い上書き） | `git status` に許可リスト和集合外のファイルが出る。または marketplace.json のエントリ重複 | Step 5 の照合を必須化。marketplace.json 追記はリーダー統合役のみ（§5.3）。競合は revert + MISTAKES.md 記録（AGENT_TEAM.md 章4 手順5） |

## 9. 実装手順（Sonnet 向けタスク分割）

本書の主成果は本ファイル自体（Opus 設計セッションで完成）。以下は本書を「運用資産として発効させる」ための最小タスク。全て人間承認ゲートつき。

1. **本ファイルの確定** — §5.1〜5.6 の確定値と §6 のフローを本ファイルに収録。完了条件: §3 の grep 群（セクション13・禁止語0・チーム型3・使い分け3行）が全て真。
2. **（承認後）AGENT_TEAM.md 章7 への型③転記** — ユーザーが §12 の Q1 を承認した場合のみ、AGENT_TEAM.md 章7 にチーム③（スキル量産）の表を追加する。AGENT_TEAM.md は user 所有のため、承認なしでは実行しない。完了条件: AGENT_TEAM.md 章7 にチーム③行が追加され、本書 §5.3 と一致。
3. **（承認後）本書ステータス更新** — 発効時に本書ステータスを「レビュー済み」に更新。完了条件: 表の1行目が更新済み。

順序依存: 1 は本設計セッションで完結。2・3 は §12 の承認が前提のため本設計では実行しない。marketplace.json / validate_skills.py は対象外（本成果物はプラグインではない）。

## 10. テスト計画

- 機械検証: §3 の grep 群を実行し exit code と出力を報告する（セクション数13・禁止語0件・`^### 5\.[123] チーム` が3・`書込許可` が3件以上・使い分け表に①②③）。
- ウォークスルー1（チーム③）: 架空の新スキル2本（`plugins/foo-skill/` と `plugins/bar-skill/`）を並列実装する割当プロンプト2通を §6 Step 3 の書式で作成し、両者の `書込許可:` の積集合が空（別 plugins ディレクトリ）であることを確認する。
- ウォークスルー2（チーム①）: 架空LP案件でデザイナー1・コーダー1・コーダー2の割当プロンプト3通を作成し、書込許可が `design-spec.md` / `index.html` / `assets/` に分離し重複しないことを確認する。
- 整合確認: §5.6 の照合表の各行が AGENT_TEAM.md 章3 所有権表の実際の行と矛盾しないことを、AGENT_TEAM.md を Read して突き合わせる。
- ネガティブ確認: 単独セッション（Agent 起動なし）のタスクでは本書の起動手順を要求しないことを、§6 Step 1 と AGENT_TEAM.md 章1 適用範囲で確認する。

## 11. 実装時判断ルール

- チーム構成表の値は §5.1〜5.3 の確定値を転記する。役割の増減・主体の変更はしない（減らす提案はユーザー確認）。
- デザイナー役に専用カスタムエージェント定義（frontend 等）を作らない。general-purpose に `model: sonnet` を指定し lp-builder のコピー/構成指針を参照させる。実在するカスタム定義は red-team のみ。
- LP案件の作業ディレクトリ（所有権表 未収載）は「implementer 割当制・同時1エージェント」として扱い、統合（マージ）はリーダーのみが行う。所有権表への恒常的な行追加は §12 でユーザー確認するまでしない。
- red-team の起動は必ず対象ファイルの絶対パスをプロンプトに含める。パスなしでは red-team が「対象パスがありません」を返す（red-team.md の入力契約）。
- チーム②のリサーチは hermes-relay 経由のみ。Claude 自身の WebSearch をユーザー調査に使わない（CLAUDE.md 調査ルール）。パイプラインのデバッグ等メタ用途のみ WebSearch 可。
- Codex を実装スロットに入れる具体コマンド・課金設定は書かない（§2.2）。役割表では「外部・任意」の言及に留める。
- 本書内容を AGENT_TEAM.md 章7 に転記したくなっても、ユーザー承認（§12 Q1）前は書かない。AGENT_TEAM.md は user 所有。

## 12. 未解決事項（ユーザー確認待ち）

- Q1: チーム③（スキル量産）の構成表を AGENT_TEAM.md 章7 に正式収録するか（現在 章7 は構成例2件のみ）。収録先が user 所有のため承認が要る。承認まで本書 §5.3 が唯一の定義。
- Q2: LP案件の作業ディレクトリを所有権表（AGENT_TEAM.md 章3）に恒常行として追加するか（例: `deliverables/**` を implementer 割当制）。現状は「未収載=leader 所有だが実運用で割当制扱い」という §11 ルールで暫定運用。
- Q3: チーム②のハイブリッド（無人収集を SDK 化）を実際に着手する時期。着手時は loop-engineering + 03-intel-hub.md を先に完成させる前提。
- Q4: Codex を実装スロットに実際に組み込む時期と課金判断（AGENT_TEAM.md の「任意」を実運用に昇格するか）。
</content>
</invoke>
