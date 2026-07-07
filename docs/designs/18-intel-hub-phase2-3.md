# intel-hub Phase 2/3 詳細設計書

| 項目 | 値 |
|---|---|
| ステータス | 実装完了。Kindle/書籍取り込み（§6.4）は docs/designs/14-app-kindle-summarizer.md が正としてそちらの方式（My Clippings.txt パーサ）で実装済み |
| 種別 | スキル拡張 + スクリプト拡張（既存 intel-hub への後方互換追加） |
| 優先度 | Tier F-4 |
| 実装モデル | Sonnet 5（推奨 effort: high） |
| 依存する設計書 | docs/designs/03-intel-hub.md（親設計。本書はその Phase 2/3 の詳細化）、docs/designs/00-fable-sonnet-bridge.md（実装プロセス）、docs/hermes-web-engine-design.md（hermes-web エンジン。未完了なら §11 判断ルールで notebooklm 読み替え） |
| 依存する既存スキル | plugins/intel-hub（Phase 1 実装済み・本書で拡張）、plugins/hermes-x-search（リレー手順の正）、plugins/sns-ops-team（週次提案の受け手） |
| 外部依存 | hermes-relay ブランチ + ローカル watcher（稼働中）。X_BEARER_TOKEN（自アカウント metrics 取得、任意） |

## 1. 目的・背景（Why）

intel-hub は Phase 1（収集→保存→検索）まで実装済み。蓄積したレコードが「入れっぱなし」で、
分析・矛盾検出・外部ソース取り込みという「使う」側が未実装のため、DB を作った価値がまだ出ていない。
本書は 03-intel-hub.md の §6.3〜§6.6 骨子を、Sonnet が質問なしで実装できる粒度に詳細化する続編。

- **Phase 2（分析・相関）**: システムG の sns-post を投稿型で分類し、型×エンゲージメントの平均比較から
  「次週の投稿提案3件」を出す週次レポート生成、およびシステムR の principle 取り込み時の矛盾検出。
- **Phase 3（コネクタ）**: X ブックマーク/一般URLの inbox 取り込み、Kindle/書籍取り込み。
  inbox/ の投入形式パーサ（URLリスト型 / Kindleハイライト型）を確定する。

使う人は Ryo 本人のみ（biz-ops-guard 対象外）。Claude の役割はクエリ整形と結果整形（レコード正規化）のみで、
統計処理・自動スクレイピングはしない（03 の実装時判断ルール準拠）。

## 2. スコープ

### 2.1 やること

- **Phase 2-A 週次分析レポート**: `intel/sns/reports/<account>-<YYYY-Www>.md` を §5.1 の固定3セクション構成で生成。
  投稿型分類の確認 → 型別エンゲージメント平均比較 → 次週提案3件の決定を、§6.1 の確定アルゴリズムで行う。
- **Phase 2-B 矛盾検出**: principle 取り込み時に同 domain の既存 claim と突合し、対立ペアを両レコードの
  `contradicts` と `intel/contradictions.md` に記録、ユーザー判定で `superseded` 化する（§6.2）。
- **Phase 3-A ブックマーク/URL 取り込み**: `intel/inbox/<YYYY-MM-DD>-<slug>.md` のURLリストをパースし、
  X/一般Web を各エンジンに振り分けて bookmark レコード化。`intel/bookmarks/<YYYY-MM>/` を新設（§6.3）。
- **Phase 3-B Kindle/書籍取り込み**: 案A（疑問即調査→book-note）と案B（ハイライト一括→book-note クラスタ）。
  inbox パーサに Kindle ハイライト型（`kindle-*.md`）を追加（§6.4）。
- **scripts/validate_intel.py の後方互換拡張**: `bookmarks/` ディレクトリ走査追加、bookmark/book-note の
  追加必須フィールド検査（§10）。既存の principle/sns-post 検査ロジックは変更しない。
- **SKILL.md の拡張**: Phase 1 の既存節を残したまま、Phase 2/3 の節を追記し「未実装」注記を削除。
- 03 §3 の Phase 2/3 完成条件（ウォークスルー C〜G）を実行観察可能な形へ具体化（§3）。

### 2.2 やらないこと（明示的スコープ外）

- 統計的仮説検定（t検定・相関係数・p値）（YAGNI・03 §11 準拠。単純平均の比較のみ、表記は「傾向」で「相関」と断定しない）。
- 投稿文ドラフトの自動生成（sns-ops-team の担当。本書は「型+テーマ+根拠レコードid」までを渡す）。
- 自アカウント metrics の自動取得を必須化すること（X_BEARER_TOKEN があれば任意で補完、無くても動く。手動入力許可）。
- Instagram メトリクスの自動取得（手動入力前提。03 §2.2 準拠）。
- X ブックマーク API（OAuth 2.0 user context）への直接接続（エクスポート=URLリストの inbox 投入で足りる。03 §2.2 準拠）。
- Kindle 画面の自動読取・OCR・常駐（03 §8 シナリオ4で却下確定。案A/案B のみ）。
- Phase 1 の既存 SKILL.md 節（§1 収集・§2 検索・§3 エッジケース・§4 ネガティブ確認）の文言変更（後方互換のため不変を DoD に含める）。
- 既存 frontmatter フィールドの削除・リネーム（追加のみ許可。§10 後方互換要件）。
- 週次レポートファイル（`sns/reports/`）を validate_intel.py の per-record 検査対象に含めること（per-record でないため対象外のまま）。
- hermes-relay watcher 本体（`automation/*.ps1`）の改修（docs/hermes-web-engine-design.md の担当）。

## 3. 完成条件（Definition of Done）

後方互換（全 Phase 共通・先に確認）:

- [ ] `git diff` で `plugins/intel-hub/skills/intel-hub/SKILL.md` の Phase 1 節（「## 1. 収集」「## 2. 検索」「## 3. エッジケース（Phase 1範囲）」「## 4. ネガティブ確認」）に変更行が無い（追記のみ）。
- [ ] `intel/` 配下に bookmark レコードが1件も無い状態で `python scripts/validate_intel.py` を実行すると、Phase 2/3 実装前と同じ `OK <N> records`（N は不変）で exit 0。
- [ ] §5 の既存 frontmatter フィールドに削除・リネームが無い（`git diff intel/README.md scripts/validate_intel.py` で追加のみ）。

Phase 2-A（週次分析）:

- [ ] ウォークスルーC: `own_account: true` の sns-post レコード12件（1アカウント・2型以上・全件 metrics 入り、テスト用手作成可）を置いて「今週のSNS分析レポートを出して」と依頼すると、`intel/sns/reports/<account>-<YYYY-Www>.md` が §5.1 の3セクション（型別成績表・傾向所見・来週提案3件）で作られ、提案3件それぞれに `型` `テーマ` `根拠(レコードid)` が入る。
- [ ] ウォークスルーD（データ不足）: sns-post 5件のみで同依頼をすると、レポートの「傾向所見」セクションに `データ不足（10件未満）` と明記され、「傾向」「相関」を含む断定文が本文に無い（grep で確認）。
- [ ] ウォークスルーH（冪等）: 同じ入力で週次レポートを2回生成すると、同一パスに上書きされ、2回目実行後の `git status` で当該レポート以外のレコードファイルに変更が無い。
- [ ] ウォークスルーI（eng率ゼロ除算回避）: impressions が全件 null または 0 の型が混在しても、型別成績表の eng率 欄が `—` になり、例外・NaN・`inf` を出さない。

Phase 2-B（矛盾検出）:

- [ ] ウォークスルーE: claim が対立する principle 2件目（同 domain）を ingest すると、両レコードの `contradicts` に相互の id が入り、`intel/contradictions.md` に §5.2 形式の1行（状態=`判定待ち`）が追記され、ユーザーに対立ペアが提示される。
- [ ] ウォークスルーJ（グレー）: 対立が不確実な場合、`contradicts` は空のまま `related` にだけ相手 id が入り、`intel/contradictions.md` に行が追記されない。
- [ ] ウォークスルーK（判定反映）: 対立ペアにユーザーが「A採用」と判定を返すと、負け側 B の `confidence` が `superseded` になり、`intel/contradictions.md` の当該行の状態が `解決済み(A採用)` に更新される。

Phase 3-A（ブックマーク/URL）:

- [ ] ウォークスルーF: `intel/inbox/2026-07-15-test.md` にURL2行（`https://x.com/...` 1件 + `https://<web>/...` 1件）を置いて「inbox を取り込んで」と依頼すると、リレークエリ2本（X=ヘッダなし、Web=hermes-web）が別ファイルで enqueue され、結果到着後に bookmark レコード2件が `intel/bookmarks/<YYYY-MM>/` に作られ、inbox ファイルが `intel/inbox/done/` へ移動される。
- [ ] ウォークスルーL（メモ反映）: URL 行の直後に `> <メモ>` 行があると、その語が生成 bookmark レコードの `tags` か本文「## 要点」に反映される。
- [ ] ウォークスルーM（非URL行）: URL でも `>` メモでも空行でもない行を含む inbox ファイルは取り込まれず、当該行が引用されて形式確認を求められる（レコードは1件も作られない）。
- [ ] bookmark レコードで `python scripts/validate_intel.py` が exit 0（`intel/bookmarks/` が走査対象になり、`type: bookmark`・`original_platform` 検査を通る）。

Phase 3-B（Kindle/書籍）:

- [ ] ウォークスルーG（疑問即調査・案A）: 「Kindle: <書名> <疑問文>」形式の依頼で、事実性の疑問は `engine: notebooklm`、実践知・評判は `engine: hermes-web` のクエリが enqueue され、結果から book-note レコード（`question` に疑問原文・`book_title` 入り）が `intel/books/<YYYY-MM>/` に1件作られる。
- [ ] ウォークスルーN（ハイライト一括・案B）: `intel/inbox/kindle-<書名slug>.md` に read.amazon.co.jp/notebook 形式のハイライト3ブロック以上を貼って「inbox を取り込んで」と依頼すると、トピック単位に book-note レコード（`question: null`）が作られ、`位置No.` が読めたものは `kindle_location` に入り、inbox ファイルが `intel/inbox/done/` へ移動される。
- [ ] ウォークスルーO（上限）: ハイライト21ブロック以上の1冊で、book-note レコードが最大20件に絞られ、残りが1件の「その他ハイライト」レコードにまとめられる。

## 4. 成果物の構成（ファイルレイアウト）

```
plugins/intel-hub/skills/intel-hub/SKILL.md   # 変更: Phase 2/3 節を追記、冒頭「未実装」注記を削除
scripts/validate_intel.py                     # 変更: bookmarks/ 走査 + bookmark/book-note 追加検査
intel/README.md                               # 変更: bookmarks/ 追記・Phase 2/3「現状未使用」注記の削除
intel/bookmarks/.gitkeep                       # 新規: bookmark レコードの居場所
intel/bookmarks/<YYYY-MM>/<id>.md              # 実行時に生成される bookmark レコード（成果物ではなく運用生成物）
intel/sns/reports/<account>-<YYYY-Www>.md      # 実行時に生成される週次レポート（同上）
intel/books/<YYYY-MM>/<id>.md                  # 実行時に生成される book-note レコード（同上）
docs/designs/18-intel-hub-phase2-3.md          # 本書
```

新規ディレクトリは `intel/bookmarks/` のみ（`sns/reports/`・`books/`・`inbox/`・`inbox/done/` は Phase 1 で作成済み）。
`intel/bookmarks/` を新設する理由: Phase 1 のディレクトリ設計（03 §4）に bookmark 型の居場所が無く、
validate_intel.py の `DIR_TYPE` にも bookmark マッピングが無い。type=ディレクトリ整合検査を通すには専用ディレクトリが要る。

## 5. データ構造

既存スキーマ（03/README の §5.1〜5.5）は不変。本書で確定・追加するのは以下のみ。

### 5.1 週次分析レポート `intel/sns/reports/<account>-<YYYY-Www>.md`

ファイル名の `<account>` は handle 先頭の `@` を除き、英数字以外を `-` に置換した slug（例 `@ryo_dev` → `ryo-dev`）。
`<YYYY-Www>` は posted_at 基準の ISO 週（例 `2026-W28`）で「レポート対象週の末日を含む週」。

frontmatter（確定）:

```yaml
---
account: "@ryo_dev"          # 対象アカウント（元の handle 表記）
week: 2026-W28               # ISO週
window_start: 2026-06-15     # 集計対象期間の開始日（week 末日から28日前、UTC YYYY-MM-DD）
window_end: 2026-07-12       # 集計対象期間の末日（UTC YYYY-MM-DD）
generated_at: 2026-07-06     # 生成日（UTC YYYY-MM-DD）
records_used: [20260701T...-a, 20260703T...-b]   # 集計に使った sns-post の id リスト
records_count: 12            # records_used の件数
---
```

本文（3セクション固定・この順・見出し文字列も固定）:

```markdown
## 1. 型別成績表
| post_type | 件数 | 平均likes | 平均reposts | 平均eng率 |
|---|---|---|---|---|
| ノウハウ | 5 | 210.0 | 33.0 | 2.1% |
| 体験談 | 4 | 180.0 | 20.0 | — |
| 未分類 | 3 | 90.0 | 5.0 | 0.8% |

## 2. 傾向所見
（records_count が10件以上の時のみ、最大3行で「傾向」を記述。10件未満なら `データ不足（10件未満）` の1行のみ）

## 3. 来週の投稿提案（3件固定）
- 提案1: 型=ノウハウ / テーマ=<1行> / 根拠=20260701T...-a
- 提案2: 型=体験談 / テーマ=<1行> / 根拠=20260703T...-b
- 提案3: 型=質問投げかけ / テーマ=<1行> / 根拠=未使用型のため実験（該当レコードなし）
```

- 平均は小数第1位まで（`round(x, 1)`）。eng率 は百分率・小数第1位まで（例 `2.1%`）。
- eng率 = 型内で impressions が非 null かつ >0 のレコードのみを分母に `mean((likes+reposts)/impressions)`。該当0件なら `—`。
- `未分類` 行 = post_type が欠落/null の sns-post（後方互換のため validator では必須化しない。§10）。

### 5.2 矛盾台帳 `intel/contradictions.md`（03 §5.7 を確定）

既存ファイル（Phase 1 で空作成済み）に行を追記する。列は固定:

```markdown
| 検出日 | domain | レコードA | レコードB | 状態 |
|---|---|---|---|---|
| 2026-07-20 | 文章術 | 20260706T...-a | 20260720T...-b | 判定待ち |
```

- 検出日 = UTC YYYY-MM-DD。レコードA = 既存側、レコードB = 新規取り込み側。
- 状態 enum（この3値+A/B表記）: `判定待ち` / `解決済み(A採用)` / `解決済み(B採用)` / `両立(条件差)`。

### 5.3 bookmark レコード（03 §5.5 を確定・配置先を決定）

frontmatter は共通（§5.1 README）+ 追加2フィールド。配置先 `intel/bookmarks/<YYYY-MM>/<id>.md`。

```yaml
type: bookmark
original_platform: x | web    # enum 固定（既存 ENUMS 済み）
bookmarked_at: 2026-07-14      # 不明なら collected_at と同値
```

本文セクション（固定）: `## 要点` / `## 引用（逐語）` / `## 未確認・断定できない点`。

### 5.4 book-note レコード（03 §5.4 のまま。配置先確定）

配置先 `intel/books/<YYYY-MM>/<id>.md`。追加フィールドは README §type: book-note のとおり
（`book_title` / `book_author` / `kindle_location` / `question`）。本文 `## 回答/要約` / `## 引用（逐語）` / `## 未確認・断定できない点`。

### 5.5 inbox 投入形式（2種を確定）

パーサはファイル名で分岐する:

| ファイル名 | 形式 | 生成レコード | パーサ §6 |
|---|---|---|---|
| `kindle-*.md` | Kindle ハイライト型 | book-note | §6.4-B |
| 上記以外（`<YYYY-MM-DD>-<slug>.md`） | URLリスト型 | bookmark（+principle 任意） | §6.3 |

**URLリスト型の行文法（確定）**:
- URL 行: strip 後 `^https?://\S+$` に完全一致する行。
- メモ行: URL 行または直前のメモ行の直後にある `>` で始まる行（直前の URL に帰属）。
- 空行: 無視。
- 上記いずれでもない行 = 「非対応行」。非対応行が1つでもあれば取り込まず、その行を引用して形式確認（§7）。
- URL は最大10件/ファイル。11件目以降は先頭10件のみ処理し、残りを新 inbox ファイルに分割して報告（03 §7 準拠）。

**Kindle ハイライト型の行文法（確定）**:
- ブロック区切り = `位置No.?\s*\d+` または `(Location|位置)\s*\d+` にマッチする「位置行」、または空行2つ以上。
- 1ブロック = 直前の位置行までの本文テキスト（ハイライト逐語）+ その位置行（あれば `kindle_location` に格納）。
- 位置行が1つも見つからない場合: 空行区切りの各段落を1ハイライトとみなし、`kindle_location: null` で処理する。
- ファイル1行目が `# <書名>` 形式なら `book_title` に採用。無ければファイル名 `kindle-<slug>.md` の slug を暫定 `book_title` にし、ユーザーに書名を確認。

## 6. 処理フロー

### 6.1 週次分析（Phase 2-A）

1. **入力**: 「今週のSNS分析レポートを出して」。アカウント指定なしなら `own_account: true` の全アカウントを個別に処理（1アカウント=1レポート）。
2. **対象抽出**: 対象アカウントの sns-post を Grep で列挙 → posted_at（null は collected_at で代用）が
   `window_start`(=生成日を含む ISO 週の末日から27日前) 〜 `window_end`(=同 ISO 週の末日) に入るものを収集。
3. **型分類の確認**: 各 sns-post の post_type を読む。欠落/null は集計上 `未分類` バケットに入れる（レコードは書き換えない）。
4. **集計**: post_type ごとに 件数・平均likes・平均reposts・eng率（§5.1 の定義）を計算。impressions が null/0 の行は eng率 分母から除外。型内で該当0件なら eng率 `—`。
5. **傾向所見**: `records_count` >= 10 なら、最高 eng率 の型・平均likes 最大の型・（posted_at がある場合）投稿時間帯の偏りを最大3行で「傾向」記述。< 10 なら `データ不足（10件未満）` の1行のみ（断定文禁止）。
6. **来週提案3件（確定アルゴリズム）**: 型を「eng率 降順（`—` は最下位）→ 平均likes 降順」でソートし、実データのある型リスト `R`、8種 enum のうち未使用の型リスト `U`（enum 定義順）を作る。
   - 提案1 = `R[0]`（最良型・継続）。テーマ = `R[0]` の最高 likes レコードの tags から1語。根拠 = そのレコード id。
   - 提案2 = `R[1]` があればそれ（継続）。無ければ `U[0]`（実験）。根拠 = レコード id（実験なら「該当レコードなし」）。
   - 提案3 = `U[0]`（`U` が空なら `R[2]`、それも無ければ `R[0]` を別テーマで）。実験提案は根拠に「未使用型のため実験（該当レコードなし）」。
7. **出力**: §5.1 のレポートを `intel/sns/reports/<account>-<YYYY-Www>.md` に書く。既存同名は上書き（冪等）。レポート以外のレコードは変更しない。validate_intel.py を実行し exit 0 を確認してコミット（push はユーザー指示時のみ）。

### 6.2 矛盾検出（Phase 2-B）

06.1(ingest) の 03 §6.1 Step 5（principle 正規化直後・保存前）に割り込む。

1. **候補列挙**: 新 principle の `domain` 値で `intel/principles/` を Grep（`^domain: <D>$`）→ ヒットファイルの `claim:` を Read（最大50件）。
2. **判定**: 新 claim と各既存 claim を Claude が意味的に突合。「同じ適用条件で結論が逆」なら対立。確信が持てないものは対立にしない。
3. **対立あり（確信）**: 新レコードと既存レコード双方の `contradicts` に相互 id を追記。`intel/contradictions.md` に §5.2 形式で1行（状態=`判定待ち`）追記。対立ペアをユーザーに提示。
4. **対立あり（不確実=グレー）**: `contradicts` は書かず、双方の `related` に相手 id を入れるのみ。台帳には追記しない。「グレー」と明示してユーザーに提示。
5. **ユーザー判定の反映**: 「A採用」→ B の `confidence` を `superseded` に変更・台帳状態を `解決済み(A採用)` に更新。「B採用」→ 対称。「両立」→ 双方の「## 適用条件・例外」に区別条件を追記・台帳状態を `両立(条件差)`。負けレコードは削除しない。

### 6.3 ブックマーク/URL 取り込み（Phase 3-A）

1. **入力**: `intel/inbox/` の未処理ファイル（`done/` 以外・`kindle-*.md` 以外）。依頼文に直接貼られたURLは、まず Claude が `intel/inbox/<YYYY-MM-DD>-<slug>.md` を作ってから同フローに乗せる。
2. **パース**: §5.5 URLリスト型の行文法。非対応行があれば中断してユーザー確認（レコード0件）。
3. **エンジン振り分け（1 URL = 1クエリファイル。バッチ混載しない）**:
   - host が `x.com` / `twitter.com` → ヘッダなし（hermes x_search、投稿/スレッド逐語抽出クエリ）。
   - それ以外 → `engine: hermes-web`（特定URL深掘りテンプレ: 逐語引用+読了/途中切れ明示）。hermes-web 未稼働時は §11 で notebooklm 読み替え。
4. **結果待ち**: 03 §6.1 Step 4 と同じポーリング（30秒間隔・15分タイムアウト）。
5. **レコード化**: URL ごとに bookmark レコードを `intel/bookmarks/<YYYY-MM>/` に作成。`original_platform` は host で決定。`> メモ` があれば tags と「## 要点」に反映。`bookmarked_at` 不明なら collected_at と同値。
6. **原則昇格（任意）**: 本文から明確な原則が抽出でき根拠URLがあれば principle レコードも追加作成し、`related` で相互リンク（03 §6.5 準拠）。
7. **後処理**: 重複チェック（source_urls を intel/ 全体 Grep）→ validate_intel.py exit 0 → 処理済み inbox ファイルを `intel/inbox/done/` へ移動 → コミット。

### 6.4 Kindle/書籍取り込み（Phase 3-B）

**【設計整合メモ・実装前に必読】** 本節は執筆時点（並列設計中）で
`docs/designs/14-app-kindle-summarizer.md` の存在を検知できず独自に書いた案。
14 は Kindle 入力の**正式な詳細設計**（My Clippings.txt パーサ方式を採用、
read.amazon.co.jp 貼り付け方式は法的リスクで却下）であり、本節の案A/B とは
入力方式が異なる。**実装は 14 を正とし、本節の案A/Bはその前段階の構想として
参考にとどめる**（14 §5 のパーサ・スキーマ定義を優先し、下記の inbox 貼り付け
前提は採用しない）。矛盾点: 本節はread.amazon.co.jp/notebookからの貼り付け
（inbox/kindle-*.md）を前提にしているが、14はこれをブラウザ拡張と同様に
ToS/保守コストの観点で却下し、My Clippings.txt（端末エクスポート）を選定している。

**案A（疑問即調査）**:
1. 入力「Kindle: <書名> <疑問文>」。
2. エンジン選択: 事実性の疑問（用語定義・事実確認）→ `engine: notebooklm` + `topic:`。実践知・評判・比較 → `engine: hermes-web`。
3. 結果から book-note レコードを `intel/books/<YYYY-MM>/` に作成。`question` に疑問原文・`book_title` に書名・`kindle_location: null`。
4. validate_intel.py exit 0 → コミット。原則化できるなら principle 昇格+`related`。

**案B（ハイライト一括）**:
1. 入力: `intel/inbox/kindle-<書名slug>.md`（read.amazon.co.jp/notebook からコピー貼付）。
2. パース: §5.5 Kindle ハイライト型。`book_title` は1行目 `# <書名>` かファイル名 slug（後者ならユーザー確認）。
3. クラスタリング: Claude がハイライトをトピック単位に束ね、1トピック=1 book-note レコード。`question: null`・`kindle_location` は代表ハイライトの位置。
4. 上限: 1冊あたり最大20 book-note。超過分は重要度降順で20件に絞り、残りを1件の「その他ハイライト」レコード（本文「## 引用（逐語）」に列挙）にまとめる。
5. 原則化: 原則として使えるハイライトは principle にも昇格し `related` 連携（03 §6.6 案B 準拠）。
6. 後処理: validate_intel.py exit 0 → inbox ファイルを `done/` へ移動 → コミット。

## 7. エッジケース

| ケース | 期待挙動 |
|---|---|
| 週次分析の対象 sns-post が0件 | レポートを作らず「対象レコード0件（アカウント/期間）」と報告 |
| 週次分析で post_type が全件欠落 | 全件を `未分類` 行に集計し、提案は `U`（未使用型）からの実験3件になる。エラーにしない |
| eng率 の impressions が 0 の行 | ゼロ除算せず、その行を eng率 分母から除外（likes/reposts の平均には含める） |
| 型別成績表の型が1種のみ | 提案2/3 は未使用型 `U` からの実験提案で3件を満たす |
| 週次レポート再生成（同週2回目） | 同一パスに冪等上書き。他レコードは変更しない |
| 矛盾候補が50件超 | 直近 collected_at 降順で50件のみ Read。その旨をユーザーに報告 |
| 矛盾判定に確信が持てない | `contradicts` に書かず `related` のみ・台帳に追記しない（グレー提示） |
| 既に `superseded` のレコードとの対立 | 台帳に追記せず「既に superseded 済み」と報告のみ |
| inbox に非URL行が混在（URLリスト型） | 取り込まず、非対応行を引用して形式確認（レコード0件） |
| inbox のURLが11件以上 | 先頭10件のみ処理し、残りを新 inbox ファイルに分割して報告 |
| bookmark の source_url が既存レコードと重複 | 新規作成せず既存 id を報告（03 §6 重複チェック準拠） |
| Kindle ハイライト貼付が空/文字化け | レコード化せず、read.amazon.co.jp/notebook のコピー手順（意図・内容・確認方法つき、CLAUDE.md 説明義務形式）を案内 |
| Kindle ハイライトに位置行が全く無い | 空行区切りで段落=ハイライトとして処理・`kindle_location: null`。書名不明ならユーザー確認 |
| Kindle ハイライトが21ブロック以上 | 重要度降順で20件+「その他ハイライト」1件に集約 |
| リレー結果が `status: error` / 15分タイムアウト | レコード化しない。03 §7 と同じ診断・案内（再enqueueは1回まで） |
| validate_intel.py が既存レコードでエラー | 新規作業を止め、壊れたレコードの修正を先に提案 |
| `intel/` レコードが2000件超 or public化決定 | 実装者は移行せずユーザーに報告して指示待ち（03 §11 移行トリガー） |

## 8. 失敗シナリオとレッドチーム所見

| # | 失敗シナリオ | 早期警報サイン | 設計上の対策 |
|---|---|---|---|
| 1 | 週次分析の metrics がほぼ null で、提案が「未使用型を試せ」ばかりになり無価値化 | 直近レポートの型別成績表の eng率 が全行 `—` | metrics null 許容で「取れた分だけ」動く設計を維持。提案アルゴリズムは metrics 無しでも件数・型分類で回る。X_BEARER_TOKEN での自アカウント補完を §11 に用意（任意）。impressions は手動入力を許可 |
| 2 | 矛盾検出が Claude の主観判定頼みで、誤検出（実は両立）や見逃しが多発し `contradictions.md` が信用されなくなる | 台帳の `両立(条件差)` 行が `判定待ち` より多い／ユーザーが台帳を見なくなる | 対立は「同一適用条件で結論が逆」に限定・確信が無ければ `related` のグレー止まり（誤検出より見逃し寄りに倒す）。最終判定は必ずユーザー。台帳は削除せず監査可能に |
| 3 | inbox パーサが X ブックマークの実際のコピー形式（URL以外の本文混じり）を弾き続け、Phase 3 が使われない | inbox に置いたファイルが毎回「非対応行」で差し戻される | パーサ形式を §5.5 で確定し SKILL.md に明記（URL 1行1件+`>`メモのみ）。実運用で3回以上差し戻しが起きたら X ブックマーク API 直結を再検討（03 §2.2 の再検討トリガー）。Kindle 型は別パーサに分離してURLパーサを単純に保つ |

### 8.1 自己反証（skill-design-rigor 4項目）

1. **本当に必要か（YAGNI）**: 週次分析・矛盾検出・コネクタは 03 で計画済みの中核価値。ただし「提案3件固定」は over-spec の疑い → §6.1 で決定論的アルゴリズムに固定し、投稿文生成は sns-ops-team に外出しして肥大化を防いだ。統計検定は明示的に不採用。
2. **後方互換は本物か**: SKILL.md Phase 1 節不変・既存 frontmatter 追加のみ・validate_intel.py は `DIR_TYPE` 追加と新 type の追加検査のみ（既存 principle/sns-post 経路に分岐追加なし）を DoD 化。bookmark を既存 `books/` に相乗りさせず専用 `bookmarks/` にしたのは type=ディレクトリ整合検査を壊さないため。
3. **判定境界は観察可能か**: 「10件未満=データ不足」「eng率 分母は impressions>0」「提案の R/U ソート順」「inbox 非対応行=中断」など、真偽が grep/ファイル存在で判定できる形に落とした。曖昧さの残る「意味的対立」「トピッククラスタ」は Claude 判断と明記し、誤りは全てユーザー判定で救済する設計。
4. **最大の穴**: 設計14（Kindle/書籍取り込みの専用設計）が存在しない（docs/designs は10まで）。本書は Kindle を 03 §6.6 準拠で自己完結させたが、将来 book 専用設計が起きたら book-note の扱いを再統合する必要がある（§12 に明記）。

## 9. 実装手順（Sonnet 向けタスク分割）

Phase 2 → Phase 3 の順（Phase 2 内は 5→6、Phase 3 内は順不同可）。各タスク=1コミット目安。

1. **validate_intel.py 後方互換拡張** — `DIR_TYPE` に `"bookmarks": "bookmark"` 追加。bookmark レコードに `original_platform` 必須検査、book-note に `book_title` 必須検査を追加（既存 principle/sns-post 経路は不変）。完了条件: 既存レコードで `OK <N> records`（N不変）exit 0。bookmark/book-note の違反テストレコードで exit 1。DoD 後方互換3項目通過。
2. **intel/ 骨格追加** — `intel/bookmarks/.gitkeep` 作成。`intel/README.md` に bookmarks/ 追記・Phase 2/3「現状未使用」注記を「実装済み」へ更新（既存フィールド定義は不変）。完了条件: `git diff intel/README.md` が追加/注記変更のみ。
3. **週次分析を SKILL.md に追加（§6.1+§5.1）** — 完了条件: ウォークスルー C/D/H/I 通過。
4. **矛盾検出を SKILL.md に追加（§6.2+§5.2）** — 完了条件: ウォークスルー E/J/K 通過。
5. **ブックマーク/URL 取り込みを SKILL.md に追加（§6.3+§5.3+§5.5）** — 完了条件: ウォークスルー F/L/M + bookmark validate 通過。
6. **Kindle 取り込みを SKILL.md に追加（§6.4+§5.4+§5.5）** — 完了条件: ウォークスルー G/N/O 通過。
7. **SKILL.md 冒頭「未実装」注記の削除 + 導入確認** — description の未実装文を実装済みへ更新。完了条件: `python scripts/validate_skills.py` exit 0、`/plugin install`→`/plugin list` で intel-hub 導入確認、後方互換 DoD 3項目再確認。

## 10. テスト計画

- **validate_intel.py 拡張（機械検証・実行必須）**: ①既存 principle/sns-post/book-note レコードで `OK <N> records`（拡張前と同じ N）exit 0 ②`intel/bookmarks/<YYYY-MM>/` に正常 bookmark 1件を置き exit 0 ③`original_platform` 欠落の bookmark・`book_title` 欠落の book-note で exit 1（「ファイルパス: 違反内容」を出力）④`type: bookmark` を `books/` に置くと type=ディレクトリ不一致で exit 1。コード読みで済ませず一時レコードを作って観察する。
- **ウォークスルー C〜O（§3）**: 各 Phase の DoD に対応。C/D は sns-post テストレコード手作成、E は対立 principle 2件手作成、F は inbox テストファイル、N/O は Kindle ハイライト貼付テストで検証。
- **リレー実往復テスト（Phase 3 完了時に1回）**: URL 1本（Web）を実際に inbox→enqueue→bookmark レコード化まで通し、所要時間と手数を記録。
- **後方互換回帰**: Phase 2/3 実装後に、Phase 1 の既存ウォークスルー A/B（03 §3）が引き続き通ることを確認。
- **ネガティブ確認**: 「先週の投稿どうだった?」等の曖昧依頼で勝手にレポート生成・レコード書き込みをしないこと。twitter-intel/pickup-automation の依頼を横取りしないこと。

## 11. 実装時判断ルール

- **hermes-web 未稼働時**: §6.3/§6.4 の hermes-web 行を notebooklm に読み替える。SKILL.md にエンジン名をハードコードせず「CLAUDE.md/03 のルーティング表に従う」と書く（03 §11 準拠）。
- **post_type 欠落の sns-post**: 週次分析では `未分類` バケットに入れる。既存レコードを書き換えて post_type を後付けしない（矛盾集計の互換を壊さない）。validator でも post_type を必須化しない（後方互換）。
- **矛盾の「対立」定義**: 「同一の適用条件で結論が逆」のみ対立。適用条件が違うなら対立でなく `related`。確信が持てなければグレー（related のみ）。最終判定は必ずユーザー。
- **提案テーマの語選び**: 根拠レコードの tags から選ぶ。tags が薄いなら「## 伸びた/伸びない要因の仮説」から1語。捏造しない。
- **eng率 の表記**: 「相関がある」と断定せず「傾向」と書く。統計検定は実装しない（03 §11・単純平均比較のみ）。
- **inbox の X ブックマークエクスポート形式が §5.5 と違う**: パースを頑張らず、非対応行を引用して形式確認（03 §11 準拠）。
- **Kindle 書名が特定できない**: ファイル名 slug を暫定採用しユーザーに確認（勝手に確定しない）。
- **enum に無い post_type/domain**: 最も近い値+tags 補足。enum 追加はユーザー確認（03 §11。集計互換を壊す）。
- **コミット/push**: レコード・レポート追加はコミットまで。push はユーザー指示時のみ。リレークエリ enqueue の hermes-relay ブランチ push は従来どおり必須。
- **移行トリガー到達時（2000件超 or public化決定）**: 実装者は移行せずユーザー報告（03 §11）。

## 12. 未解決事項（ユーザー確認待ち）

- **設計14が存在しない**: 本書は「Kindle/書籍取り込み（設計14と連携）」を指示されたが、`docs/designs/` は10までで14は無い。本書は Kindle を 03 §6.6 準拠で自己完結実装する前提で設計した。将来 book 専用設計（14）を起こす場合、本書 §6.4/§5.4 の book-note 扱いを再統合するか要確認。
- **追う自アカウント/競合アカウントの初期リスト**（platform/handle）: 週次分析の `own_account` 対象を確定するのに必要（03 §12 から継続）。
- **X_BEARER_TOKEN を用意して自アカウント metrics を半自動取得するか**: 無くても Phase 2 は動くが、有ると impressions/likes 補完で提案精度が上がる（03 §12 から継続）。
- **Instagram を週次分析の対象に含めるか**: 取得は手動入力前提のため運用負荷と相談（03 §12 から継続）。
- **X ブックマークの実運用コピー形式**: §5.5 は「URL 1行1件+`>`メモ」を前提とするが、実際にユーザーがどうエクスポートするか（手動コピー/拡張機能）が未確定。差し戻し多発時は API 直結を再検討。
