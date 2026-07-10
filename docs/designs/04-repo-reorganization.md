# レポジトリ整理（構造の再設計 + 整理逸脱チェック） 設計書

| 項目 | 値 |
|---|---|
| ステータス | 一部撤回（agent/削除はユーザー指示でrevert・保留。配置規約とCI検査は実装済み。MISTAKES M-002参照） |
| 種別 | ドキュメント + スクリプト改修 + スキル改修 |
| 優先度 | Tier F-5 |
| 実装モデル | Sonnet 5（推奨 effort: high） |
| 依存する設計書 | docs/designs/00-fable-sonnet-bridge.md（テンプレ・運用プロセス） |
| 依存する既存スキル | plugins/repo-skill-creator（配置レビュー観点を追記する対象） |
| 外部依存 | なし（ユーザー実機確認2件を §9 に含む） |

## 1. 目的・背景（Why）

このリポジトリには「Claude 全般の運用ルール（CLAUDE.md / MISTAKES.md / hooks）」
「自作スキル28個（plugins/）」「外部ベンダースキル70個×2重複（agent/ と .agents/、各13MB）」
「設計書・計画（docs/ / ROADMAP.md / LOOPS.md）」「自動化キュー（hermes-relay ブランチ）」が
混在しており、さらに今後「作りたいアプリ」（fable5-design-assets.md §4.2: コマtimes・
テニスアプリ・動画編集エージェント）の置き場が未定義。ユーザーはこれを整理したい。

現状調査（2026-07-06 実施）で確定した事実:

- `agent/skills/` と `.agents/skills/` は同じ70スキルの重複。差分は `.agents/` 側だけ
  frontmatter に `name:` が補完されている（= `.agents/` が修正済みの正）。台帳は
  `skills-lock.json`（70件、source: anthropics/skills, mattpocock/skills, obra/superpowers）。
- アプリは main ブランチにまだ1つも存在しない（移行コストゼロで置き場ルールを決められる）。
- 自動化ログは既に `hermes-relay` ブランチに隔離済み（main には存在しない）。

本設計の成果物は ①目標構造（分類軸 + 移行マップ）②Sonnet が実行できる移行手順
③整理逸脱チェック（CI + repo-skill-creator への観点追加）の3つ。

## 2. スコープ

### 2.1 やること

- 分類軸の確定と目標構造の定義（§5.1、README への明文化）
- 移行マップの確定（§5.2）と移行手順（§9）— 実体は「agent/ の重複削除」+「README 更新」のみ
- アプリ・実データの置き場ルールの確定（別リポジトリ、§5.1 分類E・F）
- `scripts/validate_skills.py` へのルート許可リスト検査の追加（整理逸脱の CI 検出）
- `plugins/repo-skill-creator` SKILL.md への「配置レビュー観点」節の追加 + version 更新
- 移行後の破壊確認（hermes-relay 疎通・/plugin update・.agents スキル認識）

### 2.2 やらないこと（明示的スコープ外）

- リポジトリ分割（skills/apps/private の3分割）— 不採用。理由は §5.3 のトレードオフ比較
- `plugins/` 配下のディレクトリ移動・改名 — marketplace.json の `./plugins/<name>`、
  session-start.sh の glob、インストール済み28スキルのパス依存を壊すだけでメリットなし
- `hermes-relay` ブランチ・`automation/` の変更 — ローカル watcher（タスクスケジューラ常駐、
  リポジトリ URL + ブランチ名固定で毎分ポーリング）を壊すリスクがあり、既に隔離済みで整理不要
- `docs/` 直下の旧形式設計書（hermes-web-engine-design.md, mistakes-db-design.md,
  skill-quality-loop.md, skill-requirements.md, global-rules.md, fable5-design-assets.md）の
  `docs/designs/` への移動・改名 — MISTAKES.md と README.md から相対パスで参照されており、
  移動はリンク切れリスクのみでメリットなし（凍結扱い。00 設計書 §7 の「実装済みは凍結」と同じ）
- 常駐の整理エージェント・定期レビュー Routine の新設 — YAGNI。CI 検査 +
  repo-skill-creator の観点で足りる。CI 検査が3ヶ月で3回以上逸脱を検出したら再検討
- アプリ用リポジトリの実際の作成 — 最初のアプリ実装時に行う（今作ると空リポジトリが腐る）
- CLAUDE.md への配置規約の追記 — README の1節 + CI 検査で足りる。CLAUDE.md は
  毎セッション注入されるため肥大化コストが高い
- 外部ベンダースキル70個の取捨選択（不要スキルの削除）— ユーザー判断待ち（§12）

## 3. 完成条件（Definition of Done）

- [ ] `git ls-tree HEAD --name-only` の出力に `agent` が含まれず、`.agents` は含まれる
- [ ] `python3 scripts/validate_skills.py` が exit 0 で終わり、標準出力に `root layout OK` を含む
- [ ] `touch /tmp/x && cp /tmp/x stray-test.txt && git add stray-test.txt && python3 scripts/validate_skills.py`
      が exit 1 で終わり、標準出力または標準エラーに `stray-test.txt` を含む
      （確認後 `git rm --cached stray-test.txt && rm stray-test.txt` で片付ける）
- [ ] README.md に「## リポジトリ構造と配置規約」節があり、§5.1 の6分類の表と
      「アプリは別リポジトリ」「実データはコミット禁止」の2ルールを含む
- [ ] `plugins/repo-skill-creator/skills/repo-skill-creator/SKILL.md` に「配置レビュー観点」
      節（§5.4 の5項目）があり、plugin.json の version が上がっている
- [ ] `.github/workflows/validate-skills.yml` が push 時に改修後の validate_skills.py を
      実行している（ワークフローの実行ログでルート検査行が確認できる）
- [ ] 【ユーザー実機・agent/ 削除前】ローカル Claude Code で `.agents/skills/` の
      スキル（例: brainstorming）が認識されている（§9 タスク1 の確認手順）
- [ ] 【ユーザー実機・移行後】`/plugin marketplace update claude-skills` が成功し、
      `/plugin list` で28スキルが enabled のまま
- [ ] 【移行後】hermes-relay 疎通: `automation/queries/pending/` にテストクエリを push し、
      4分以内に `automation/results/` に同名ファイルが返る

## 4. 成果物の構成（ファイルレイアウト）

変更・削除するファイル（main ブランチ）:

```
claude-skills/
├── agent/                      # 【削除】.agents/ と重複（劣後コピー）
├── README.md                   # 【変更】構造ツリー修正 + 配置規約節を追加
├── scripts/validate_skills.py  # 【変更】ルート許可リスト検査を追加
└── plugins/repo-skill-creator/
    ├── .claude-plugin/plugin.json                    # 【変更】version bump
    └── skills/repo-skill-creator/SKILL.md            # 【変更】配置レビュー観点を追加
docs/designs/04-repo-reorganization.md                # 本書（ステータス更新のみ）
```

上記5点以外のファイルは変更しない。

## 5. データ構造

### 5.1 分類軸（確定・6分類）

課題提示の5分類（運用ルール/スキル/アプリ/設計書/自動化ログ）では、第三者製で
ライセンス・出典・更新経路が異なる外部ベンダースキル（13MB、リポジトリ容量の9割）を
自作スキルと区別できない。よって6分類とする。

| # | 分類 | 置き場（確定） | 現在の該当物 |
|---|---|---|---|
| A | 運用ルール | main の `CLAUDE.md` `MISTAKES.md` `.claude/`（hooks, settings） | 左記 + docs/global-rules.md（移植キット、docs のまま凍結） |
| B | 自作スキル | main の `plugins/` `.claude-plugin/marketplace.json` `scripts/` `.github/` | 28プラグイン + 検証/配布スクリプト + CI |
| C | 外部ベンダースキル | main の `.agents/skills/` + 台帳 `skills-lock.json` | 70スキル（agent/ の重複は削除） |
| D | 設計書・計画 | main の `docs/designs/`（新規は NN-slug 形式のみ）`ROADMAP.md` `LOOPS.md`。docs/ 直下の既存6ファイルは凍結 | 左記 |
| E | アプリ | **別リポジトリ**。`ryotaroh180105/<app-name>` を1アプリ1リポジトリで作成。公開判断はアプリごと | 該当物なし（未着手）。このリポジトリには置かない |
| F | 実データ・自動化ログ | 実データ（音声・投稿キュー実運用分・学習ログ・TODO.md）は**このリポジトリにコミット禁止**（ユーザーローカルまたはアプリ側 private リポジトリ）。自動化キューは `hermes-relay` ブランチ（現状維持） | hermes-relay/automation/ |

### 5.2 移行マップ（確定）

| 現在 | 移行先 | 操作 |
|---|---|---|
| `agent/`（70スキル重複） | 削除 | `git rm -r agent/`（§9 タスク1の実機確認後） |
| `.agents/skills/` | 現状維持（分類Cの正） | なし |
| `plugins/` 全28 + marketplace.json | 現状維持 | なし |
| `docs/` 直下の6ファイル | 現状維持（凍結） | なし |
| `hermes-relay` ブランチ | 現状維持 | なし |
| アプリ（未存在） | 新規は別リポジトリ | README に規約明文化のみ |
| 実データ（未コミット） | コミット禁止を規約化 | README に規約明文化のみ |

移動が1件（削除）しかないのは意図的。混在の実害は「重複13MB」と「置き場ルールの不在」
であり、後者はルール明文化 + CI 検査で解消できる。既存パスを動かす整理は
インストール済みスキル・watcher・外部参照を壊すコストが利得を上回る（§5.3）。

### 5.3 リポジトリ分割 vs モノレポ（トレードオフ比較と推奨）

| 観点 | 案1: 3分割（skills / apps / private-data） | 案2: モノレポ維持 + ディレクトリ規約 + アプリのみ別リポ【推奨】 |
|---|---|---|
| marketplace / インストール済みスキル | リポジトリ名変更なら `/plugin marketplace add` からやり直し。28スキル×全端末で再インストール | 影響なし（plugins/ 不動） |
| ローカル watcher（hermes-relay） | クローン URL・ブランチ参照が変わり、タスクスケジューラ常駐の再セットアップが必要。失敗すると調査パイプラインが無言で止まる | 影響なし |
| MISTAKES.md 原本参照 | docs/global-rules.md で他環境（claude.ai・他リポジトリ）に配布済みの原本 URL が変わる | 影響なし |
| git 履歴 | filter-repo で分割すれば保持できるが、既存ブランチ10本・PR 参照が切れる | 完全保持 |
| 混在解消の効果 | 高い（物理分離） | 中（規約 + CI 検査で担保） |
| 実データの隔離 | private リポジトリで確実 | コミット禁止規約 + ルート許可リスト検査で担保。アプリ実データはアプリ側リポジトリ（private 可）に置けるため実質同等 |

**推奨: 案2**。分割の利得（物理分離）は規約 + CI で代替でき、分割のコスト（3系統の
パス依存の破壊・再セットアップ）は回復に実機作業を要し過小評価できない。ただし
アプリ（分類E）は未着手で移行コストゼロのため、最初から別リポジトリとする —
これが分割の利得の大半（サイズ肥大防止・private 化・デプロイ独立）を無コストで得る。

### 5.4 repo-skill-creator に追記する「配置レビュー観点」（確定・5項目）

```markdown
## 配置レビュー観点（新規ファイル・ディレクトリを追加する前に確認）

1. 追加先は README「リポジトリ構造と配置規約」の6分類のどれか。どれでもなければ追加しない（ユーザーに確認）。
2. アプリのコード・アセットではないか。アプリは ryotaroh180105/<app-name> の別リポジトリに作る。
3. 実データ（音声ファイル・投稿キューの実運用データ・学習ログ・TODO.md）ではないか。このリポジトリにはコミットしない。
4. リポジトリ直下に新しいファイル・ディレクトリを増やしていないか。増やす場合は scripts/validate_skills.py の ROOT_ALLOWLIST と README のツリーを同一コミットで更新する。
5. 設計書は docs/designs/NN-<slug>.md 形式か。docs/ 直下への新規追加はしない（既存6ファイルは凍結）。
```

### 5.5 validate_skills.py のルート許可リスト（確定）

```python
ROOT_ALLOWLIST = {
    ".agents", ".claude", ".claude-plugin", ".github", ".gitignore",
    "CLAUDE.md", "LOOPS.md", "MISTAKES.md", "README.md", "ROADMAP.md",
    "docs", "plugins", "scripts", "skills-lock.json",
}
```

検査対象は `git ls-files` の第1パスセグメント集合（作業ツリーの未追跡ファイルは対象外。
CI はコミット済みツリーを検査するため）。集合が ROOT_ALLOWLIST の部分集合でなければ
違反パスを列挙して exit 1。合格時は `root layout OK` を出力する。

### 5.6 README に追加する節の骨子（確定）

節名 `## リポジトリ構造と配置規約`。内容: §5.1 の6分類表（そのまま転記）+ 次の2行:

```markdown
- アプリは別リポジトリ（`ryotaroh180105/<app-name>`、1アプリ1リポジトリ）に作る。本リポジトリには置かない。
- 実データ（音声・投稿キュー実運用分・学習ログ・TODO.md）は本リポジトリにコミットしない。
```

あわせて README 冒頭の構造ツリー（現在 plugins/scripts/.claude-plugin/.github のみ記載）に
`.agents/` `.claude/` `docs/designs/` を追記し、実態と一致させる。

## 6. 処理フロー

本設計は常駐処理を持たない。フローは2つ。

**移行フロー（1回きり）**: §9 のタスク1〜6 を順に実行。
入力 = 現在の main ブランチ、出力 = §4 の5ファイル変更が反映された main ブランチ +
§3 の実機確認3件の完了。

**逸脱チェックフロー（継続・自動）**:
入力 = push / PR → 処理 = GitHub Actions が validate_skills.py を実行（既存の
スキル検査 + 新設のルート許可リスト検査）→ 出力 = 違反があれば CI fail と違反パス一覧。
人手側は repo-skill-creator の配置レビュー観点（§5.4）がスキル作成時に先回りで効く。

## 7. エッジケース

| ケース | 期待挙動 |
|---|---|
| `.agents/skills/` のスキルが実機で認識されない（§9 タスク1 の確認で発覚） | agent/ を削除せず中断。どちらが読まれているかをユーザーと確認し、読まれている側を残して本設計書 §12 に追記 |
| agent/ 削除後に外部スキルの旧コピーが必要になった | `git revert` で復元可能（履歴保持のため filter 系は使わない）。skills-lock.json は削除しない（再取得の台帳） |
| ルート検査導入後、正当な理由で直下にファイルを増やしたい | ROOT_ALLOWLIST・README ツリー・当該ファイルを同一コミットで更新（§5.4 観点4） |
| hermes-relay ブランチに main の変更が波及する懸念 | 波及しない（別ブランチ・共有ファイルなし）。§3 の疎通確認で観察検証する |
| 過去の設計書・README が `agent/skills` を参照していた | 調査済み: *.md / *.json / *.sh に参照なし（skills-lock.json の skillPath は取得元リポジトリ内パスであり無関係）。追加対応不要 |
| validate_skills.py が git のない環境で実行された | `git ls-files` 失敗時はルート検査をスキップし警告を出して既存検査のみ実行（exit code は既存検査結果に従う） |

## 8. 失敗シナリオとレッドチーム所見

計画ゲート回答: (1) 失敗パターンは下表3件。(2) やらない境界は §2.2 に列挙
（特に plugins/ 移動・リポジトリ分割・docs 改名を「ついでにやりそう」として明示禁止）。
(3) 完成条件は全て実行観察形式（§3）。(4) 実装者が最初に詰まるのは「agent/ と .agents/ の
どちらを消すか」— §5.2 で確定済み + タスク1 に実機確認ゲートを置いた。(5) 必要性:
既存スキル・設計書に代替なし（repo-skill-creator はスキル作成規約のみで配置規約を持たない）。

| # | 失敗シナリオ | 早期警報サイン | 設計上の対策 |
|---|---|---|---|
| 1 | ディレクトリ移動でインストール済みスキル・hooks が壊れる（最頻・最重）— 実装者が「整理」の名目で plugins/ や docs/ を移動する | 移行 PR の diff に plugins/ 配下・marketplace.json のパス変更が含まれる | 移動を agent/ 削除の1件に限定（§5.2）。§2.2 で plugins/ 移動・docs 改名を明示禁止。§3 に /plugin update と28スキル enabled の実機確認を完成条件化 |
| 2 | agent/ と .agents/ の削除対象を取り違え、外部スキル70個が読み込み不能になる | 削除コミット後、実機のスキル一覧から brainstorming が消える | 差分調査で `.agents/` が正（name: 補完済み）と確定済み。さらにタスク1 で削除前にユーザー実機確認、失敗時は §7 の中断ルール。復元は git revert 1発 |
| 3 | 規約が読まれず混在が再発する（アプリを plugins/ に作る、実データをコミットする） | ルート直下に許可リスト外のエントリが現れる / CI が fail する | validate_skills.py のルート検査で機械検出 + repo-skill-creator の配置レビュー観点で作成時に先回り。CLAUDE.md 非依存（肥大回避）で CI に寄せる |

watcher 破壊は「hermes-relay に触らない」（§2.2）ため発生経路がないが、
念のため §3 で疎通を観察確認する。

## 9. 実装手順（Sonnet 向けタスク分割）

順序依存: 1 → 2 は必須（実機確認前に削除しない）。3〜5 は相互独立。6 は最後。

1. **【ユーザー実機確認・agent/ 削除ゲート】** — ユーザーに依頼する（CLAUDE.md の説明義務に従い、
   意図: 削除対象の取り違え防止 / 内容: ローカル Claude Code のこのリポジトリで
   「brainstorming スキルを使って」と入力し発動するか、または利用可能スキル一覧に
   brainstorming が出るか確認 / 確認方法: 発動または一覧表示があれば OK と返信）。
   完了条件: ユーザーから OK の返信。NG なら §7 の中断ルールへ。
2. **agent/ 削除** — `git rm -r agent/` して1コミット（他の変更を混ぜない。revert 可能性のため）。
   完了条件: `git ls-tree HEAD --name-only` に `agent` が含まれない。
3. **validate_skills.py 改修** — §5.5 の ROOT_ALLOWLIST 検査を追加。
   完了条件: §3 の exit 0 / stray-test.txt で exit 1 の両テストが通る。
4. **README 更新** — §5.6 のとおり構造ツリー修正 + 配置規約節を追加。
   完了条件: §3 の README 項目を満たす。
5. **repo-skill-creator 改修** — SKILL.md に §5.4 の節を追加、plugin.json の version を
   1段上げる。完了条件: validate_skills.py exit 0 + §3 の該当項目。
6. **push + 実機確認 + ステータス更新** — push 後、§3 の実機確認3件
   （/plugin update・.agents 認識は完了済み・hermes-relay 疎通）を実施し、本設計書の
   ステータスを「実装完了」に更新してコミット。完了条件: §3 全項目にチェックが入る。

## 10. テスト計画

- ルート検査の正常系: クリーンな HEAD で `python3 scripts/validate_skills.py` → exit 0、
  出力に `root layout OK`。
- ルート検査の異常系: `stray-test.txt` を `git add` した状態で実行 → exit 1、違反パス表示
  （§3 の手順どおり。テスト後に取り消す）。
- 既存検査の非退行: 改修後も28プラグインの SKILL.md 検査結果が改修前と同一
  （改修前後で実行し出力を diff）。
- CI: push 後の GitHub Actions 実行ログでルート検査行を確認。
- 実機3件: §3 の【ユーザー実機】【移行後】項目（スキル認識・/plugin update・hermes-relay 疎通）。
  いずれも実行結果の観察であり、コードを読んでの確認は不可。

## 11. 実装時判断ルール

- agent/ 削除は git rm のみ。git filter-repo・history rewrite は使わない（履歴保持と
  revert 可能性を優先。13MB の履歴肥大は許容する）。
- ROOT_ALLOWLIST の検査は「ディレクトリ丸ごと許可」。docs/ や plugins/ の配下構造までは
  検査しない（配下の逸脱は repo-skill-creator の観点4・5 で人手カバー。機械検査の深掘りは
  逸脱が実際に3回起きたら再検討）。
- validate_skills.py への追加は関数1つ（`validate_root_layout(errors)`）に収める。
  設定ファイル化・CLI オプション化はしない。
- README の6分類表は §5.1 をそのまま転記する（要約・改変しない）。
- タスク1 でユーザーが「一覧の見方が分からない」場合: `ls ~/.claude/` と
  リポジトリ直下での `claude` 起動時のスキル候補表示を案内する。それでも判定不能なら
  削除を保留し §12 に追記してユーザー判断を仰ぐ。
- 外部ベンダースキルの個別削除を頼まれても本移行コミットには混ぜない（別タスク化）。

## 12. 未解決事項（ユーザー確認待ち）

- 外部ベンダースキル70個の取捨選択（全部残すか、使うものだけに絞るか）。絞る場合は
  skills-lock.json との整合更新が必要 — 別タスクとして ROADMAP 候補に積む。
- 最初のアプリ用リポジトリの命名と public/private（アプリ着手時に決定）。
- `.agents/skills/` がローカル実機で実際に読み込まれているかは実機確認（タスク1）の
  結果待ち。読み込まれていない場合「外部スキルをどこに置けば使えるか」自体を
  再設計する（本書の分類Cの置き場が変わる可能性）。
