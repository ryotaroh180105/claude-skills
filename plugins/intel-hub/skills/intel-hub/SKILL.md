---
name: intel-hub
description: hermes-relay経由で調べた原則・知見（システムR）やSNS投稿（システムG）を intel/ 配下のMarkdown+YAML frontmatterレコードとして正規化・蓄積し、Grepベースで再検索するスキル。週次SNS分析レポート、principle矛盾検出、ブックマーク/URL取り込み、Kindleハイライト・読書中疑問の取り込みも扱う。「intelに入れて」「intelで検索」「調べてDBに蓄積」「リサーチDB」「過去に調べたことを探して」「今週のSNS分析レポートを出して」「inboxを取り込んで」「Kindle: <書名> <疑問文>」といった依頼で使う。単に「◯◯を調べて」だけの依頼（DB蓄積の指示なし）では発動しない。X収集そのものは twitter-intel、ROADMAP候補出しは github-trends/pickup-automation の担当であり、本スキルはその結果をDB化・再検索する後段工程を担う。Phase 1（収集→保存→検索）・Phase 2（週次分析・矛盾検出）・Phase 3（ブックマーク/Kindle取り込み）すべて実装済み。
---

# intel-hub（Phase 1〜3: 収集→保存→検索→分析→コネクタ）

`intel/` 配下の Markdown レコードDBへの ingest（正規化して保存）・検索・週次分析・矛盾検出・
外部コネクタ取り込みを行う。スキーマ・運用ルールの正は `intel/README.md`。処理フロー・
エッジケースの正は `docs/designs/03-intel-hub.md`（Phase 1）、`docs/designs/18-intel-hub-phase2-3.md`
（Phase 2/3 詳細）、`docs/designs/14-app-kindle-summarizer.md`（Kindle入力層。Kindleは18ではなく
こちらが正 — 18 §6.4 参照）。

## 1. 収集（ingest）

### 1.1 入力

- ユーザーの調査依頼（例:「note の文章術の原則を調べて intel に入れて」）
- または既存の hermes-relay 結果ファイルの直接指定（例: ウォークスルーAのように
  `automation/results/<id>.md` を指定される）

### 1.2 エンジン選択（クエリ整形のみ。実行体は hermes-relay）

| 調査種別 | ヘッダ | 実行体 |
|---|---|---|
| 事実（法律・IR・公式ドキュメントの確認） | `engine: notebooklm` + `topic:` | NotebookLM Deep Research |
| トレンド・実践知（Web記事・比較） | `engine: hermes-web` | Hermes web_search/web_extract（Grok） |
| Xの投稿・反応・アカウント分析 | ヘッダなし | Hermes x_search（Grok） |

hermes-web が未稼働（docs/hermes-web-engine-design.md の受け入れテスト未完了）の場合は
上表の hermes-web 行を notebooklm に読み替える。engine 名をハードコードせず、CLAUDE.md /
本表のルーティングに従う。

クエリの整形手順（enqueue・ポーリングのコマンド含む）は `plugins/hermes-x-search/skills/hermes-x-search/SKILL.md`
の「Automated relay」節をそのまま使う（本スキルは変更・再実装しない）。日本語指定・
出力セクション指定・根拠URL必須・逐語引用・ASCIIダブルクォート禁止のチェックリストに従う。

### 1.3 正規化（結果 → レコード）

1. 結果本文（またはユーザーが直接渡した調査結果）から原則・投稿・知見を抽出する。
   1結果あたり最大10件。根拠URLの無い主張はレコード化しないか `confidence: unconfirmed` にする。
2. 1原則 = 1 principle レコード（`claim` は1行・100文字以内）。sns-post も同じ手順で
   type: sns-post として正規化する。1つの調査結果から principle と sns-post の両方が
   取れる場合は両方作り `related` で相互リンクする。
3. ファイルパス: `intel/principles/<YYYY-MM>/<id>.md` または `intel/sns/<YYYY-MM>/<id>.md`。
   `<id>` は `intel/README.md` の共通 frontmatter 仕様どおり `<UTC時刻>-<slug>`。
4. frontmatter・本文セクションは `intel/README.md` の該当 type の仕様に厳密に従う
   （本文セクションは順序固定。空でも見出しは残し「該当なし」と書く）。
5. domain / post_type / platform 等の enum に当てはまらない場合は最も近い値を選び
   tags で補足する。enum への値追加はユーザー確認を取ってから行う。

### 1.4 重複チェック（レコード作成前に必ず実行）

`source_urls` の各URLを `intel/` 全体に Grep する。ヒットしたら新規作成せず既存 id を
報告する（再取り込みの明示指示があった場合のみ新規作成し `related` に旧 id を入れる。
旧レコードは変更しない）。

### 1.5 検証・保存

`python scripts/validate_intel.py` を実行し exit 0 を確認してからコミットする。
push はユーザー指示時のみ（リレークエリの enqueue 自体は hermes-relay ブランチへの
push が必須で、これは従来どおり許可されている）。

## 2. 検索

1. 入力例:「intel で note の文章術を検索して」
2. Grep を2段で実行する（`path: intel/` 固定。`intel/README.md` と `intel/contradictions.md`
   はスキーマ説明文にヒットするノイズ源なので検索対象から除外し、レコードファイル
   （`intel/principles/`・`intel/sns/`・`intel/books/` 配下）だけを見る）。
   1. frontmatter: `claim:` `tags:` `domain:` `book_title:` を対象に Grep
   2. ヒットが薄ければ本文全文を対象に Grep
3. 出力: 表 `| id | type | claim/要点1行 | confidence | source_urls |`。
   ヒット0件なら「0件。使用パターン: <実際に使ったGrepパターン>」と報告する
   （結果を捏造しない）。

## 3. エッジケース（Phase 1範囲）

| ケース | 期待挙動 |
|---|---|
| リレー結果が `status: error` | レコード化しない。frontmatter の stderr を読み診断を報告。再enqueueは1回まで |
| リレー結果 15分タイムアウト | 「watcher停止の可能性」を報告し、hermes-x-search SKILL.mdのトラブルシュート（watcher.log / schtasks確認）を案内。レコード化しない |
| 同一 source_url のレコードが既存 | 新規作成せず既存idを報告（再取り込み明示指示時のみ新規作成） |
| 根拠URLゼロの調査結果 | principle化しない。「出典なしのためレコード化見送り」と報告（捏造禁止） |
| metricsが1つも取れないsns-post | metrics全フィールドnullで保存可 |
| validate_intel.pyが既存レコードでエラー | 新規作業を止め、壊れたレコードの修正を先に提案 |
| 巨大な生テキストをレコードに入れたくなった | 入れない。生テキストはhermes-relayのresults/が保持。レコードは`relay_result_id`で参照する |

## 4. ネガティブ確認（発動範囲）

- 「◯◯を調べて」だけでDB蓄積の指示が無い場合、勝手に `intel/` へ書き込まない。
- X収集そのものの依頼は twitter-intel / hermes-x-search の担当。本スキルはその結果を
  DB化・再検索したいときにのみ発動する。

## 5. 週次分析（システムG / Phase 2-A）

処理・データ構造の正は `docs/designs/18-intel-hub-phase2-3.md` §5.1・§6.1・§7。

### 5.1 入力

「今週のSNS分析レポートを出して」。アカウント指定なしなら `own_account: true` の
全アカウントを個別に処理する（1アカウント = 1レポート）。

### 5.2 対象抽出・集計

1. 対象アカウントの sns-post レコードを `intel/sns/` から Grep で列挙し、`posted_at`
   （null なら `collected_at` で代用）が集計期間（生成日を含む ISO週の末日から27日前
   〜 その末日、`window_start`〜`window_end`）に入るものを収集する。
2. 対象0件なら レポートを作らず「対象レコード0件（アカウント/期間）」と報告して終了する。
3. `post_type` ごとに 件数・平均likes・平均reposts・eng率を集計する。`post_type` が
   欠落/null のレコードは `未分類` バケットに入れる（レコード自体は書き換えない）。
4. eng率 = 型内で `impressions` が非null かつ >0 のレコードのみを分母に
   `mean((likes+reposts)/impressions)`。該当0件なら `—`（ゼロ除算・NaN・inf を出さない）。
5. `records_count`（集計に使ったレコード数）が10件以上なら、最高eng率の型・平均likes最大の型・
   （posted_at がある場合）投稿時間帯の偏りを最大3行で「傾向」として記述する。10件未満なら
   「傾向所見」セクションに `データ不足（10件未満）` の1行のみを書き、「傾向」「相関」を
   含む断定文を書かない。
   さらに型同士の比較（「型Xが型Yより伸びる」）は**比較する各型が n≧5 の場合のみ**書く。
   n<5 の型は型別成績表に出すだけでランキング・傾向文から除外する（外れ値1件で順位が
   反転する規模の比較は傾向として意味を持たないため。§5.3 の提案では実験枠として扱う）。

### 5.3 来週の投稿提案3件（確定アルゴリズム）

型を「eng率 降順（`—` は最下位）→ 平均likes 降順」でソートし、実データのある型リスト `R`、
8種enumのうち未使用の型リスト `U`（enum定義順）を作る。

- 提案1 = `R[0]`（最良型・継続）。テーマ = `R[0]` の最高likesレコードのtagsから1語。
  根拠 = そのレコードid。
- 提案2 = `R[1]` があればそれ（継続）。無ければ `U[0]`（実験）。根拠は該当レコードid、
  実験提案なら「未使用型のため実験（該当レコードなし）」。
- 提案3 = `U[0]`（`U` が空なら `R[2]`、それも無ければ `R[0]` を別テーマで）。実験提案は
  根拠に「未使用型のため実験（該当レコードなし）」。
- テーマは根拠レコードの `tags` から選ぶ。tagsが薄いなら「## 伸びた/伸びない要因の仮説」
  から1語。捏造しない。投稿文そのものは書かない（sns-ops-team に渡す）。

### 5.4 出力

`intel/sns/reports/<account>-<YYYY-Www>.md`（`<account>` は handle 先頭の `@` を除き
非英数字を `-` に置換したslug、`<YYYY-Www>` はレポート対象週末日のISO週）に、
frontmatter（`account`/`week`/`window_start`/`window_end`/`generated_at`/`records_used`/
`records_count`）+ 固定3セクション（`## 1. 型別成績表` `## 2. 傾向所見`
`## 3. 来週の投稿提案（3件固定）`）を書く。既存同名ファイルがあれば上書き（週次は冪等）。
レポート以外のレコードは変更しない。`python scripts/validate_intel.py` を実行し
exit 0 を確認してからコミットする（push はユーザー指示時のみ）。

## 6. 矛盾検出（システムR / Phase 2-B）

処理の正は `docs/designs/18-intel-hub-phase2-3.md` §6.2・§7。principle の新規 ingest
（§1.3 正規化直後・保存前）に割り込む。

1. **候補列挙**: 新 principle の `domain` 値で `intel/principles/` を Grep（`^domain: <D>$`）
   → ヒットファイルの `claim:` を Read（最大50件。50件超なら直近 `collected_at` 降順で
   50件のみ読み、その旨を報告）。
2. **判定**: 新claimと各既存claimを意味的に突合する。「同一の適用条件で結論が逆」なら対立。
   適用条件が違うだけなら対立ではなく `related`。確信が持てなければ対立にしない（グレー、
   見逃し寄りに倒す）。
3. **対立あり（確信）**: 新旧両レコードの `contradicts` に相互idを追記。
   `intel/contradictions.md` に `| 検出日 | domain | レコードA(既存) | レコードB(新規) | 判定待ち |`
   の1行を追記し、対立ペアをユーザーに提示する。
4. **対立あり（不確実 = グレー）**: `contradicts` は書かず、双方の `related` にのみ相手idを
   入れる。台帳には追記しない。「グレー」と明示してユーザーに提示する。
5. **既にsupersededのレコードとの対立**: 台帳に追記せず「既にsuperseded済み」と報告のみ。
6. **ユーザー判定の反映**: 「A採用」→ Bの `confidence` を `superseded` に変更し、台帳の
   当該行の状態を `解決済み(A採用)` に更新（対称も同様）。「両立」→ 双方の
   「## 適用条件・例外」に区別条件を追記し、台帳状態を `両立(条件差)` にする。負けレコードは
   削除しない。

## 7. ブックマーク/URL 取り込み（Phase 3-A）

処理の正は `docs/designs/18-intel-hub-phase2-3.md` §5.3・§5.5・§6.3・§7。

### 7.1 入力・行文法

`intel/inbox/` の未処理ファイル（`done/` 以外・`kindle-*.md` 以外。ファイル名形式
`<YYYY-MM-DD>-<slug>.md`）。依頼文に直接URLが貼られた場合は、まずこの形式のinboxファイルを
作ってから同じフローに乗せる。行文法（確定）:

- URL行: strip後 `^https?://\S+$` に完全一致する行。
- メモ行: URL行または直前のメモ行の直後にある `>` で始まる行（直前のURLに帰属）。
- 空行: 無視。
- 上記いずれでもない行 = 非対応行。1つでもあれば取り込まず、その行を引用して形式確認する
  （レコード0件で中断）。
- URLは最大10件/ファイル。11件目以降は先頭10件のみ処理し、残りを新しいinboxファイルに
  分割して報告する。

### 7.2 エンジン振り分け（1 URL = 1クエリファイル。バッチ混載しない）

- host が `x.com` / `twitter.com` → ヘッダなし（hermes x_search、投稿/スレッド逐語抽出）。
- それ以外 → `engine: hermes-web`（特定URL深掘り: 逐語引用+読了/途中切れ明示）。
  hermes-webが未稼働なら notebooklm に読み替える（engine名をハードコードしない）。

結果待ちは §1 と同じポーリング（30秒間隔・15分タイムアウト）。

### 7.3 レコード化・後処理

URLごとに bookmark レコードを `intel/bookmarks/<YYYY-MM>/<id>.md` に作る。
`original_platform` はhostで決定。`> メモ` があれば `tags` と「## 要点」に反映。
`bookmarked_at` 不明なら `collected_at` と同値。本文から明確な原則が抽出でき根拠URLが
あれば principle レコードも追加作成し `related` で相互リンクする（任意）。

重複チェック（§1.4 と同じ、source_urlsをintel/全体Grep）→ `python scripts/validate_intel.py`
exit 0 → 処理済みinboxファイルを `intel/inbox/done/` へ移動 → コミット。

## 8. Kindle コネクタ（Phase 3 / 設計14）

入力の受け口の正は `docs/designs/14-app-kindle-summarizer.md`（book-noteスキーマ・保存・
検索・矛盾検出・エンジンルーティングは本スキル・03の担当のまま。14は入力生成のみ担当）。

### 8.1 ハイライト取込（案B・一括）

1. `intel/inbox/` に `kind: kindle-highlights` のfrontmatterを持つファイル
   （`kindle-<book-slug>.md`）があれば処理対象とする。
2. 生成手段: Kindle端末の `My Clippings.txt` を
   `python3 scripts/parse_kindle_clippings.py <path> --out intel/inbox/` で変換する
   （書籍ごとに1ファイル生成）。または read.amazon.co.jp/notebook からの手動貼り付け
   （`source: notebook`）でも同フォーマットなら受け付ける。
3. 本文の `[位置No.…]` 行をトピックでクラスタリングし、1冊あたり最大20件の book-note
   レコード（`type: book-note`, `kindle_location`=位置No., `question: null`,
   `source_engine: manual`, `source_urls: []` 可、`book_title`/`book_author` はfrontmatter
   由来）を `intel/books/<YYYY-MM>/` に作る。超過分は重要度降順で20件に絞り、残りを
   1件の「その他ハイライト」レコード（本文「## 引用（逐語）」に列挙）にまとめる。
4. 原則として使えるハイライトは principle にも昇格し `related` で連携する。
5. `python scripts/validate_intel.py` exit 0 → 処理済みinboxファイルを
   `intel/inbox/done/` へ移動 → コミット。

### 8.2 読書中疑問（案A・即時）

1. `intel/inbox/kindle-questions.md`（`kind: kindle-questions`）の各行
   （`[書名] 疑問文` または書名プレフィックス無し）を1クエリとして扱う。
2. エンジン選択は §1.2 のルーティング表に従う: 事実性の疑問（用語定義・事実確認）→
   `engine: notebooklm`、実践知・評判・比較 → `engine: hermes-web`。緊急即答が要る場合は
   「Kindle: <書名> <疑問文>」の単発依頼としてその場でも同じルーティングで実行できる。
3. 結果から book-note レコード（`question`=疑問原文、`book_title`=書名またはnull、
   `kindle_location: null`）を `intel/books/<YYYY-MM>/` に作る。
4. 処理済み行を含むファイルは削除せず、ファイルごと `intel/inbox/done/` へ移動する
   （空の `kindle-questions.md` は運用ファイルとして残すため、処理後に空の新規ファイルを
   同名で再作成する）。

### 8.3 要約対象の制限（ネガティブ確認）

DRM保護されたKindle本文の取得・全文要約は行わない。要約対象は常に**ユーザー自身が
作成したハイライト/メモ**に限る。「この本を丸ごと要約して」のような依頼には、
本文取得を試みず「要約対象はユーザーのハイライト/メモに限る」と応答して断る
（`docs/designs/14-app-kindle-summarizer.md` §8 シナリオ2 準拠）。
