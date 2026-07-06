# intel-hub（情報集約・リサーチエージェント / システムR・G統合）設計書

| 項目 | 値 |
|---|---|
| ステータス | 実装完了（Phase 1）。Phase 2（週次分析・矛盾検出）/ Phase 3（ブックマーク・Kindle）は本書の計画のみで未実装 |
| 種別 | スキル + データベース（Markdown） + パイプライン |
| 優先度 | Tier F-4 |
| 実装モデル | Sonnet 5（推奨 effort: high） |
| 依存する設計書 | docs/designs/00-fable-sonnet-bridge.md（実装プロセス）、docs/hermes-web-engine-design.md（hermes-web エンジン。未完了でも本書 Phase 1 は着手可 — §11 判断ルール参照） |
| 依存する既存スキル | plugins/hermes-x-search（リレー手順の正）、plugins/twitter-intel（X収集経路）、plugins/sns-ops-team（週次提案の受け手）、plugins/loop-engineering（定期実行の設計） |
| 外部依存 | hermes-relay ブランチ + ローカル watcher（稼働中）。X_BEARER_TOKEN（Phase 2 の自アカウント metrics 取得、任意） |

## 1. 目的・背景（Why）

調査結果が今はチャットログ・ROADMAP 候補表・hermes-relay の results/ に散在し、
「前に調べたはず」を再検索できない。本資産は2系統の蓄積DBを1つの基盤に統合する:

- **システムR（資料作成リサーチDB）**: Web/note/X/書籍から抽出した「原則」（資料作成・
  文章術・SEO・技術・法務IR の実践知）を1原則=1レコードで正規化し、矛盾検出と再検索を可能にする。
- **システムG（SNS伸びるアカウント分析DB）**: X/note/Instagram の投稿を型分類・メトリクス付きで
  蓄積し、型×エンゲージメントの相関から「次週の具体提案」を出す。

収集の実行体は既存の hermes-relay パイプライン（X=hermes、Web=hermes-web/notebooklm）。
**Claude の役割はクエリ整形と結果整形（＝レコード正規化）のみ**で、CLAUDE.md の運用原則をそのまま踏襲する。
使う人は Ryo 本人のみ（biz-ops-guard 対象外）。

## 2. スコープ

### 2.1 やること

- Phase 1（最小: 収集→保存→検索）
  - `intel/` データディレクトリと正規化スキーマ（§5）の確定・作成
  - `plugins/intel-hub/` スキル: ①リレー経由の調査→レコード化（ingest） ②Grep ベース検索インターフェース
  - `scripts/validate_intel.py`: レコードの frontmatter 機械検証
- Phase 2（分析・相関）
  - システムG: 投稿レコードの型分類・週次分析レポート（型別成績 + 相関所見 + 次週提案3件）
  - システムR: 取り込み時の矛盾検出（同 domain 内の claim 突合）と `intel/contradictions.md` 運用
- Phase 3（コネクタ）
  - ブックマーク取り込み: `intel/inbox/` へのURLリスト投入 → リレー経由で本文取得 → レコード化
  - Kindle リサーチ・要約: ①読書中の疑問を即調査して book-note 化 ②Kindle ハイライトエクスポートの一括取り込み

### 2.2 やらないこと（明示的スコープ外）

- SQLite / DuckDB 等のバイナリDB導入（理由: §5 冒頭の選定理由参照。Grep で足りる規模）
- ChatGPT をリレーの新エンジンとして追加すること（YAGNI。トレンド調査は hermes/hermes-web で賄い、ChatGPT Deep Research の結果は手動貼り付け＝`source_engine: manual` で受ける）
- X ブックマーク API（OAuth 2.0 user context）への直接接続（実装・認可コストが高く、エクスポート投入で足りる。3回/週以上手動投入が発生したら再検討）
- Kindle 画面の自動読取・常駐 OCR・「Kindle VPN」（実現不能に近い — §8 失敗シナリオ4。代替が正式案）
- 投稿文ドラフトの自動生成（sns-ops-team の執筆工程の担当。本スキルは提案=型+テーマ+根拠までを渡す）
- Instagram メトリクスの自動取得（公式APIはビジネスアカウント+審査が必要。手動入力で受ける）
- hermes-relay watcher 本体（`automation/*.ps1`）の改修（docs/hermes-web-engine-design.md の担当）
- 既存 results/（hermes-relay ブランチ）の過去分一括レコード化（ユーザー判断待ち。§12）

## 3. 完成条件（Definition of Done）

Phase 1:

- [ ] `intel/README.md`・`intel/principles/.gitkeep`・`intel/sns/.gitkeep`・`intel/sns/reports/.gitkeep`・`intel/books/.gitkeep`・`intel/inbox/.gitkeep`・`intel/contradictions.md` が存在する
- [ ] `plugins/intel-hub/skills/intel-hub/SKILL.md` と `plugins/intel-hub/.claude-plugin/plugin.json` が存在し、`python scripts/validate_skills.py` が exit 0
- [ ] `marketplace.json` に intel-hub のエントリがある
- [ ] `python scripts/validate_intel.py` が exit 0 で終わり、標準出力に `OK <レコード数> records` を出す（レコード0件でも `OK 0 records`）
- [ ] ウォークスルーA（ingest）: hermes-relay ブランチの実在結果ファイル `automation/results/20260705T164640Z-x-viral-post-analysis.md` を入力に、SKILL.md の手順だけで principle レコードが `intel/principles/2026-07/` に作られ、validate_intel.py が exit 0
- [ ] ウォークスルーB（検索）: レコード3件（principle 2件 + sns-post 1件、テスト用に手作成可）を置いた状態で「intel で note の文章術を検索して」と依頼すると、該当レコードの id・claim・source_urls を含む表が返る
- [ ] `/plugin install` → `/plugin list` で intel-hub の導入確認済み（README の完了定義）

Phase 2:

- [ ] ウォークスルーC（週次分析）: sns-post レコード12件（1アカウント・2型以上・metrics 入り。テスト用手作成可）を置いて「今週のSNS分析レポートを出して」と依頼すると、`intel/sns/reports/<account>-<YYYY-Www>.md` が §5.6 の3セクション構成で作られる
- [ ] ウォークスルーD（データ不足）: sns-post レコード5件のみの状態で同依頼をすると、レポートの相関所見セクションに「データ不足（10件未満）」と明記され、断定的な相関主張を含まない
- [ ] ウォークスルーE（矛盾検出）: claim が対立する principle 2件目を ingest すると、両レコードの `contradicts` に相互の id が入り、`intel/contradictions.md` に1行追記される

Phase 3:

- [ ] ウォークスルーF（ブックマーク）: `intel/inbox/2026-07-15-test.md` にURL2行（X 1件 + Web 1件）を置いて「inbox を取り込んで」と依頼すると、リレークエリ2本が enqueue され、結果到着後に bookmark レコード2件が作られ、inbox ファイルが `intel/inbox/done/` へ移動される
- [ ] ウォークスルーG（Kindle質問）: 「Kindle: <書名> <疑問文>」形式の依頼で notebooklm エンジンのクエリが enqueue され、結果から book-note レコード（question フィールド入り）が1件作られる

## 4. 成果物の構成（ファイルレイアウト）

```
plugins/intel-hub/
├── .claude-plugin/plugin.json
└── skills/intel-hub/SKILL.md
scripts/validate_intel.py
intel/
├── README.md                       # スキーマ定義の写し（§5）+ 運用ルール
├── contradictions.md               # 矛盾台帳（Phase 2）
├── inbox/                          # コネクタ投入口（Phase 3）
│   └── done/                       # 取り込み済み inbox ファイルの移動先
├── principles/<YYYY-MM>/<id>.md    # システムR レコード
├── sns/<YYYY-MM>/<id>.md           # システムG 投稿レコード
├── sns/reports/<account>-<YYYY-Www>.md  # 週次分析レポート
└── books/<YYYY-MM>/<id>.md         # Kindle/書籍レコード
marketplace.json                    # エントリ追記
docs/designs/03-intel-hub.md        # 本書
```

DB の実体は **このリポジトリ main ブランチの `intel/` 配下の Markdown + YAML frontmatter**。

選定理由（SQLite を選ばない理由を含む）:
1. Claude は Markdown を Read/Grep でネイティブに扱える。SQLite はクエリ用ツール実装・
   スキーママイグレーション・バイナリ diff 不能という保守コストが増えるだけで、
   数千レコード規模の全文 Grep に性能問題はない。
2. git がそのまま履歴・同期・複数セッション共有になる。
3. 生の調査結果（長文）は hermes-relay ブランチの `automation/results/` に既に永続化されて
   おり、main 側レコードは軽量な正規化層に徹する（二重保存しない）。

別リポジトリにしない理由: 通常セッションで clone なしに Grep 検索できることを優先。
移行トリガーを §11 に定義（`find intel -name '*.md' | wc -l` が 2000 超、またはリポジトリを
public にする決定をした時点で、専用 private リポジトリ `intel-db` へ `intel/` を丸ごと移す）。

## 5. データ構造

### 5.1 共通 frontmatter（全レコード必須フィールド）

```yaml
---
id: 20260706T090000Z-note-hook-writing   # UTC時刻+slug。ファイル名（拡張子除く）と完全一致
type: principle | sns-post | book-note | bookmark
collected_at: 2026-07-06                  # 取り込み日（UTC、YYYY-MM-DD）
source_engine: hermes | hermes-web | notebooklm | manual | inbox
relay_result_id: 20260705T164640Z-x-viral-post-analysis  # リレー結果ファイル名。リレー経由でなければ null
source_urls:
  - https://x.com/...                     # 1件以上必須（source_engine: manual のみ空リスト可）
tags: [note, 文章術]                       # 自由語彙、小文字、1〜5個
confidence: confirmed | unconfirmed | superseded
related: []                               # 関連レコード id のリスト
contradicts: []                           # 矛盾レコード id のリスト（Phase 2 で運用開始）
---
```

- slug 規則: 小文字 ASCII とハイフンのみ、40文字以内。
- `superseded` は矛盾解決でユーザーが「負け」と判定したレコードに付ける（削除しない）。

### 5.2 type: principle（システムR）追加フィールド

```yaml
domain: 資料作成 | 文章術 | SEO | SNS運用 | 技術 | 法務IR | 書籍知見   # enum 固定
claim: 結論を最初の3行に置くと読了率が上がる                            # 原則1行。矛盾検出の突合対象
```

本文セクション（この順・全部必須。空なら「該当なし」と書く）:

```markdown
## 根拠（逐語引用）
> 「…」 — https://...（出典URL、引用ごとに1つ）
## 適用条件・例外
## 未確認・断定できない点
```

### 5.3 type: sns-post（システムG）追加フィールド

```yaml
platform: x | note | instagram            # enum 固定
account: "@handle または note ユーザー名"
post_url: https://x.com/.../status/...
posted_at: 2026-07-05T21:00:00+09:00      # 不明なら null
post_type: 体験談 | ノウハウ | 意見主張 | 実績報告 | 質問投げかけ | まとめリスト | 引用コメント | 告知   # enum 固定・8種
own_account: true | false                  # 自アカウントの投稿か
metrics:
  impressions: 12400                       # 取得不能なら null
  likes: 230
  reposts: 41
  replies: 12
  bookmarks: 88
metrics_as_of: 2026-07-06                  # metrics 取得日。全 null なら null
```

本文セクション: `## 投稿本文（逐語）` `## 伸びた/伸びない要因の仮説` `## 未確認・断定できない点`。

### 5.4 type: book-note 追加フィールド

```yaml
book_title: "…"
book_author: "…"                           # 不明なら null
kindle_location: "位置No.1234" | null
question: "読書中に出た疑問の原文" | null   # 疑問起点でない（ハイライト取込）なら null
```

本文セクション: `## 回答/要約` `## 引用（逐語）` `## 未確認・断定できない点`。

### 5.5 type: bookmark 追加フィールド

```yaml
bookmarked_at: 2026-07-14                  # 不明なら collected_at と同値
original_platform: x | web                 # enum 固定
```

本文セクション: `## 要点` `## 引用（逐語）` `## 未確認・断定できない点`。

### 5.6 週次分析レポート（`intel/sns/reports/<account>-<YYYY-Www>.md`）

frontmatter: `account` / `week`（ISO週 `2026-W28`）/ `generated_at` / `records_used`（使った sns-post id のリスト）。
本文は次の3セクション固定:

```markdown
## 1. 型別成績表
| post_type | 件数 | 平均likes | 平均reposts | 平均eng率(likes+reposts)/impressions |
（impressions が null の行は eng率を「—」とする）
## 2. 相関所見
（対象4週間・10件以上ある場合のみ傾向を記述。10件未満なら「データ不足（10件未満）」とだけ書く）
## 3. 来週の投稿提案（3件固定）
- 提案1: 型=<post_type> / テーマ=<1行> / 根拠=<レコードid 1つ以上>
（投稿文は書かない。sns-ops-team に渡す）
```

### 5.7 矛盾台帳（`intel/contradictions.md`）

```markdown
| 検出日 | domain | レコードA | レコードB | 状態 |
|---|---|---|---|---|
| 2026-07-20 | 文章術 | 20260706T...-a | 20260720T...-b | 判定待ち / 解決済み(A採用) / 両立(条件差) |
```

### 5.8 inbox ファイル（`intel/inbox/<YYYY-MM-DD>-<slug>.md`）

URL 1行1件（最大10件/ファイル）。URL 行の直後に `> メモ` 行を置いてよい（レコードの tags・要点のヒントとして使う）。

## 6. 処理フロー

### 6.1 収集（ingest）— Phase 1

1. **入力**: ユーザーの調査依頼（「◯◯の原則を調べて intel に入れて」）、
   または既存のリレー結果ファイルの指定。
2. **エンジン選択**（確定ルーティング。Claude はクエリ整形のみ）:

   | 調査種別 | engine ヘッダ | 実行体 |
   |---|---|---|
   | 事実（法律・IR・公式ドキュメントの確認） | `engine: notebooklm` + `topic:` | NotebookLM Deep Research |
   | トレンド・実践知（Web記事・比較） | `engine: hermes-web` | Hermes web_search/web_extract（Grok） |
   | X の投稿・反応・アカウント分析 | ヘッダなし | Hermes x_search（Grok） |

3. **クエリ整形**: hermes-x-search SKILL.md のチェックリスト（日本語指定・出力セクション指定・
   根拠URL必須・逐語引用・ASCII ダブルクォート禁止）に従い、
   `automation/queries/pending/<UTC時刻>-<slug>.md` に置いて hermes-relay ブランチへ push。
4. **結果待ち**: バックグラウンド Bash で 30 秒間隔ポーリング、15分でタイムアウト
   （hermes-x-search SKILL.md のコマンドをそのまま使う）。
5. **正規化**: 結果本文から原則を抽出し、1原則 = 1 principle レコードを作成
   （1結果あたり最大10件。根拠URLの無い主張はレコード化しないか `confidence: unconfirmed` にする）。
   sns-post / book-note / bookmark も同じ手順で該当 type に正規化する。
6. **重複チェック**: レコード作成前に `source_urls` の各URLを `intel/` 全体に Grep。
   ヒットしたら新規作成せず既存 id を報告（例外は §11）。
7. **検証・保存**: `python scripts/validate_intel.py` を実行し exit 0 を確認してからコミット。
   push はユーザー指示時のみ（既存運用どおり）。

### 6.2 検索 — Phase 1

1. **入力**: 「intel で◯◯を検索」。
2. **処理**: Grep を2段で実行 — ①frontmatter（`claim:` `tags:` `domain:` `book_title:`）
   ②本文全文。`path: intel/` 固定。
3. **出力**: 表 `| id | type | claim/要点1行 | confidence | source_urls |` + ヒット0件なら
   「0件。使用パターン: <Grep パターン>」と報告（結果を捏造しない）。

### 6.3 週次分析（システムG）— Phase 2

1. **入力**: 「今週のSNS分析レポートを出して」（アカウント指定なしなら own_account: true の全アカウント）。
2. **処理**: 対象アカウントの直近4週間（posted_at 基準、null は collected_at で代用）の
   sns-post レコードを収集 → post_type ごとに件数・平均 likes/reposts/eng率を集計 →
   10件以上なら型・投稿時間帯の傾向を記述、未満なら「データ不足」→ 提案3件を作成。
3. **出力**: §5.6 のレポートファイル。既存同名ファイルがあれば上書き（週次は冪等）。

### 6.4 矛盾検出 — Phase 2

1. **入力**: principle レコードの新規 ingest（6.1 Step 5 の直後に割り込む）。
2. **処理**: 同じ `domain:` の既存レコードの `claim:` を Grep で列挙（最大50件を Read）→
   新 claim と意味的に対立するものを判定 → 対立あり: 両レコードの `contradicts` に相互 id を追記し、
   `intel/contradictions.md` に「判定待ち」で1行追記 → ユーザーに提示。
3. **出力**: ユーザーが判定を返したら台帳の状態を更新し、負け側レコードを `confidence: superseded` に変更。
   両立（条件差）なら両レコードの「適用条件・例外」に条件を追記。

### 6.5 ブックマーク取り込み — Phase 3

1. **入力**: `intel/inbox/` の未処理ファイル（または依頼文に直接貼られたURLリスト →
   Claude が inbox ファイルを作ってから同じフローに乗せる）。
2. **処理**: URL ごとに: X の URL → hermes エンジン（投稿・スレッド抽出クエリ）、
   それ以外 → hermes-web（UC5 特定URL深掘りテンプレ: 逐語引用 + 読了/途中切れ明示）。
   1ファイル最大10 URL、1 URL = 1クエリファイル（バッチ混載しない — 既存 SKILL.md の原則）。
3. **出力**: bookmark レコード（`> メモ` 行があれば tags と要点に反映）。原則が抽出できた場合は
   principle レコードも追加作成し `related` で相互リンク。処理済み inbox ファイルは
   `intel/inbox/done/` へ移動。

### 6.6 Kindle リサーチ・要約 — Phase 3

**正式案A（疑問即調査）**: 「Kindle: <書名> <疑問文>」→ 事実性の疑問は `engine: notebooklm`、
実践知・評判は `engine: hermes-web` → 結果を book-note レコード（`question` に疑問原文）として保存。

**正式案B（ハイライト一括取込）**: ユーザーが read.amazon.co.jp/notebook からハイライトを
コピーして `intel/inbox/kindle-<書名slug>.md` に貼る → Claude がトピックごとにクラスタリングし
book-note レコード化（1冊あたり最大20レコード。超過分は最重要順に絞り、残りは1レコードに
「その他ハイライト」としてまとめる）→ 原則として使えるものは principle にも昇格（related 連携）。

**却下案（元要求「Kindle VPN」= 閲覧画面の自動読取）**: 却下理由は §8 シナリオ4。

## 7. エッジケース

| ケース | 期待挙動 |
|---|---|
| リレー結果が `status: error` | レコード化しない。frontmatter の stderr を読み診断を報告。再 enqueue は1回まで |
| リレー結果 15分タイムアウト | 「watcher 停止の可能性」を報告し、hermes-x-search SKILL.md のトラブルシュート（watcher.log / schtasks 確認）を案内。レコード化しない |
| 同一 source_url のレコードが既存 | 新規作成せず既存 id を報告（再取り込み明示指示時のみ §11 の手順で新規作成） |
| 根拠URLゼロの調査結果 | principle 化しない。「出典なしのためレコード化見送り」と報告（捏造禁止 — twitter-intel と同じ鉄則） |
| metrics が1つも取れない sns-post | metrics 全フィールド null で保存可。週次分析では件数・型分類のみに使い、eng率集計から除外 |
| 週次分析の対象が0件 | レポートを作らず「対象レコード0件」と報告 |
| inbox ファイルに11件以上のURL | 先頭10件のみ処理し、残りを新しい inbox ファイルに分割して報告 |
| inbox ファイルがURL形式でない行のみ | 取り込まず「解釈できない行」を引用して確認 |
| Kindle ハイライト貼り付けが空・文字化け | レコード化せず、read.amazon.co.jp/notebook からのコピー手順（意図・内容・確認方法つき — CLAUDE.md の説明義務形式）を案内 |
| 矛盾判定に確信が持てない | contradicts は書かず、`related` にだけ入れて「グレー」としてユーザー提示（pickup-automation と同じグレー原則） |
| validate_intel.py が既存レコードでエラー | 新規作業を止め、壊れたレコードの修正を先に提案 |
| 巨大な生テキストをレコードに入れたくなった | 入れない。生テキストは hermes-relay の results/ が保持。レコードは `relay_result_id` で参照する |

## 8. 失敗シナリオとレッドチーム所見

計画ゲート回答の要約: 最大の敵は「技術」ではなく「取り込みの摩擦」。自動化できない部分
（自アカウント metrics・Kindle 本文・ブックマーク）を無理に自動化せず、手動投入の摩擦を
最小化する設計（inbox 投入・null 許容・enum 固定）に倒した。

| # | 失敗シナリオ | 早期警報サイン | 設計上の対策 |
|---|---|---|---|
| 1 | 取り込みが面倒でDBが育たず、3週間で更新が止まる | `git log --since='14 days ago' -- intel/` が0コミット | ingest をリレー調査の標準出口にする（調査したら自動でレコード化までがワンセット）。手動投入は inbox 1ファイル置くだけ。Phase 1 を「収集→保存→検索」だけに絞り初速を出す |
| 2 | システムGの metrics 自動取得が実現できず、分析が空回りする | sns-post レコードの metrics が全件 null | 設計時点で自動取得を前提にしない: metrics は null 許容、週次分析は「取れた分だけ」で動く。自アカウントは X API v2（X_BEARER_TOKEN、public_metrics）で補完可能だが必須にしない。impressions は手動入力を許す |
| 3 | 1結果=1レコードの粗い粒度で入れてしまい、矛盾検出と再検索が機能しない | principle レコードの claim に「〜について調べた結果」のような複文が入る | 1原則=1レコード・claim 1行を §5.2 で強制。validate_intel.py で claim 100文字超をエラーにする。矛盾突合は claim 同士のみ |
| 4 | 「Kindle VPN」（画面自動読取）を実装しようとして頓挫する | Kindle 用のスクレイパー・OCR・常駐プロセスの実装タスクが生える | 却下を設計で確定: Kindle 本文は DRM 保護されており、自動読取は Amazon 利用規約抵触リスク + 画面OCR常駐という脆い構成にしかならない。正式案は §6.6 の A（疑問即調査）+ B（公式ハイライトエクスポート取込）。この2つは追加インフラゼロで今日から動く |
| 5 | リポジトリ肥大・公開露出（自アカウント分析・戦略がDBに載る） | `intel/` 配下 2000 ファイル超、またはリポジトリ public 化の話が出る | 移行トリガーを §4/§11 に明文化（2000件 or public 化決定で private `intel-db` リポジトリへ移す）。生テキストはレコードに持たない（relay 側参照）。秘密情報（APIキー・未公開戦略の原文）はレコードに書かない |

## 9. 実装手順（Sonnet 向けタスク分割）

Phase 1（この順で。各タスク=1コミット目安）:

1. **intel/ 骨格 + README** — §4 のディレクトリと `intel/README.md`（§5 スキーマの写し + 運用ルール）を作成。完了条件: DoD 1項目目のファイルが全て存在。
2. **validate_intel.py** — §10 の仕様どおり実装。完了条件: レコード0件で `OK 0 records` exit 0、必須フィールド欠落・enum 違反・id/ファイル名不一致・claim 100文字超のテストレコードで exit 1。
3. **intel-hub スキル（Phase 1 範囲）** — SKILL.md に §6.1/6.2 の手順・§5 スキーマ・§7 エッジケースを収録。description の発動トリガー:「intelに入れて」「intelで検索」「調べてDBに蓄積」「リサーチDB」「過去に調べたことを探して」。完了条件: validate_skills.py exit 0。
4. **marketplace.json 追記 + ウォークスルーA/B + 導入確認** — 完了条件: Phase 1 DoD 全項目チェック。

Phase 2（Phase 1 完了後）:

5. **週次分析（§6.3 + §5.6）を SKILL.md に追加** — 完了条件: ウォークスルーC/D 通過。
6. **矛盾検出（§6.4 + §5.7）を SKILL.md に追加** — 完了条件: ウォークスルーE 通過。

Phase 3（Phase 2 完了後。順不同可）:

7. **ブックマーク取り込み（§6.5 + §5.8）** — 完了条件: ウォークスルーF 通過。
8. **Kindle 正式案A/B（§6.6）** — 完了条件: ウォークスルーG 通過 + ハイライト取込を実物1冊分で確認。

## 10. テスト計画

- **validate_intel.py（機械検証）**: 仕様 — `intel/principles/` `intel/sns/`（reports 除く）`intel/books/` `intel/`直下ではなく上記3系のみ走査。検査項目: ①YAML frontmatter がパース可能 ②共通必須フィールド（§5.1）が全て存在 ③type がディレクトリと一致（principles→principle 等）④enum フィールド（type/source_engine/confidence/domain/platform/post_type/original_platform）が定義値のみ ⑤id == ファイル名 stem ⑥source_engine が manual 以外なら source_urls 非空 ⑦principle の claim が存在し100文字以内。全部通れば `OK <N> records` exit 0、違反は「ファイルパス: 違反内容」を列挙して exit 1。実行テストは正常レコード・違反レコード各1件以上を一時作成して観察する（コード読みで済ませない）。
- **ウォークスルーA〜G（§3）**: 各 Phase の DoD に対応。A は hermes-relay の実在結果ファイルを入力にし、リレー往復なしで ingest 部分だけを検証できる。
- **リレー実往復テスト（Phase 1 完了時に1回）**: `engine: hermes-web` のクエリ1本を実際に enqueue → 結果から principle レコード化まで通し、所要時間と手数を記録する。
- **ネガティブ確認**: 「◯◯を調べて」（DB蓄積の指示なし）で勝手に intel/ へ書き込まないこと。twitter-intel / pickup-automation の依頼を intel-hub が横取りしないこと（SKILL.md の description で棲み分けを明記）。

## 11. 実装時判断ルール

- **hermes-web が未稼働の場合**（docs/hermes-web-engine-design.md の受け入れテスト未完了）: §6.1 のルーティングで hermes-web の行を notebooklm に読み替えて実装・運用する。SKILL.md にはルーティング表を「CLAUDE.md のエンジン表に従う」と書き、engine 名をハードコードしない。
- **再取り込みの明示指示があった場合**: 新レコードを作り、`related` に旧 id を入れる。旧レコードは変更しない。
- **1つの調査結果から principle と sns-post の両方が取れる場合**: 両方作り `related` で相互リンク。
- **domain / post_type の enum に当てはまらない場合**: 最も近い値を選び tags で補足する。enum への値追加はユーザー確認（勝手に増やさない — 増えると過去レコードとの集計互換が壊れる）。
- **tags の表記ゆれ**: 新タグを付ける前に同義タグを Grep（例: `sns` と `SNS運用`）。既存があればそちらに合わせる。
- **週次分析の「相関」の言い方**: 10件以上でも「相関がある」と断定せず「傾向」と書く。統計検定は実装しない（YAGNI。単純平均の比較のみ）。
- **intel/ の移行トリガー到達時**（2000件超 or public 化決定）: 実装者は移行を実行せず、ユーザーに報告して指示を待つ。
- **inbox の X ブックマークエクスポート形式が想定と違う場合**: パースを頑張らず、解釈できない行を引用してユーザーに形式を確認する。
- **コミット/push**: レコード追加はコミットまで。push はユーザー指示時のみ（既存運用どおり）。ただしリレークエリの enqueue は hermes-relay ブランチへの push が必須（これは従来から許可された運用）。

## 12. 未解決事項（ユーザー確認待ち）

- このリポジトリの公開/非公開の現状と方針（public なら Phase 1 着手前に `intel-db` private リポジトリ案へ切り替える — §8 シナリオ5）
- hermes-relay ブランチ既存 results/（20件超）の過去分を一括レコード化するか（Phase 1 完了後の任意バッチ）
- システムGで追う自アカウント・競合アカウントの初期リスト（platform / handle）
- X_BEARER_TOKEN を用意して自アカウント metrics を半自動取得するか（無しでも Phase 2 は動く）
- Instagram を Phase 2 の分析対象に含めるか（取得は手動入力前提のため、運用負荷と相談）
