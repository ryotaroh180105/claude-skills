# KOMA TIMES 完全自動運用 設計書 v2（AskHub離脱・Composio全廃・無人運転）

| 項目 | 値 |
|---|---|
| ステータス | 設計完了（実装ブロッカーは §12 B-2/B-3 のみ） |
| 種別 | アプリ（別リポジトリ `ryotaroh180105/koma-times`）— 既存システムの引き継ぎ・完全自動化 |
| 優先度 | ユーザー指示により最優先アプリ |
| 実装モデル | Sonnet 5（推奨 effort: high） |
| 依存する設計書 | docs/designs/04-repo-reorganization.md §5.1 分類E（アプリは別リポジトリ） |
| 依存する既存スキル | なし（standalone。参照実装として plugins/sns-auto-posting/skills/sns-auto-posting/scripts/post_x.py の OAuth 1.0a 署名コードを流用する） |
| 外部依存 | ANTHROPIC_API_KEY（選定・台本・投稿文）、GEMINI_API_KEY（画像）、XAI_API_KEY（収集）、自前 X アプリの OAuth 1.0a キー4種（投稿）、Windows タスクスケジューラ |
| 改訂履歴 | v1: 2026-07-07 初版（学習データ.md 前提・Composio 残置）。v2: 2026-07-12 全面改訂 — 一次情報を ptc/ に差し替え、Composio 全廃、healthcheck/自己停止/スケジューラ自動登録を追加し「完全自動運用」を設計目標に格上げ |

## 0. 一次情報（この設計の正）

ユーザー提供 `twitter_news.zip`（2026-07-11 受領。実装時は koma-times リポジトリの `docs/handover/` に全量コピーして凍結参照する）:

| ファイル | 扱い |
|---|---|
| `ptc/main_pipeline.py` + `ptc/step0〜step5_*.py` | **② 生成の現行本体・移植元の正**。step1（4軸20点スコア: hook_power/shareability/story/social_literacy + 重複名寄せ + emotion_core、TOP_N=4）、step2（4コマ台本+画像プロンプト。SERIF_LIMITS・FIXED_STYLE・動物キャラ比喩禁止・字数超過リトライ1回）、step3（画像5枚生成・部分失敗許容）、step4（X 6ツイートスレッド・X_LIMIT=280 加重カウント・article_*.json + _DONE）。step0/step5 は Composio Drive 中継なので移植対象外（ローカルI/Oに置換） |
| `KOMA_TIMES_引き継ぎ資料.md` | 全体像・データ契約の参考。「🆕 最新アップデート（2026-06-09）」節が資料内の正 |
| `collect.py` | ① 収集の移植元（xAI Grok x_search+web_search、X発:報道発≒7:3、2ソース裏取り）。出口の Composio Drive 部のみ置換 |
| `post_worker.py` | ③ 投稿のオーケストレーション部（ロック・カテゴリ分散・進捗書き戻し・再開・退避）の移植元。Composio アダプタ部（`_composio*`/`sync_from_drive`/`upload_media`/`post_tweet`）は**廃止して x_adapter.py に差し替え** |
| `askhub_tools.py` | ローカル shim の土台。Gemini 画像生成部（`generate_or_edit_image`）は流用。`llm_call` は model/schema 引数が無く ptc の要求を満たさないため拡張する（§5.4） |
| `学習データ.md`・`system_prompt.py`（全3種）・`system_prompt_no_ptc.py` | 旧版・AskHub 駆動用。**全て廃止**（handover/ に凍結保存のみ） |

## 1. 目的・背景（Why）

KOMA TIMES = AIニュース4コマ漫画のXアカウント。ゴールは**人間の操作ゼロで 収集→選定→台本→画像→投稿 が回り続け、止まったら人間に通知が来る**こと。

旧構成の問題: ② 生成が AskHub チャット起動（=人間がセッションを開く必要）、プロセス間が Composio 経由 Google Drive 中継（AskHub とローカルの環境分断の産物）、失敗検知の仕組みゼロ（塩漬け化の根本原因）。

v2 の解決: 全工程をローカル Python + Windows タスクスケジューラに一本化し、Composio・AskHub・Drive 中継を全廃。healthcheck による死活監視と投稿失敗時の自己停止（凍結対策）を新設する。

### 1.1 工程分解と担当対応表（第一原理・全工程）

| 工程 | 担当 | 備考 |
|---|---|---|
| 1. 収集 | `collect.py`（自動・8hおき） | xAI 直叩き |
| 2. 選定 | `generate.py` step1 部（自動） | Anthropic API |
| 3. 台本・画像プロンプト | `generate.py` step2 部（自動） | Anthropic API |
| 4. 作画 | `generate.py` step3 部（自動） | Gemini |
| 5. 投稿文 | `generate.py` step4 部（自動） | Anthropic API |
| 6. 配信（X投稿） | `post_worker.py` + `x_adapter.py`（自動・周期は §12 B-2 のプラン次第） | X API 直叩き |
| 7. 健全性監視 | `healthcheck.py`（自動・日1回）+ 自己停止フラグ | v2 新設 |
| 8. 反応分析・企画還流 | **意図的に対象外**（理由: まず配信の無人化を完成させる。X API の metrics 取得はプラン依存であり、Phase 3 として再稼働後に別設計） | — |
| 9. Instagram 展開 | `insta_worker.py` 素材生成のみ（Phase 2・投稿は手動） | 自動投稿は対象外 |

### 1.2 ループ設計（loop-engineering 6要素）

- **Trigger**: Windows タスクスケジューラ4本（§6）。イベント連鎖なし（各タスク独立、時刻カップリングなし）
- **Doer**: collect / generate / post_worker の3スクリプト（1回実行して終了、常駐なし）
- **Verifier**: (a) generate 完了時に `validate_output.py` をサブプロセス実行しスキーマ検証 (b) post_worker は tweet_id 取得を成功条件とする (c) `healthcheck.py` が別主体として全タスクの status を照合
- **Stop Rules**: 成功条件=各実行の正常終了。安全上限=生成は inbox 供給律速（collect 3回/日 × TOP4 = 最大12記事/日で頭打ち）、投稿は 1起動1記事 + ツイート間8秒 + 認証系エラー連続3回で `status/POSTING_DISABLED` を作成し以後自己停止（解除は人間がファイル削除）
- **Memory/State**: `tmp/{inbox,output,posted}/`・`status/*.json`・`tmp/.last_category`（全てファイル永続化、git 管理外）
- **Skills/Routines**: なし（standalone リポジトリ。運用知識は `docs/OPERATIONS.md` に固定）
- 失敗モードチェック: Blind（Verifier 3系統あり）/ Tangled（3スクリプト疎結合維持）/ Amnesiac（状態は全てファイル）/ Manual（Trigger はスケジューラ登録スクリプトで実登録し `schtasks /query` で確認）いずれも該当なし

## 2. スコープ

### 2.1 やること

- 新リポジトリ `ryotaroh180105/koma-times`（private — §12 B-3）の組成（§4）
- ① `src/collect.py`: 移植 + 出口を `tmp/inbox/search_results.json` へのアトミック書き込みに変更（収集プロンプト不変更）。出口直前に各記事 URL の疎通検証（HEAD、タイムアウト5秒、HTTP 4xx/5xx・接続不能の記事は除外してログに記録 — red-team #3 採択・捏造URL対策）を追加
- ② `src/generate.py`: `ptc/step1〜step4` のロジックを一本化移植（プロンプト・スコア基準・SERIF_LIMITS・FIXED_STYLE・字数検証を一字も変えない）。入口=inbox ポーリング、出口=`tmp/output/`。Instagram 関連の生成は一切しない（Phase 2 の insta_worker が担当 — §5.2）。二重起動ロック・`--mock` つき
- `src/askhub_tools.py`: shim 拡張 — `llm_call` に model/schema 対応の Anthropic 経路を追加（§5.4）。Gemini 画像経路は流用
- ③ `src/post_worker.py`: オーケストレーション部を移植し、Composio アダプタを `src/x_adapter.py`（X API 直叩き・§5.5）に差し替え。`sync_from_drive` 系は削除
- `src/healthcheck.py` + status 記録の共通関数（§5.6）: 死活監視・ALERT 通知・自己停止フラグ検査
- `scripts/validate_output.py`: article JSON のスキーマ検証（§5.2）
- `scripts/register_tasks.ps1`: タスクスケジューラ4本の一括登録（§6）
- `docs/OPERATIONS.md`: ループ6要素・障害対応手順・鍵ローテ手順
- Phase 2: `src/insta_worker.py`（Pillow キャプション帯合成、ローカル保存のみ）

### 2.2 やらないこと（明示的スコープ外）

- AskHub / PTC / system_prompt 系の維持（廃止。handover/ 凍結のみ）
- **Composio の一切**（v1 から変更: X 投稿も Drive も使わない。理由: 自前 X アプリが必須である以上、中間 SaaS は障害点と鍵管理を増やすだけ。実投稿未検証なので「検証済み資産」でもない）
- Google Drive 中継・アップロード（v1 の④スマホ配信含め廃止。Instagram 素材はローカル `tmp/instagram/` のみ。Drive 配信が欲しくなったら再稼働後に別途）
- 反応分析・metrics 収集・企画還流（§1.1 工程8。Phase 3 として別設計）
- Instagram / TikTok の自動投稿（素材生成まで）
- 選定ロジック・台本プロンプト・画風の変更（移植のみ。改善は再稼働後）
- hermes-relay 経由の収集（collect.py は xAI 直叩きで完結）
- claude-skills リポジトリへのコード配置（分類E違反。本設計書のみ）
- 投稿前の人間承認ゲート（引き継ぎ資料 §11 の決定「完全全自動」を維持。安全弁は事前の除外条件・2ソース裏取り・事後の healthcheck と B-4 目視期間で担保）

## 3. 完成条件（Definition of Done）

Phase 0（組成・全モック疎通 — API キー不要で判定可能）:
- [ ] リポジトリに §4 のファイルが全て存在する
- [ ] `grep -rn "composio\|GOOGLEDRIVE\|FOLDER_ID\|sync_from_drive\|genesis1p" src/ scripts/` が 0 件
- [ ] `python src/collect.py --mock` が exit 0 で `tmp/inbox/search_results.json` を生成し、§5.1 スキーマに適合
- [ ] `python src/generate.py --mock` が exit 0 で `tmp/output/` に `article_*.json` 4件 + 画像ダミー5枚/記事 + `_DONE` を生成し、`python scripts/validate_output.py` が exit 0
- [ ] `python src/post_worker.py --mock` で: カテゴリ分散選定 → t1〜t6 の進捗書き戻し → `tmp/posted/` 退避が観察できる。t3 完了時点で kill → 再実行で t1〜t3 をスキップし t4 から再開（stdout ログで確認、二重投稿なし）
- [ ] `python src/post_worker.py --mock` を認証エラー模擬モードで3回実行すると `status/POSTING_DISABLED` が生成され、4回目は投稿処理に入らず exit 0（stdout に自己停止中の旨）
- [ ] `status/*.json` を25時間前の日時に細工して `python src/healthcheck.py` を実行すると `status/ALERT-<date>.txt` が生成され、Windows トースト通知コマンドが発行される（`--no-toast` でファイル生成のみ検証可）
- [ ] `python -m pytest tests/` が全通過（最低: llm_call schema モードのモック単体テスト、weighted_length の境界テスト、validate_output の正常/異常系）

Phase 1（実 API・無人運転開始 — ユーザーのキー投入後）:
- [ ] `python src/collect.py` 実行で実 xAI API から §5.1 スキーマの inbox が生成される
- [ ] `python src/generate.py` 実行で1記事以上が実画像付きで `tmp/output/` に出る
- [ ] `python src/post_worker.py` で X に6ツイートスレッドが1件実投稿される（スレッド URL を README の検証記録に記載）
- [ ] `scripts/register_tasks.ps1` 実行後、`schtasks /query /tn "koma\*"` で4タスクが登録済み
- [ ] 人間が何も操作しない状態で1サイクル（収集→生成→投稿）が完走し、新規スレッドが X に出る
- [ ] healthcheck が正常系で ALERT を出さない（1日運転後に status/ に ALERT が無い）

Phase 2（Instagram 素材・任意）:
- [ ] `python src/insta_worker.py` で1記事分のキャプション帯付き画像4枚（日本語が正しく描画）が `tmp/instagram/<article_id>/` に生成される

## 4. 成果物の構成（ファイルレイアウト — koma-times リポジトリ）

```
koma-times/
├── README.md                 # 概要・セットアップ・鍵取得手順（X/xAI/Anthropic/Gemini）・検証記録
├── .env.example              # §5.3 の全キー
├── .gitignore                # .env / tmp/ / status/ / __pycache__
├── requirements.txt          # anthropic, google-genai, openai(xAI用), jsonschema, python-dotenv, pytest, Pillow(Phase2)
├── docs/
│   ├── handover/             # twitter_news.zip 全量を凍結保存（改変禁止）
│   ├── CONTRACTS.md          # §5 データ契約の写し
│   └── OPERATIONS.md         # ループ6要素・スケジューラ・障害対応・鍵ローテ・POSTING_DISABLED解除手順
├── src/
│   ├── collect.py            # ① 収集
│   ├── generate.py           # ② 生成（ptc/step1-4 一本化）
│   ├── askhub_tools.py       # shim（llm_call 拡張 + Gemini 画像）
│   ├── x_adapter.py          # X API 直叩き（upload_media / post_tweet）
│   ├── post_worker.py        # ③ 投稿
│   ├── healthcheck.py        # ⑦ 死活監視
│   ├── status_util.py        # status/*.json 読み書きの共通関数（4スクリプトが使用）
│   └── insta_worker.py       # Phase 2
├── scripts/
│   ├── validate_output.py
│   └── register_tasks.ps1
├── tests/
│   ├── fixtures/search_results.sample.json   # 架空データ（実データ持ち込み禁止）
│   └── test_*.py
├── status/                   # 実行時生成（git管理外）: <task>.json / ALERT-*.txt / POSTING_DISABLED
└── tmp/                      # 実行時生成（git管理外）: inbox/ inbox/done/ output/ posted/ images/ instagram/
```

## 5. データ構造

### 5.1 入口 `tmp/inbox/search_results.json`（①→②）

引き継ぎ資料 §4.1 と同一: `[{"category": "<名>", "articles": [{"title","url","snippet"}]}]`。①はアトミック書き込み（`.tmp`→`os.replace`）。②は読込成功後 `tmp/inbox/done/search_results_<UTC時刻>.json` へ改名移動。

### 5.2 出口 `tmp/output/article_{RUN_ID}_{n}.json`（②→③）

**ptc/step4 の出力形式そのままが正**（red-team #1 採択: `instagram_carousel` は ptc/step4 の出力に存在しないため必須キーにしない。生成プロンプト不変則を優先）:
- 必須キー: `title` / `category` / `score` / `emotion_core` / `script` / `citations` / `x_thread`（t1〜t6。各 `{"text": str, "image": str|null}`。t1=combined、t2〜t5=panel1-4、t6=null）/ `image_status`（キー名・構造は handover/ の step4_compose.py 実物と照合して確定する。上記列挙と実物が食い違う場合は実物が正）
- Instagram 素材は Phase 2 の `insta_worker.py` が `script`（各コマのセリフ・解説）から導出する（②には手を入れない）
- `instagram_status` キーは出力しない（旧仕様の廃止）
- 画像ファイル名は ptc/step3 の確定命名 `article_{RUN_ID}_{n}_{combined|panel1..4}.png`。RUN_ID = `YYYYmmdd_HHMMSS`
- アトミック書き込み。全記事完了で `tmp/output/_DONE`
- ③が `_post_progress` を追記する仕様は不変

### 5.3 環境変数（.env）

```
ANTHROPIC_API_KEY=      # ② 選定・台本・投稿文
GEMINI_API_KEY=         # ② 画像生成
XAI_API_KEY=            # ① 収集
X_API_KEY=              # ③ 投稿（OAuth 1.0a Consumer Key）
X_API_SECRET=
X_ACCESS_TOKEN=
X_ACCESS_TOKEN_SECRET=
KOMA_LLM_MODEL=claude-sonnet-5     # 省略時この値
KOMA_XAI_MODEL=grok-4.3            # 省略時この値
KOMA_MAX_ARTICLES_PER_RUN=1        # ③ 1起動あたり投稿記事数
```

### 5.4 askhub_tools.llm_call 拡張仕様（実装者が最初に詰まる箇所への先回り）

```python
async def llm_call(prompt: str, model: str = "", schema: dict | None = None):
    # 1) model が "claude" で始まる、または schema が指定された場合 → Anthropic API
    #    - モデルIDは model 引数を使う。ただし ptc 由来コードの "claude-sonnet-4-6" は
    #      移植時に os.environ.get("KOMA_LLM_MODEL", "claude-sonnet-5") 参照へ置換する
    #      （プロンプト文字列は不変。変更してよいのはモデルIDの取得方法のみ）
    #    - schema あり: tools=[{name:"output", input_schema:schema}] + tool_choice 強制で
    #      dict を返す。返却 dict を jsonschema.validate で検証し、失敗時は1回だけ再試行、
    #      2回目も失敗なら例外（呼び出し側の既存エラー処理に乗せる）
    #    - schema なし: response の text を str で返す
    # 2) それ以外（model 空 or "gemini*"） → 既存 Gemini 経路（後方互換・変更しない）
```

`generate_or_edit_image(prompt)` は受領版のまま（Gemini `gemini-2.5-flash-image`、戻り値 `{"path": ...}`）。

### 5.5 x_adapter.py 仕様

post_worker が呼ぶ2関数のみ公開。OAuth 1.0a 署名は `plugins/sns-auto-posting/skills/sns-auto-posting/scripts/post_x.py` の `build_oauth_header` / `weighted_length` を写して使う（実績コード。claude-skills への依存は持たず、コードをコピーして冒頭に出典コメントを書く）:

- `upload_media(image_path: str) -> str`: `POST https://api.x.com/2/media/upload`（multipart/form-data、OAuth 1.0a。署名対象は oauth パラメータのみでボディは含めない）。戻り値 media_id（レスポンスの `data.id` / `media_id_string` の実キーは初回実投稿で確認 — §11-2）。v2 が 4xx を返す環境では `https://upload.twitter.com/1.1/media/upload.json` にフォールバック
- `post_tweet(text: str, media_ids: list[str] | None, reply_to: str | None) -> str`: `POST https://api.x.com/2/tweets`、payload は `{"text", "media": {"media_ids": [...]}, "reply": {"in_reply_to_tweet_id": ...}}`（該当キーのみ）。戻り値 tweet_id
- 例外規約（red-team #3 採択）: 401 と、403 のうちレスポンスボディに suspend / permission / access 系の文言を含むものは `XAuthError`（自己停止カウント対象）。403 の duplicate content（重複投稿）と 429 はそれぞれ `XDuplicateError` / `XRateLimitError`（カウント対象外・その回を打ち切るのみ）。他は `XPostError`

### 5.6 status/*.json と自己停止

各スクリプトは終了時に `status_util.record(task_name, ok: bool, error: str | None)` を呼び、`status/<task>.json` を更新:

```json
{"task": "post", "last_run": "<ISO8601+09:00>", "last_success": "<同>", "last_error": null, "consecutive_failures": 0, "meta": {}}
```

`meta` はタスク固有の成果カウント: collect は `{"article_count": <収集記事数>}`、generate は `{"emitted": <出力記事数>}`、post は `{"posted": <投稿記事数>}` を毎実行記録する。

- post_worker: `XAuthError` で `consecutive_failures` を加算し、**3 に達したら `status/POSTING_DISABLED` を作成**（中身: 日時と最終エラー）。起動時にこのファイルが存在すれば投稿処理に入らず正常終了。解除は人間がファイルを削除（手順は OPERATIONS.md）。`XRateLimitError` は失敗カウントに含めない（その回を打ち切るのみ）
- healthcheck（日1回）は次の4検査を行い、1つでも該当すれば `status/ALERT-<YYYYMMDD>.txt` に事象を書き、PowerShell 経由で Windows トースト通知を出す（WinRT ToastNotification。通知失敗してもファイルは残る）:
  1. プロセス死活: 各 status の `last_success` が閾値超過（collect: 16h / generate: 24h / post: 26h ※在庫ゼロ終了も success 扱い）
  2. 自己停止: `POSTING_DISABLED` の存在
  3. 成果物停滞（red-team #2 採択・プロセス緑のまま出力ゼロを検知）: `tmp/output/` に未投稿在庫が1件以上あるのに `tmp/posted/` の最新 mtime が26h超（投稿だけが空回りしている）
  4. 収集枯渇（同上）: collect の `meta.article_count` が直近2回連続で 0（status_util が直前値を `meta.prev_article_count` に保持して判定）

## 6. 処理フロー

タスクスケジューラ4本（`scripts/register_tasks.ps1` が `schtasks /create` で一括登録。時刻カップリングなし・各スクリプトは1回実行して終了）:

| タスク名 | 周期 | 動作 |
|---|---|---|
| koma-collect | 8hおき（06:00/14:00/22:00 JST） | xAI 収集 → inbox アトミック書き込み。既存 inbox が未処理でも上書きしない（inbox に search_results.json が存在すればスキップして正常終了） |
| koma-generate | 1hおき | inbox に search_results.json が**あれば**処理（選定→台本→画像→投稿文→output/ 出力→inbox を done/ へ）、**なければ即 exit 0**（ポーリング型・自己発見 Trigger） |
| koma-post | 2hおき | POSTING_DISABLED 検査 → output/ の未投稿を古い順+カテゴリ分散で `KOMA_MAX_ARTICLES_PER_RUN` 件投稿（ツイート間8秒・進捗書き戻し・全成功で posted/ 退避） |
| koma-healthcheck | 日1回 09:00 JST | §5.6 の照合と通知 |

生産は最大12記事/日（collect 3回 × TOP4）、消費は §12 B-2 のプランに応じて 1〜12記事/日（`KOMA_MAX_ARTICLES_PER_RUN` と koma-post の周期で調整。既定は Free プラン想定の1記事/日=周期24hに register_tasks.ps1 のパラメータで対応）。

## 7. エッジケース

| ケース | 期待挙動 |
|---|---|
| inbox 空で generate 起動 | 即 exit 0（status は success として記録） |
| collect 起動時に未処理 inbox が残存 | スキップして正常終了（生成が追いつくまで新規収集しない。ニュース鮮度は48hルールで generate 側が担保） |
| generate の画像生成が部分失敗 | ptc/step3 の既存仕様維持: `image_status` に成否記録、step4 が投稿文と画像の整合を取る |
| post 起動時に在庫0 | 何もせず正常終了 |
| 6ツイート中3で失敗 | 進捗書き戻し→次回 t4 から再開。二重投稿しない（モックで再検証） |
| X 認証エラー連続3回 | POSTING_DISABLED 作成→以後自己停止→healthcheck が翌朝 ALERT（§5.6） |
| レート制限（429） | その回は打ち切り。失敗カウント対象外。次周期に自然リトライ |
| PC がスリープ/再起動でタスク未実行 | スケジューラ設定で「スケジュール時刻を逃した場合すぐ実行」を有効化（register_tasks.ps1 に含める）。長期停止は healthcheck が検知 |
| 同時二重起動 | 全スクリプトにロックファイル（post_worker の既存方式を generate にも実装） |
| Anthropic schema 検証失敗 | 1回再試行→なお失敗なら例外→その記事をスキップし次記事へ（generate は部分成功を許容し、成功分だけ output へ） |
| トースト通知が出せない環境 | ALERT ファイルは必ず残す。通知失敗は healthcheck の exit code に影響させない |

## 8. 失敗シナリオとレッドチーム所見

計画ゲート回答: (1)最確率の失敗は下表1〜3。(2)境界=§2.2（特に Composio 復活・反応分析・ロジック改善に手を出さない）。(3)DoD は全て実行観察形式。(4)実装者が最初に詰まるのは llm_call 拡張 → §5.4 に確定仕様を記述済み。(5)既存設計書 v1 では完全自動運用が成立しないため本改訂は必要。

| # | 失敗シナリオ | 早期警報サイン | 設計上の対策 |
|---|---|---|---|
| 1 | X API 直叩きの media upload が動かず（v2/v1.1 の仕様差・レスポンスキー差）、投稿だけが止まり続ける | Phase 1 の実投稿1件 DoD が通らない / POSTING_DISABLED が初週に発生 | v2→v1.1 フォールバックを実装（§5.5）。実投稿1件を独立 DoD 化し、無人運転開始の前提にする。失敗しても他プロセスは無傷（疎結合） |
| 2 | 無人稼働が静かに死ぬ（PC スリープ・鍵失効・SDK 破壊的変更）まま数週間放置され、旧システムと同じ塩漬けに戻る | ALERT ファイルの発生 / X アカウントの更新停止 | healthcheck + トースト + ALERT ファイルの三重通知（§5.6）。「見逃した実行を即時実行」のスケジューラ設定。B-4 の立ち上げ期目視 |
| 3 | 完全全自動投稿が誤報・不謹慎な4コマを出し、凍結・炎上で媒体価値を失う | 引用元の訂正・削除報道 / リプ欄の事実誤認指摘 / 認証以外の 403 増加 | ptc の除外条件・2ソース裏取り・中立性ルールを一字も変えず移植。立ち上げ2週間は投稿後24h以内の目視（B-4）。凍結時は POSTING_DISABLED で拡大停止、post のみ止まり収集・生成は継続 |

v2 レッドチーム所見（2026-07-12 実施）と採択結果: #1 instagram_carousel の契約矛盾 → **採択**（§5.2 を ptc/step4 実物準拠に変更、Instagram 導出は insta_worker へ移管）。#2 プロセス緑のまま出力ゼロ → **採択**（healthcheck に成果物停滞・収集枯渇の2検査を追加 §5.6。通知の外部チャネル化は B-7 に推奨として記載、PC は hermes watcher 常駐で日常使用中のためブロッカーにはしない）。#3 403 誤分類・URL 捏造 → **部分採択**（403 ボディ分岐 §5.5 と URL HEAD 検証 §2.1 を採択。「2ドメイン以上の機械検証」は現行データ契約が記事1URL構造でロジック改善禁止の境界内のため棄却 — Phase 3 で再検討 B-6）。

補足対策: チャット露出済みの旧鍵（COMPOSIO_API_KEY / X client_secret）は Composio 廃止により大半が無効化対象。X キーは新規発行で開始し、旧鍵の失効を Phase 0 のユーザー作業に含める（B-5）。

## 9. 実装手順（Sonnet 向けタスク分割）

順序: 1 → 2 →（3・4・5・6 並列可）→ 7 → 8。1タスク=1コミット目安。

1. **リポジトリ組成** — §4 レイアウト・README 骨子・.env.example・.gitignore・requirements.txt・docs/handover/ に zip 全量コピー・tests/fixtures/ に架空サンプル。完了条件: DoD Phase 0 の1件目 + grep 0件（この時点で src/ は空でも grep は通る）
2. **status_util.py + askhub_tools.py 拡張** — §5.4/§5.6 どおり。完了条件: pytest の llm_call schema モックテスト通過
3. **collect.py 移植** — 出口をローカル inbox に置換、`--mock`（xAI 呼び出しを fixtures 返却に差替）実装、inbox 残存スキップ。完了条件: DoD の collect --mock 項目
4. **generate.py 一本化移植** — ptc/step1〜4 のプロンプト・定数・検証ロジックを不変で移植し、`WORKSPACE` 定数（`/opt/amazon/genesis1p-tools/var/workspace`）をリポジトリ相対 `tmp/` に、`GOOGLEDRIVE_*` 入出力をローカル I/O に置換。ロック・`--mock`・validate_output 自動実行・部分成功許容。完了条件: DoD の generate --mock 項目
5. **x_adapter.py + post_worker.py 改修** — §5.5 のアダプタ新設（post_x.py から署名コード流用）、post_worker のオーケストレーション部移植 + 自己停止（§5.6）+ `--mock`。完了条件: DoD の post --mock 2項目
6. **healthcheck.py + validate_output.py + register_tasks.ps1** — §5.6/§6 どおり。完了条件: DoD の healthcheck 項目 + validate_output の正常/異常系テスト
7. **docs 整備** — OPERATIONS.md（ループ6要素・POSTING_DISABLED 解除・鍵ローテ・スケジューラ変更手順）・CONTRACTS.md・README 完成。完了条件: DoD Phase 0 全項目のセルフチェック記録を README に記載
8. **Phase 1 実 API 検証** — ユーザーのキー投入後: 実収集→実生成→実投稿1件→register_tasks.ps1→無人1サイクル。完了条件: DoD Phase 1 全項目

## 10. テスト計画

- 単体: pytest（llm_call schema モック / weighted_length 境界 / validate_output 正常・異常 / status_util の連続失敗カウント）
- 結合（モック）: DoD Phase 0 の各 `--mock` 実行を README 記載のコマンドどおりに実施し、stdout とファイル生成を観察。再開性は kill→再実行で観察
- 実機: Phase 1 DoD（実投稿1件はスレッド URL を記録）。無人1サイクルは「ユーザーが当日 PC に触らない日」を1日設定して確認
- 回帰: generate.py 内の移植プロンプト・定数が ptc 原本と一致することを `git diff --no-index` 相当の目視でなく、`tests/test_ported_constants.py`（SERIF_LIMITS・FIXED_STYLE・スコア軸名・除外条件文字列が handover/ 原本と一致するか読み比べる自動テスト）で担保

## 11. 実装時判断ルール

1. ptc 移植で現行 SDK と非互換が出たら、本体ロジックを書き換えず askhub_tools.py 側で吸収。吸収不能なら §12 に追記してユーザー確認
2. x_adapter の media upload レスポンスキー（`data.id` / `media_id_string`）は初回実投稿時に実値確認し、両対応の取り出し（`data.get("id") or data.get("media_id_string")`）で実装してよい
3. プロンプト・スコアリング・画風・字数制限は ptc/step1-4 の値を一字も変えない。変更してよいのはモデルIDの env 参照化（§5.4）とファイルパスのみ
4. 新規の抽象化・共通化は status_util.py と x_adapter.py の2つまで。①②③の共通 config モジュール等は作らない（3スクリプト疎結合が核。yagni）
5. tmp/・status/・.env はコミットしない。fixtures は架空データのみ
6. `--mock` の定義（3スクリプト共通）: 外部 API 呼び出し関数（llm_call / generate_or_edit_image / xAI 呼び出し / upload_media / post_tweet）を、fixtures ベースの固定応答・生成 1x1 PNG・連番 ID 採番のダミーに差し替える引数。ネットワークに一切出ない
7. トースト通知の実装が30分以上難航したら、ALERT ファイル生成のみで DoD 通過とし、通知手段は §12 B-7 としてユーザー確認に切り替える
8. Windows 前提の箇所（ps1・トースト・スケジューラ）は Phase 0 の Linux/CI 環境では実行検証不能でよい。ps1 は構文チェック（`pwsh -NoExecute` 相当が無ければ目視+ユーザー実行）まで

## 12. 未解決事項（ユーザー確認待ち）

- **B-2【Phase 1 ブロッカー】X API プランと投稿頻度**: 自前 X アプリ作成 + キー4種発行はユーザー作業。プランで運転レートが決まる — Free（$0）: 約1記事/日が上限目安（write 上限とリクエスト/日制限のため。koma-post 周期24h・MAX=1）／Basic（$200/月）: 12記事/日フル稼働可。**推奨: Free で1記事/日から開始**し反応を見て判断（register_tasks.ps1 のパラメータ変更のみで増速可）
- **B-3 リポジトリ public/private**: private 推奨（運用プロンプト・収益戦略を含む）
- B-4 立ち上げ期の投稿後24h以内目視を何週間続けるか（推奨2週間）
- B-5 露出済み旧鍵の失効確認（COMPOSIO_API_KEY は解約/失効、X 系は新規発行で置換）
- B-6 反応分析（工程8）を Phase 3 としていつ設計するか（無人運転が2週間安定してから推奨）
- B-7 ALERT の通知チャネル: 既定は Windows トースト + ALERT ファイル。**推奨: PC 外に届くチャネル（メール等）を1つ追加**（red-team #2 指摘。PC 自体が長期停止した場合はトーストも出ないため）。必要なら追加指示
