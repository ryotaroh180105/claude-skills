# Kindle AI リサーチ・要約ツール（intel-hub Phase 3 コネクタ）設計書

| 項目 | 値 |
|---|---|
| ステータス | 設計完了 |
| 種別 | スクリプト + スキル拡張（intel-hub Phase 3 の詳細仕様） |
| 優先度 | Tier F-6 |
| 実装モデル | Sonnet 5（推奨 effort: high） |
| 依存する設計書 | docs/designs/00-fable-sonnet-bridge.md（実装プロセス）、docs/designs/03-intel-hub.md（book-note スキーマ §5.4・Kindle 正式案 §6.6・inbox §5.8・エンジンルーティング §6.1 の正）、docs/designs/04-repo-reorganization.md §5.1（アプリは別リポジトリ規約） |
| 依存する既存スキル | plugins/intel-hub（book-note レコードの保存・検索・レコード化の実行体）、plugins/hermes-x-search（リレー手順の正）、plugins/biz-ops-guard（本書 §1.2 の Go/No-Go の根拠） |
| 外部依存 | hermes-relay ブランチ + ローカル watcher（intel-hub と共有、稼働中）。Kindle 端末（My Clippings.txt 取得元）または read.amazon.co.jp/notebook（ハイライトコピー元）。API キー追加なし |

## 1. 目的・背景（Why）

### 1.1 課題と再設計

元要求は「Kindle に AI を差し込める VPN（読書中に調べたいことをすぐ調べたい・あわよくば本を要約させたい）」。
このうち **「VPN」は実現手段として成立しない** — VPN は通信経路の暗号化・迂回であって、Kindle
アプリ（クローズドな DRM 保護アプリ）の UI に AI 出力を注入する能力を一切持たない。閲覧画面の
自動読取・常駐 OCR も Amazon 利用規約・DRM 回避規制（著作権法 技術的保護手段回避）に抵触する脆い構成にしかならない（→ §8 シナリオ2）。

そこで元要求を2つの実現可能な課題に分離して再設計する:

- **課題A「読書中に調べたい」** = 読書中に湧いた疑問を、Kindle アプリの外（別デバイス/別ウィンドウ）で
  即座に調べ、答えを蓄積したい。現実解は **アプリ注入ではなく「疑問の低摩擦キャプチャ + リレー調査」**。
- **課題B「本を要約させたい」** = 本の DRM 本文ではなく、**ユーザー自身が作成したハイライト/メモ**
  （My Clippings.txt / read.amazon 通知帳）を起点に AI 要約したい。現実解は **ハイライトエクスポートの取込 + クラスタリング要約**。

本書はこの2課題の実現手段を、**intel-hub（設計03）の book-note レコードへの入力側コネクタ**として詳細化する。
intel-hub §6.6 は正式案A（疑問即調査）/B（ハイライト一括取込）を既に方針として持つが、
**入力の受け口（My Clippings.txt のパース・疑問キャプチャ導線・Kindle 専用 inbox フォーマット）は未確定**であり、
本書がその確定仕様を与える。

### 1.2 パッケージング判断（3択の推奨を1つに絞る）

| 候補 | 評価 | 採否 |
|---|---|---|
| 別リポジトリのアプリ/ブラウザ拡張 | Cloud Reader 拡張は DOM 変更で頻繁に壊れ（保守予算超過）、Amazon ToS の自動操作・改変禁止に抵触。04 §5.1-E なら別リポジトリだが、そもそも作らない | 却下 |
| 独立スキル（新規 plugins/kindle-*） | book-note のスキーマ・保存・検索・リレールーティングを intel-hub と二重実装。棚卸し原則（CLAUDE.md 常時適用ルール5）に反する重複 | 却下 |
| **intel-hub Phase 3 コネクタとして吸収** | book-note の器（§5.4）・検索・リレーは intel-hub に既存。本書は Kindle 固有の**入力層のみ**（パーサ1本 + SKILL.md 追記）を足す。追加インフラゼロ・重複ゼロ | **推奨** |

**推奨: intel-hub Phase 3 に吸収**。新規アプリ・拡張・独立スキルは作らない。

### 1.3 役割境界（棚卸し・CLAUDE.md ルール5）

intel-hub と本コネクタの責務が重なるため境界を明記する:

- **intel-hub の担当**: book-note レコードのスキーマ（03 §5.4）・保存・Grep 検索・矛盾検出・
  リレーのエンジンルーティング（03 §6.1）・レコード化（クラスタリングして book-note を書く工程）。
- **本コネクタ（14）の担当**: Kindle 固有の**入力生成のみ** — ①My Clippings.txt → Kindle 専用 inbox
  ファイルへの機械変換（`scripts/parse_kindle_clippings.py`）、②読書中の疑問を貯める quick-capture 導線、
  ③Kindle 専用 inbox フォーマット（§5.2）の定義。本コネクタは book-note スキーマを**再定義しない**（03 §5.4 を再利用）。

### 1.4 biz-ops-guard Go/No-Go ラダー（記入）

使う主体は主に Ryo 本人だが、My Clippings.txt パーサは Kindle 利用者に共有可能な OSS ユーティリティになりうるため、
biz-ops ラダーを通す（G3=学習・実績目的として割り切る項目は明示する）。

1. **想定ユーザーを固有名詞で3人**: ①Ryo（Kindle で技術書/ビジネス書を読み、疑問を調べ蓄積したい本人）
   ②同じ claude-skills を使う開発者（intel-hub 利用者で Kindle ヘビーユーザー）③Kindle でハイライトを
   大量に取るが読後に見返さない知識労働者（My Clippings.txt パーサ単体の潜在ユーザー）。→ **Yes**
2. **代替からの乗り換え理由（1文）**: 「My Clippings.txt を手で読み返す・ChatGPT に本文を貼る（DRM で不可）・
   Readwise 課金、の代わりに、自分のハイライトを追加課金ゼロで AI 要約し検索可能な intel DB に蓄積できる」。→ **Yes**
3. **導入〜初回価値 5分・3ステップ以内**: ①Kindle を USB 接続し My Clippings.txt をコピー
   ②`python3 scripts/parse_kindle_clippings.py <path>` 実行 ③「intel で <書名> を book-note 化して」と依頼。→ **Yes（3ステップ）**
4. **保守予算（週N分）**: 週30分。壊れる要因は My Clippings.txt のフォーマット差異（言語・端末世代）のみ。→ **Yes**
5. **最初の10ユーザーへの経路**: intel-hub 利用者（=自分と claude-skills 導入者）。外部配布は行わない。→ **Yes（内部のみ。外部 GTM は「学習目的として意図的に無視」）**

**ビジネス運用面シート（要約）**:
- 一文価値提案: Kindle ユーザーが Readwise 課金や手作業の読み返しをせずに、自分のハイライトを AI 要約して検索可能に蓄積できる。
- 導入: 手順3 / 所要5分 / 前提=Kindle 端末 or read.amazon アカウント、intel-hub 導入済み。
- 保守: 予算 週30分 / 壊れる要因=My Clippings.txt フォーマット差 / 廃止基準=2ヶ月 book-note 追加ゼロ。
- 運用: 定常作業=なし（都度実行） / 失敗通知経路=パーサの非ゼロ exit + intel-hub のタイムアウト報告 / 1利用あたりコスト=リレー1〜数往復（既存枠内、追加課金なし）。
- 収益/回収: 無料。回収は G3（学習・実績）+ 自分の読書ROI向上。
- 意図的に無視すること: 外部配布・GTM（内部利用のみ）／Readwise 同等の同期自動化（手動実行で足りる）／OCR・拡張（§8 で却下）。
- 悪魔の代弁者: §8 の失敗シナリオ3件で代替。

使う人が Ryo 本人のみに固定するなら biz-ops は yagni-guard のみでよいが、上記のとおり全項目 Yes で成立するため設計を止める No 項目はない。

## 2. スコープ

### 2.1 やること

- **課題B（要約）の入力層**: `scripts/parse_kindle_clippings.py` — My Clippings.txt を Kindle 専用 inbox
  ファイル（§5.2）へ機械変換。書籍ごとに1ファイル、ハイライト/メモを位置No.付きで抽出。
- **Kindle 専用 inbox フォーマット（§5.2）の定義**（intel-hub §5.8 は URL リスト用。ハイライトは非URLのため新 kind を定義）。
- **課題A（読書中調査）の現実フロー定義（§6.1）**: 疑問の quick-capture 導線（`intel/inbox/kindle-questions.md`）と、
  別デバイス/別ウィンドウでの即時調査手順。実行体は intel-hub の正式案A（03 §6.6）+ hermes-relay。
- **intel-hub SKILL.md への追記仕様（§5.3）**: Kindle 専用 inbox（highlights / questions 両 kind）を検出して
  book-note レコード化する処理を、intel-hub の ingest フローに接続する記述。
- **エッジケース・法的/規約リスクの明文化（§7・§8）**。

### 2.2 やらないこと（明示的スコープ外）

- **Kindle 閲覧画面の自動読取・常駐 OCR・「Kindle VPN」**（元要求の直訳）— 実現不能かつ ToS/DRM 抵触。§8 シナリオ2。
- **スクショ OCR パイプライン**（候補②）— DRM 画面のOCRは規約・DRM回避リスク、かつ画像処理依存が保守を圧迫。MVP から除外（§8 シナリオ2）。理由: 法的リスク + 保守コスト。
- **Kindle Cloud Reader ブラウザ拡張**（候補③）— DOM 破損で頻繁に壊れ、Amazon ToS の自動操作禁止に抵触。理由: 保守コスト + 規約リスク（§1.2 で却下済み）。
- **別リポジトリのアプリ化・拡張機能ストア公開** — 04 §5.1-E の対象になるが、本設計は intel-hub 吸収を選ぶため作らない。理由: 棚卸し（重複回避）。
- **book-note レコードのスキーマ定義・検索・矛盾検出・リレールーティングの再実装** — intel-hub（03）の担当。本書は入力層のみ。理由: 役割境界（§1.3）。
- **Readwise / Notion 等への同期** — YAGNI。手動実行 + intel DB 蓄積で足りる。3回以上「他ツールにも出したい」要望が出たら再検討。
- **DRM 本文の全文取得・要約** — 不可能かつ違法。要約対象はユーザー自身のハイライト/メモに限る（§7・§8）。
- **My Clippings.txt の言語自動判定を超えた多言語対応** — 日本語/英語の Kindle 標準フォーマットのみ対応。他言語で崩れたら §7 のフォールバック。理由: YAGNI。
- **intel-hub 本体（Phase 1/2）の改修** — 既存を前提に接続するのみ。SKILL.md への追記（§5.3）は Phase 3 の一部として行う。

## 3. 完成条件（Definition of Done）

- [ ] `scripts/parse_kindle_clippings.py` が存在し、`python3 scripts/parse_kindle_clippings.py --help` が exit 0 で使い方を出力する
- [ ] 【正常系】§10 のサンプル My Clippings.txt（2冊・ハイライト3件・メモ1件）を入力に
      `python3 scripts/parse_kindle_clippings.py <sample> --out <tmpdir>` を実行すると exit 0 で終わり、
      標準出力に `OK 2 books 4 clippings` を含み、`<tmpdir>` に `kindle-<slug>.md` が2ファイル生成され、各ファイルが §5.2 の frontmatter と `[位置No.…]` 行を持つ
- [ ] 【空入力】ハイライト0件（区切り `==========` のみ、または空ファイル）を入力すると exit 1 で終わり、標準エラーに `no clippings parsed` を含む
- [ ] 【不正入力】UTF-8 でないバイト列を含むファイルを入力すると exit 1 で終わり、標準エラーに文字コードエラーの旨（`encoding` を含む文字列）を出す
- [ ] `plugins/intel-hub/skills/intel-hub/SKILL.md` に「Kindle コネクタ」節（§5.3 の3点: highlights inbox 処理・questions inbox 処理・parse スクリプト呼び出し手順）が追記され、`python scripts/validate_skills.py` が exit 0
- [ ] 【ウォークスルーH（ハイライト取込）】`<tmpdir>` の `kindle-<slug>.md`（highlights kind）1ファイルを `intel/inbox/` に置いて「inbox の Kindle ハイライトを book-note 化して」と依頼すると、intel-hub の手順だけで `intel/books/<YYYY-MM>/` に book-note レコードが作られ（`kindle_location` 入り・`question: null`）、`python scripts/validate_intel.py` が exit 0、処理済み inbox は `intel/inbox/done/` へ移動する
- [ ] 【ウォークスルーI（読書中疑問）】`intel/inbox/kindle-questions.md`（§5.2 questions kind）に疑問2行を置いて「Kindle の疑問を調べて book-note 化して」と依頼すると、疑問ごとに intel-hub のエンジンルーティング（03 §6.1）でリレークエリが enqueue され、結果到着後に book-note レコード（`question` 入り）が作られる
- [ ] 【ネガティブ確認】DRM 本文の全文要約を求める依頼（「この本全部を要約して」）に対し、intel-hub/本コネクタが本文取得を試みず「要約対象はユーザーのハイライト/メモに限る」と応答する記述が SKILL.md にある
- [ ] docs/designs/03-intel-hub.md §6.6 の「入力の受け口は本書14が正」への相互参照が、本書14の §1.1 と intel-hub 側の該当箇所双方に存在する（intel-hub 側追記は本コネクタ実装時に行う）

## 4. 成果物の構成（ファイルレイアウト）

実装時に作成・変更するファイル（全て main ブランチ・claude-skills リポジトリ内。別リポジトリは作らない）:

```
scripts/parse_kindle_clippings.py                       # 【新規】My Clippings.txt → Kindle inbox 変換
plugins/intel-hub/skills/intel-hub/SKILL.md             # 【変更】「Kindle コネクタ」節を追記（§5.3）
plugins/intel-hub/.claude-plugin/plugin.json            # 【変更】version を1段上げる
intel/inbox/kindle-questions.md                         # 【新規・運用ファイル】読書中疑問の quick-capture（初期は空 + 記入例1行コメント）
intel/inbox/kindle-<book-slug>.md                       # 【生成物】parser 出力（highlights kind）。コミット対象外の運用ファイル
docs/designs/14-app-kindle-summarizer.md                # 本書
```

book-note レコードの実体（`intel/books/<YYYY-MM>/<id>.md`）は intel-hub の器をそのまま使う（新規ディレクトリを作らない）。
`scripts/` 直下への新規スクリプト追加は 04 §5.5 の ROOT_ALLOWLIST 内（`scripts` は許可済み）で規約適合。

## 5. データ構造

### 5.1 My Clippings.txt の入力フォーマット（Kindle 標準・パーサが解釈する対象）

Kindle 端末が `documents/My Clippings.txt` に追記する標準形式。1エントリは以下の4行構造 + 区切り:

```
<書名> (<著者>)
- <種別> on <位置/ページ情報> | Added on <日時>
<空行>
<ハイライト本文 または メモ本文>
==========
```

- 種別（英語 UI）: `Your Highlight`（ハイライト）/ `Your Note`（メモ）/ `Your Bookmark`（ブックマーク=本文なし）。
- 種別（日本語 UI）: `ハイライト` / `メモ` / `ブックマーク`。
- 位置情報: 英語 `Location 1234-1236` / 日本語 `位置No. 1234-1236` / ページ `page 45`。パーサは数値部分を抽出。
- 区切り線は `==========`（イコール10個）固定。
- 著者は括弧内。括弧がなければ著者 null。

### 5.2 Kindle 専用 inbox フォーマット（本書が定義。intel-hub §5.8 の URL 形式とは別 kind）

**highlights kind**（parser の出力。1冊=1ファイル、ファイル名 `kindle-<book-slug>.md`）:

```markdown
---
kind: kindle-highlights
book_title: "リーダブルコード"
book_author: "Dustin Boswell"          # 不明なら null
source: my-clippings                    # my-clippings | notebook（手動コピー時）
clip_count: 12
---
[位置No.1234-1236] ハイライト本文の逐語テキスト
[位置No.1250] > メモ本文（`Your Note` は先頭に `> ` を付ける）
[位置No.1301] 次のハイライト逐語テキスト
```

- `book-slug`: 書名を小文字 ASCII 化・非 ASCII はローマ字化不要でハイフン、40文字以内、衝突時は末尾に `-2`。ASCII 化不能な日本語書名は先頭16文字を URL エンコードせず `kindle-<連番>` にフォールバック（§7）。
- 位置No. は §5.1 から抽出した数値（範囲はハイフン保持）。ページ形式は `[page 45]` とする。ブックマーク（本文なし）行は出力しない。

**questions kind**（読書中疑問の quick-capture。ユーザーが手で追記）:

```markdown
---
kind: kindle-questions
---
[リーダブルコード] 変数名の長さと可読性のトレードオフの一般原則は？
[サピエンス全史] 農業革命が「罠」と呼ばれる根拠の一次資料は？
```

- 1行1疑問。`[書名]` プレフィックスは任意（無ければ book_title null で book-note 化）。
- intel-hub が1行=1クエリとして処理し、処理済み行は削除せずファイルごと `intel/inbox/done/` へ移動（intel-hub の inbox 規約に従う）。

### 5.3 intel-hub SKILL.md に追記する「Kindle コネクタ」節（確定・3点）

```markdown
## Kindle コネクタ（Phase 3 / 設計14）

1. **ハイライト取込**: `intel/inbox/` に `kind: kindle-highlights` のファイルがあれば、
   本文の `[位置No.…]` 行をトピックでクラスタリングし、1冊あたり最大20件の book-note レコード
   （type: book-note, kindle_location=位置No., question: null, source_engine: manual,
   source_urls: [] 可, book_title/book_author=frontmatter 由来）を intel/books/<YYYY-MM>/ に作る。
   超過分は最重要順に絞り、残りを1レコード「その他ハイライト」にまとめる（03 §6.6 案B）。
   My Clippings.txt からの生成は `python3 scripts/parse_kindle_clippings.py <path> --out intel/inbox/`。
2. **読書中疑問**: `kind: kindle-questions` の各行を1クエリとして 03 §6.1 のエンジンルーティングで
   enqueue（事実性→notebooklm、実践知・評判→hermes-web）。結果を book-note（question=疑問原文）に。
3. **要約対象の制限**: DRM 本文の取得・全文要約はしない。要約対象はユーザー自身のハイライト/メモに限る。
   「本を丸ごと要約して」には本ルールを提示して断る。
```

### 5.4 book-note レコード（再利用・intel-hub 03 §5.4 が正）

本コネクタは新スキーマを定義しない。生成される book-note は 03 §5.1 共通 + §5.4 追加フィールド
（`book_title` / `book_author` / `kindle_location` / `question`）に完全準拠する。
`source_engine`: ハイライト取込=`manual`、疑問調査=`notebooklm` または `hermes-web`。

## 6. 処理フロー

### 6.1 課題A（読書中に調べたい）— 現実フロー

1. **キャプチャ（読書中・アプリ外）**: 疑問が湧いたら Kindle アプリを離れず、別デバイス/別ウィンドウで
   `intel/inbox/kindle-questions.md` に `[書名] 疑問文` を1行追記する（数秒）。緊急で今すぐ答えが要る場合は
   別デバイスの Claude セッションで直接 `Kindle: <書名> <疑問文>`（intel-hub 03 §6.6 案A）を実行。
2. **バッチ調査（読後 or 休憩時）**: 「Kindle の疑問を調べて book-note 化して」と依頼 → intel-hub が
   各行を 03 §6.1 のルーティングで enqueue → 結果を book-note（question 入り）化。
3. **出力**: `intel/books/<YYYY-MM>/` に book-note レコード。questions inbox は `done/` へ移動。

**アプリ注入（VPN）を使わない理由**: Kindle アプリは注入不能。疑問の低摩擦キャプチャ + 非同期リレー調査で
「すぐ調べたい」を実質満たす（即答が要る少数ケースのみ別デバイス即時実行）。

### 6.2 課題B（本を要約させたい）— 現実フロー

**入力経路1（E-ink 端末・My Clippings.txt）**:
1. Kindle 端末を USB 接続し `documents/My Clippings.txt` を取得。
2. `python3 scripts/parse_kindle_clippings.py <path> --out intel/inbox/` → 書籍ごとに `kindle-<slug>.md`（highlights kind）生成。
3. 「inbox の Kindle ハイライトを book-note 化して」→ intel-hub がクラスタリングして book-note 化（03 §6.6 案B）。

**入力経路2（アプリ/Cloud・notebook コピー）**:
1. read.amazon.co.jp/notebook で対象書のハイライトを表示しコピー。
2. `intel/inbox/kindle-<slug>.md` を手作成し `kind: kindle-highlights` / `source: notebook` で貼り付け（位置No. は取れる範囲で）。
3. 経路1と同じ book-note 化依頼。

**出力**: book-note レコード群（1冊最大20件）+ 原則として使えるものは intel-hub が principle へ昇格（related 連携。03 §6.6）。

### 6.3 parse_kindle_clippings.py の内部処理

1. **入力**: My Clippings.txt パス（引数1）、`--out <dir>`（出力先、既定 `intel/inbox/`）。
2. **読込**: UTF-8（BOM 許容）で読む。デコード失敗 → stderr に `encoding error: ...` を出し exit 1。
3. **分割**: `==========` でエントリ分割。各エントリを §5.1 の4行構造でパース（種別・位置・本文を抽出）。
4. **グルーピング**: 書名でグルーピング。書名ごとに §5.2 highlights kind のファイルを生成（既存同名は上書き）。
5. **メモ/ブックマーク処理**: `Your Note`/`メモ` は本文に `> ` プレフィックス。`Your Bookmark`/`ブックマーク`（本文なし）はスキップ（clip_count に数えない）。
6. **出力**: 生成ファイル数と総クリップ数を `OK <B> books <C> clippings` で stdout に出す。クリップ0件なら stderr `no clippings parsed` + exit 1。

## 7. エッジケース

| ケース | 期待挙動 |
|---|---|
| My Clippings.txt が空 / 区切りのみ / クリップ0件 | book-note 化しない。stderr `no clippings parsed`、exit 1 |
| UTF-8 でないファイル（Shift-JIS 等） | 変換せず stderr に `encoding error`、exit 1。ユーザーに UTF-8 保存を案内（CLAUDE.md 説明義務形式） |
| 書名が日本語で ASCII slug 化不能 | ファイル名を `kindle-<3桁連番>.md` にフォールバックし、frontmatter の book_title に原文書名を保持。stdout に採番マッピングを1行報告 |
| 同名書籍が複数版で slug 衝突 | slug 末尾に `-2`, `-3` を付与 |
| `Your Note`（メモ）が直前ハイライトに紐づく | 独立行として `> ` 付きで出力（紐づけ推定はしない。YAGNI） |
| ブックマーク（本文なし）エントリ | 出力に含めない（要約価値なし） |
| ハイライトが数千件で巨大 | パーサはそのまま全出力（軽量テキスト処理）。book-note 化時に intel-hub が1冊20件上限で絞る（03 §6.6） |
| DRM 本文全文の要約を要求された | 拒否。「要約対象はユーザー自身のハイライト/メモに限る」と応答（§5.3-3・§8 シナリオ2） |
| 出版社のハイライト上限で notebook のコピーが途中で切れる | 取れた範囲で book-note 化し、レコードの「未確認・断定できない点」に「ハイライト上限で一部欠落」と明記 |
| questions inbox の行に `[書名]` が無い | book_title null で book-note 化（03 §5.4 は null 許容） |
| 位置情報が `page` 形式のみ（固定レイアウト本） | `[page 45]` として出力し、kindle_location に `page 45` を格納 |
| リレー結果が status: error / タイムアウト | intel-hub のエッジケース（03 §7）に委譲。本コネクタは追加処理しない |

## 8. 失敗シナリオとレッドチーム所見

計画ゲート要約: (1) 失敗は下表3件。(2) やらない境界=§2.2（特に OCR・拡張・VPN・本文全文要約・独立スキル化を明示禁止）。
(3) 完成条件は全て実行観察形式（§3）。(4) 実装者が最初に詰まるのは「My Clippings.txt の言語別フォーマット差」→ §5.1 に英/日両 UI の種別・位置表記を明記。(5) 必要性=intel-hub §6.6 が入力受け口を持たず、本書が唯一その確定仕様を与える（既存で代替不可）。

| # | 失敗シナリオ | 早期警報サイン | 設計上の対策 |
|---|---|---|---|
| 1 | 「読書中にすぐ調べたい」への即時性が満たされず、VPN 幻想への不満が残る | 「結局アプリ内で調べられない」という不満、questions inbox がほぼ空のまま | 期待値を §1.1・§6.1 で明示宣言（アプリ注入は不能。低摩擦キャプチャ+非同期調査で代替、即答要件は別デバイス即時実行）。キャプチャを「1行追記・数秒」に最小化して摩擦を下げる |
| 2 | 「便利だから」と OCR / ブラウザ拡張 / 本文取得を後から実装し、Amazon ToS・DRM 回避規制（著作権法/DMCA §1201）に抵触。アカウント停止・法的リスク | OCR・スクレイパー・拡張・本文取得のタスクや依存（画像処理・DOM 注入ライブラリ）が生える | §2.2 で OCR・拡張・VPN・DRM 本文取得を明示禁止。§5.3-3 と §3 のネガティブ確認で「要約対象はユーザーのハイライト/メモに限る」を SKILL.md に固定。要約入力は**ユーザーが正規機能で作成したハイライト**のみ（自作データなので私的複製の範囲、再配布しない） |
| 3 | ハイライト取込が面倒で book-note が育たず、intel-hub 同様3週間で更新が止まる | `git log --since='21 days ago' -- intel/books/` が0コミット / questions・highlights inbox が空のまま | 入力を1コマンド（parser）+ inbox 1ファイル置くだけに圧縮。My Clippings.txt（USB でまとめて取れる）を主経路にしてバッチ性を確保。null 許容で「取れた分だけ」動かす（intel-hub 03 シナリオ1 と同じ設計思想を継承） |

法的補足（レッドチーム・攻撃者/経営視点）: My Clippings.txt はユーザー端末上のユーザー自身のハイライト平文であり、
これをローカルでパース・要約するのは私的利用の範囲。**本文の全文再構成・第三者への再配布・DRM 回避は本設計の全経路で行わない**
（そこを踏み越えるのが唯一の危険線で、§2.2・§5.3-3 で封じている）。

## 9. 実装手順（Sonnet 向けタスク分割）

intel-hub Phase 1（実装済み）を前提とする。Phase 3 の一部として実装。各タスク=1コミット目安。

1. **parse_kindle_clippings.py 実装** — §5.1 パース・§5.2 出力・§6.3 内部処理。argparse で `--help`・`--out`。
   完了条件: §3 の正常系（`OK 2 books 4 clippings`）・空入力 exit 1・非 UTF-8 exit 1 の3テストが通る。
2. **intel-hub SKILL.md に「Kindle コネクタ」節を追記** — §5.3 の3点をそのまま収録。plugin.json version を1段上げる。
   完了条件: `python scripts/validate_skills.py` exit 0。
3. **Kindle 専用 inbox 運用ファイル作成** — `intel/inbox/kindle-questions.md`（空 + 記入例コメント1行、§5.2 questions kind）。
   完了条件: ファイル存在 + `python scripts/validate_intel.py` が exit 0（inbox は検証対象外だが既存レコードを壊さないこと）。
4. **ウォークスルーH/I + ネガティブ確認 + 相互参照追記** — §3 の該当項目 + intel-hub §6.6 への「入力受け口は設計14が正」相互参照。
   完了条件: §3 全項目にチェック。

## 10. テスト計画

- **parser 単体（実行観察）**: サンプル My Clippings.txt を一時作成して実行し出力を観察（コード読みで済ませない）。
  サンプル内容 = 2冊 / `Your Highlight` 2件 + `ハイライト`（日本語UI）1件 + `Your Note` 1件 + `Your Bookmark` 1件（本文なし・出力除外）。
  期待: `OK 2 books 4 clippings`（ブックマーク除外で4）、2ファイル生成、日本語UI行も位置No.抽出成功。
- **異常系**: 空ファイル → exit 1 `no clippings parsed`。Shift-JIS バイト列 → exit 1 `encoding error`。
- **ウォークスルーH（ハイライト取込）**: §3 のとおり book-note 生成 + validate_intel.py exit 0 + inbox done 移動を観察。
- **ウォークスルーI（疑問調査）**: §3 のとおりリレー enqueue → book-note（question 入り）生成を観察（リレー実往復1回）。
- **ネガティブ確認**: ①「本を全部要約して」で本文取得を試みず拒否応答する（§5.3-3） ②DB 蓄積指示のない「Kindle の本について教えて」で勝手に intel/ へ書かない ③intel-hub の通常検索・twitter-intel の依頼を横取りしない。
- **非退行**: 追記後も intel-hub の既存ウォークスルーA/B（03 §3）が通る（SKILL.md 追記が既存フローを壊さない）。

## 11. 実装時判断ルール

- **My Clippings.txt の言語 UI 判定**: 種別文字列（`Your Highlight`/`ハイライト` 等）で判定。両方に一致しない未知言語の行は、
  本文はそのまま出力しつつ種別を `highlight` 既定に倒す（メモ判定は日英キーワードのみ）。多言語の頑健パースは追わない（YAGNI・§2.2）。
- **位置 vs ページ**: 両方あれば位置No.優先。位置が無くページのみなら `[page N]`。どちらも無ければ `[位置No.不明]` とし本文は残す。
- **book-slug が日本語で ASCII 化不能**: §7 のとおり `kindle-<連番>` にフォールバック。ローマ字変換ライブラリは導入しない（依存追加禁止・YAGNI）。
- **既存同名 inbox ファイルの上書き**: parser は上書き（冪等）。ただし `kind: kindle-questions`（手書き）は parser の出力対象外なので上書きしない。
- **book-note 化のクラスタリング粒度・上限**: intel-hub 03 §6.6（1冊最大20件）に委譲。本コネクタは判断しない。
- **エンジンルーティング**: 疑問調査は intel-hub 03 §6.1 の表に従う。本書でエンジン名をハードコードしない（hermes-web 未稼働時は notebooklm 読替、03 §11 と同じ）。
- **コミット/push**: パーサ・SKILL.md 追記はコミットまで。生成された inbox ファイル・book-note レコードのコミットは intel-hub 運用に従い、push はユーザー指示時のみ。リレー enqueue の hermes-relay ブランチ push は従来どおり許可。
- **アプリ化の誘惑**: 「拡張やアプリにしたい」と要望されても本コミットに混ぜない。別リポジトリ化は 04 §5.1-E に従い別タスク・ユーザー判断（§12）。

## 12. 未解決事項（ユーザー確認待ち）

- **My Clippings.txt の実物フォーマット**: ユーザーの Kindle 端末世代・UI 言語で §5.1 の想定と差異がないか、実ファイル1本で検証したい（言語別の種別・位置表記の揺れ確認）。実装前にサンプル1本の提供を依頼。
- **主経路の選択**: E-ink 端末（My Clippings.txt / 経路1）を主に使うか、アプリ/Cloud（notebook コピー / 経路2）が主か。ユーザーの読書環境で MVP のテスト対象を1つに絞る。
- **即答要件の頻度**: 課題A で「別デバイス即時実行」が要る割合。高いなら quick-capture より即時フローを主にする（現状は非同期バッチを主に設計）。
- **将来のアプリ化判断**: intel-hub 吸収で不足を感じた場合のみ、04 §5.1-E に従い別リポジトリの拡張/アプリ化を再検討（現時点は作らない）。
- **本設計書の連番**: 既存は 10 まで。本書は指示どおり 14 を採番したが、11〜13 が欠番。詰めるか否かはユーザー判断（リンク参照が生じる前に確定推奨）。
