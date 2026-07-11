# KOMA TIMES 引き継ぎ・再稼働設計書（AskHub離脱・完全ローカル化）

| 項目 | 値 |
|---|---|
| ステータス | 設計完了（実装ブロッカーは §12 B-2〜B-3 のみ。B-1は2026-07-11 ptc/ 現物判明により解消） |
| 種別 | アプリ（別リポジトリ）— 既存システムの引き継ぎ・再構築 |
| 優先度 | ユーザー指示により最優先アプリ |
| 実装モデル | Sonnet 5（推奨 effort: high） |
| 依存する設計書 | docs/designs/04-repo-reorganization.md §5.1 分類E（アプリは別リポジトリ）、docs/designs/12-app-komatimes.md（廃版・経緯のみ）、docs/designs/19 §4（同期漏れ対策） |
| 依存する既存スキル | なし（このリポジトリのスキルとは独立。運用時に sns-ops-team 等とは接続しない — §2.2） |
| 外部依存 | GEMINI_API_KEY（生成・画像）、XAI_API_KEY（収集）、COMPOSIO_API_KEY + 自前 X OAuth2 アプリ + X API 有料プラン（投稿）、Windows タスクスケジューラ |

## 0. 一次情報（この設計の正）

ユーザー提供分（2026-07-07 個別5ファイル受領、2026-07-11 `twitter_news.zip` で全量再受領・`ptc/` フォルダが新規判明。実装時は koma-times リポジトリの `docs/handover/` にコピーして参照する）:

1. `KOMA_TIMES_引き継ぎ資料.md` — 全体像・データ契約・TASK 1〜4。**「🆕 最新アップデート（2026-06-09）」節が最新の正**
2. `collect.py` — ① 収集（xAI Grok x_search + web_search）。動作コードだが出口が Composio Drive
3. `askhub_tools.py` — `llm_call` / `generate_or_edit_image` のローカル実装（Gemini + Nano Banana）。**Geminiのみ対応・model/schema引数なし**（§0-1で判明した ptc/ の要求仕様を満たさない。§9-4 で拡張要）
4. `post_worker.py` — ③ 投稿ワーカー。オーケストレーション完成・Composio X アダプタ実装済み（実投稿のみ未検証）。入口が Composio Drive
5. `ptc/main_pipeline.py` + `step0_fetch_inbox.py`〜`step5_publish_drive.py` — **② 生成パイプラインの現行本体**（2026-07-11判明。以下「B-1」は解消）。00→05 を `main_pipeline.py` が順に await するAskHub PTC駆動構成:
   - `step0_fetch_inbox.py`: Composio Drive 入口(`komatimes_research`)から `search_results.json` 取得
   - `step1_select.py`: 4軸20点スコア（hook_power/shareability/story/social_literacy）+ 重複名寄せ + `emotion_core` 付与 → `TOP_N=4` 選定
   - `step2_script.py`: 4コマ台本 + 画像プロンプト生成（`SERIF_LIMITS`・`FIXED_STYLE`・動物キャラ比喩なし・字数超過時リトライ1回）
   - `step3_images.py`: 統合画像+パネル4枚生成（`askhub_tools.generate_or_edit_image`、部分失敗許容）
   - `step4_compose.py`: X 6ツイートスレッド生成 → `output/article_{run_id}_{n}.json` + `_DONE`
   - `step5_publish_drive.py`: Composio Drive 出口フォルダへ配信（post_worker.py の入力）
   - `step1_select.py`/`step2_script.py` は `llm_call(prompt, model="claude-sonnet-4-6", schema=<JSON Schema>)` を呼ぶ（AskHubカーネル版・Anthropic構造化出力）。ローカル版 askhub_tools.py の `llm_call(prompt)` にはこの model/schema 引数が無い（上記3参照）
6. `system_prompt.py`（ptc版、117行）— PTC駆動の司令塔プロンプト。`system_prompt.py`（ルート、95行・`学習データ.md`直接bash実行を指示する旧版）と `system_prompt_no_ptc.py`（コスト比較用・チャット完結版）は**いずれも廃止対象**（参考保持のみ）

**旧・被supersede資料**: `学習データ.md`（旧モノリシック版②本体。引き継ぎ資料執筆時点では最新だったが、現在の実運用は `ptc/step0-5.py` に置き換わっている）。**移植元は `学習データ.md` ではなく `ptc/step1-4.py` を正とする**（§9-4を参照）。

## 1. 目的・背景（Why）

KOMA TIMES = AIニュース4コマ漫画のXアカウント。収集→選定→4コマ台本→画像生成→Xスレッド投稿を全自動で回す。既存設計は「② 生成」を AskHub（チャットエージェント+PTC）で実行し、①↔②↔③ を Composio 経由の Google Drive フォルダで中継していた。

ユーザー決定: **AskHub での実行はもうしない**。よって:
- ② を AskHub PTC からローカル Python スクリプトに置き換える
- Drive 中継の存在理由（AskHub とローカルの環境分断）が消滅するため、**プロセス間受け渡しをローカルファイルに一本化**する（引き継ぎ資料の初期設計 §1 の形に戻す）
- Composio は X 投稿アダプタとしてのみ残す（実装確定済み資産を捨てない）

## 2. スコープ

### 2.1 やること

- 新リポジトリ `ryotaroh180105/koma-times` の組成（§4）
- ① `collect.py` 改修: 出口を Composio Drive → ローカル `tmp/inbox/search_results.json` に変更（xAI 収集ロジックは不変更）
- ② `generate.py` 新規: AskHub PTC（00〜05 + system_prompt 駆動）を置き換えるローカル一気通貫スクリプト。データ契約は §5 を厳守
- ③ `post_worker.py` 改修: `sync_from_drive()` と Drive 関連コード（`_write_drive_file`・`OUTPUT_FOLDER_ID`）を削除し、`tmp/output/` 直読みに戻す。Composio X アダプタ（`upload_media`/`post_tweet`）とオーケストレーション部は**1文字も変更しない**
- ④ `insta_worker.py` 新規（Phase 2）: 引き継ぎ資料 TASK 3（Pillow でキャプション帯合成）。保存先はローカル `tmp/instagram/` + Google Drive アップロード（スマホ閲覧用。これは AskHub 非依存の公式 Drive API or Composio でよい — 実装時判断 §11-4）
- 引き継ぎ資料 TASK 2 の反映: ② は X 用5枚のみ生成、`instagram_carousel` は素材形式（§5.2）
- モック検証（引き継ぎ資料 §10 の方式）と実投稿1件までの検証手順（§10）
- Windows タスクスケジューラ登録手順書（§6 の3タスク）

### 2.2 やらないこと（明示的スコープ外）

- AskHub / PTC / `system_prompt.py` の維持・改修（廃止。ファイルは docs/handover/ に凍結保存のみ）
- Composio Drive 中継（`GOOGLEDRIVE_*` によるプロセス間受け渡し）— ローカルファイルに置換。※④のスマホ向け Drive アップロードは「中継」ではなく「配信」なので対象外
- Instagram / TikTok の自動投稿（引き継ぎ資料どおり Phase 3 以降。②はX用素材+キャプション文字列まで）
- 選定ロジック・台本プロンプト・画風の変更（学習データ.md の確定内容を移植する。改善は再稼働後の別フェーズ）
- Hermes Agent 経由の収集（collect.py は xAI API 直叩きで完結しており、hermes-relay はこのシステムでは使わない）
- claude-skills リポジトリへのコード配置（分類E違反。設計書のみ本リポジトリ）
- X 投稿の最終人間チェックゲート（引き継ぎ資料 §11 の決定「完全全自動」を維持）

## 3. 完成条件（Definition of Done）

Phase 0（組成・モック疎通）:
- [ ] `ryotaroh180105/koma-times` リポジトリが存在し、§4 のレイアウトどおりファイルが配置されている
- [ ] `.env.example` に必要キー4種（GEMINI/XAI/COMPOSIO_API_KEY, COMPOSIO_USER_ID）が記載され、`.gitignore` が `.env` `tmp/` を除外している
- [ ] `grep -rn "GOOGLEDRIVE\|OUTPUT_FOLDER_ID\|INBOX_FOLDER_ID\|sync_from_drive" src/` が 0 件（Drive 中継の完全除去）
- [ ] モック実行: `python src/generate.py --mock`（llm_call/画像をダミー応答に差し替え、サンプル search_results.json 使用）が exit 0 で、`tmp/output/` に `article_*.json` 4件 + `_DONE` が生成され、各 JSON が §5.2 スキーマの必須キーを持つ（検証スクリプト `python scripts/validate_output.py` exit 0）
- [ ] モック実行: `python src/post_worker.py --mock`（upload_media/post_tweet をID採番モックに差替）で、カテゴリ分散選定→6ツイート進捗書き戻し→`tmp/posted/` 退避が観察できる。途中killして再実行すると投稿済み t をスキップして再開する（二重投稿なしのログ確認）

Phase 1（実投稿）:
- [ ] `python src/collect.py` 実行で `tmp/inbox/search_results.json` が §5.1 スキーマで生成される（実 xAI API）
- [ ] `python src/generate.py` 実 API 実行で 1記事以上が `tmp/output/` に画像付きで出る
- [ ] `python src/post_worker.py` で X に6ツイートスレッドが1件実投稿され、`tmp/posted/` へ退避される（引き継ぎ資料 TASK 1 の受け入れ条件）
- [ ] タスクスケジューラ3本（収集8h/生成=収集15分後/投稿2h）の登録手順書 `docs/SCHEDULER.md` が存在し、ユーザーが登録・1サイクル無人完走を確認

Phase 2（Instagram素材）:
- [ ] `python src/insta_worker.py` で1記事分のキャプション帯付き画像4枚（日本語が正しく描画）が `tmp/instagram/<article_id>/` に生成され、Drive の指定フォルダにアップロードされる

## 4. 成果物の構成（ファイルレイアウト — koma-times リポジトリ）

```
koma-times/
├── README.md                 # 一言概要・セットアップ・実行・スケジューラ登録
├── .env.example
├── .gitignore                # .env / tmp/ / __pycache__
├── docs/
│   ├── handover/             # 受領5ファイル+学習データ.md を凍結保存（改変禁止）
│   ├── CONTRACTS.md          # §5 データ契約の写し（プロセス間の正）
│   └── SCHEDULER.md          # Windows タスクスケジューラ登録手順（3タスク）
├── src/
│   ├── collect.py            # ① 収集（改修版）
│   ├── generate.py           # ② 生成（学習データ.md の koma_times.py を移植・TASK 2 反映）
│   ├── askhub_tools.py       # 受領版そのまま（generate.py が import）
│   ├── post_worker.py        # ③ 投稿（Drive除去版）
│   └── insta_worker.py       # ④ Instagram素材（Phase 2）
├── scripts/
│   └── validate_output.py    # article_*.json のスキーマ検証（§5.2 必須キー）
└── tmp/                      # 実行時生成（git管理外）: inbox/ output/ posted/ instagram/ images/
```

## 5. データ構造（プロセス間契約 — 引き継ぎ資料 §4 を継承、変更点のみ明記）

### 5.1 入口 `tmp/inbox/search_results.json`（①→②）

引き継ぎ資料 §4.1 と同一（category / articles[title,url,snippet] の配列）。パスのみ `tmp/search_results.json` → `tmp/inbox/search_results.json` に変更（受け渡し口を inbox に統一）。②は読み込み成功後、処理済みとして `tmp/inbox/done/` へ移動する（同名再投入との衝突回避）。

### 5.2 出口 `tmp/output/article_{RUN_ID}_{n}.json`（②→③④）

引き継ぎ資料 §4.2 に **TASK 2 を適用した形**が正:

- `x_thread`: t1〜t6（変更なし。t1=combined、t2〜t5=panel1-4、t6=画像null）
- `instagram_carousel`: **素材形式** `{"slideN": {"text": "<30〜60字>", "panel_image": "article_{RUN_ID}_{n}_panelN.png"}}`（完成画像は持たない）
- `instagram_status` キーは**出力しない**（廃止）
- 画像は1記事5枚（combined + panel1-4）。RUN_ID = `YYYYmmdd_HHMMSS`
- アトミック書き込み（.tmp→os.replace）、全記事完了で `_DONE`
- ③が `_post_progress` を追記する仕様は不変

### 5.3 必要環境変数（.env）

```
GEMINI_API_KEY=      # ② テキスト+画像生成
XAI_API_KEY=         # ① 収集（grok。モデルは KOMA_XAI_MODEL で上書き可）
COMPOSIO_API_KEY=    # ③ X投稿（④のDriveアップロードにも流用可）
COMPOSIO_USER_ID=    # 未設定なら "default"
```

## 6. 処理フロー

タスクスケジューラ駆動・常駐なし（各スクリプトは1回実行して終了）:

1. **収集（8時間おき）**: `collect.py` — xAI x_search+web_search で7カテゴリ収集（X発:報道発≒7:3、2ソース裏取り）→ `tmp/inbox/search_results.json` をアトミック書き込み
2. **生成（収集トリガーの15分後）**: `generate.py` — inbox 読込→4軸20点選定 TOP4→台本（字数検証・自動短縮リトライ）→画像5枚→X用6ツイート→ `tmp/output/` へ記事単位出力→ `_DONE` → inbox を done/ へ
3. **投稿（2時間おき）**: `post_worker.py` — `tmp/output/` の未投稿を古い順+カテゴリ分散で1件選定→ t1〜t6 を画像添付+reply連結で投稿（ツイート間8秒）→全成功で `tmp/posted/` 退避。部分失敗は進捗保存して次回再開
4. **Instagram素材（任意時刻・Phase 2）**: `insta_worker.py` — output/ と posted/ の記事 JSON から素材取得→Pillow で下部18%帯+日本語キャプション合成→ `tmp/instagram/<id>/` + Drive アップロード→処理済み記録

生産12記事/日・消費12記事/日で均衡（引き継ぎ資料 §1 の設計を維持）。

## 7. エッジケース

| ケース | 期待挙動 |
|---|---|
| inbox に search_results.json が無い状態で②起動 | エラー終了（既存仕様）。スケジューラの次回収集を待つ |
| ②の画像生成が部分失敗 | 既存仕様維持: `image_status` に成否記録、投稿文が嘘をつかない整合処理 |
| ③実行時に在庫0 | 何もせず正常終了（既存仕様） |
| ③が6ツイート中3で失敗 | 進捗書き戻し→次回 t4 から再開。二重投稿しない（既存仕様・モックで再検証） |
| X スパム判定・レート制限 | WAIT_BETWEEN_TWEETS=8秒 + 2hおき1記事を維持。凍結の早期警報は §8-2 |
| 同時二重起動 | ロックファイル（既存仕様）。generate.py にも同方式のロックを追加 |
| 学習データ.md の移植コードが現行 Gemini SDK と非互換 | askhub_tools.py のシグネチャ（llm_call/generate_or_edit_image）は維持されているため差分は shim 内で吸収。それでも動かない箇所は §11-1 |

## 8. 失敗シナリオとレッドチーム所見

計画ゲート回答: (1)最確率の失敗は下表1〜3。(2)境界=§2.2（特にAskHub維持・Instagram自動投稿・ロジック改善に手を出さない）。(3)DoDは全て実行観察形式。(4)実装者が最初に詰まるのは askhub_tools.py の schema対応拡張（§9-4.5）— 単体テストを完了条件にした。(5)既存スキル・設計書で代替不可（12は廃版）。

| # | 失敗シナリオ | 早期警報サイン | 設計上の対策 |
|---|---|---|---|
| 1 | ptc/step1-4.py の移植時に askhub_tools.py の schema拡張を作り込みすぎ、または逆に雑に済ませて `step1_select.py`/`step2_script.py` が要求する構造化出力（4軸スコア・emotion_core等）の型が壊れる | generate.py の出力 JSON が §5.2 スキーマの必須キーを満たさない / validate_output.py が exit 1 | §9-4.5 を独立タスク化し単体テストを完了条件にする。schema検証は Anthropic API 呼び出し直後に行い、失敗時は再試行1回のみ（既存 step2 の字数超過リトライと同じ方針） |
| 2 | X API 有料プラン・自前 OAuth2 アプリ未整備で Phase 1 が無期限停滞し、システム全体が再び塩漬けになる | Phase 0 完了から2週間、X connect の進捗ゼロ | Phase 0/2（X 非依存）を先に完成させ、①②④は X なしで日次稼働開始できる構成にする。X connect はユーザー作業として §12 B-2 に明記 |
| 3 | 完全全自動投稿が誤報・不謹慎な4コマを投稿し、アカウント凍結や炎上で媒体価値を失う | 引用元訂正・削除のニュースを扱った投稿 / リプ欄に事実誤認指摘が連続 | 既存の除外条件（炎上回避・信頼性の足切り）・2ソース裏取り・中立性ルールを移植で維持。立ち上げ2週間は投稿後24h以内の目視確認をユーザー運用に含める（§12 B-4）。凍結時対応: post_worker を止めるだけで他プロセス無傷（疎結合） |

チャット露出済みの COMPOSIO_API_KEY / X client_secret の rotate（引き継ぎ資料の警告）を Phase 0 のユーザー作業に含める。

## 9. 実装手順（Sonnet 向けタスク分割）

順序: 1 → 2 →（3・4・5 は並列可）→ 6 → 7。

1. **リポジトリ組成** — `ryotaroh180105/koma-times`（private、§12 B-3 で確認）作成。§4 レイアウト・README・.env.example・.gitignore・docs/handover/ に受領ファイルをコピー。完了条件: Phase 0 DoD 1〜2項目
2. **post_worker.py の Drive 除去** — `sync_from_drive`・`_write_drive_file`・`OUTPUT_FOLDER_ID` と main() 内の呼び出しを削除。アダプタ・オーケストレーションは不変更。完了条件: grep 0件 + `--mock` フラグ実装（upload_media/post_tweet をID採番モックに差替する引数）でモック DoD 通過
3. **collect.py のローカル出口化** — `put_to_inbox`（Composio Drive）を `tmp/inbox/search_results.json` へのアトミック書き込みに置換。composio import を削除。完了条件: モックレスポンスで JSON がスキーマどおり書かれる
4. **generate.py 移植** — `ptc/step1_select.py`〜`step4_compose.py` のロジック（スコアリング・字数検証・画風・SERIF_LIMITS・FIXED_STYLE・動物キャラ禁止を1字も変えず）を `src/generate.py` に一本化移植し、(a) `step0`/`step5` の Composio Drive 呼び出しを `tmp/inbox/`・`tmp/output/` へのローカルI/Oに置換 (b) TASK 2（Instagram画像生成の削除・素材形式化・instagram_status 廃止）を適用 (c) 二重起動ロック追加 (d) `--mock` 実装。完了条件: Phase 0 DoD のモック生成項目 + validate_output.py exit 0
4.5. **askhub_tools.py 拡張** — `llm_call` に `model`・`schema` 引数を追加し、schema指定時は Anthropic API（`ANTHROPIC_API_KEY`）を tool-use/structured-output で直叩きする経路を新設（`step1_select.py`/`step2_script.py` が要求する構造化出力に対応するため。既存の Gemini 経路は無引数呼び出し時のみ残す・呼び分けは model引数の有無で判定）。完了条件: schema付き呼び出しで検証可能なJSONが返る単体テスト1件
5. **validate_output.py 作成** — §5.2 必須キー（x_thread.t1〜t6 の text/image、instagram_carousel の素材形式、index/title/category/score）の検査。完了条件: 正常系 exit 0 / キー欠落ファイルで exit 1
6. **実 API 検証（Phase 1）** — ユーザーがキー投入後: 収集→生成→実投稿1件。完了条件: Phase 1 DoD 全項目 + docs/SCHEDULER.md
7. **insta_worker.py（Phase 2）** — Pillow 合成（下部18%白帯・Noto Sans JP・黒文字中央）+ Drive アップロード + 処理済み記録。完了条件: Phase 2 DoD

## 10. テスト計画

- モック検証（引き継ぎ資料 §10 の実績ある方式を踏襲）: ②はダミー llm/画像 + サンプル search_results.json で全 STEP 実走。③はモックアダプタで「カテゴリ分散・退避・在庫枯渇・部分失敗→再開」の4ケースを観察
- スキーマ検証: validate_output.py（機械検証、CI は Phase 1 以降に GitHub Actions 化を検討 — YAGNI、初回は手動実行でよい）
- 実投稿検証: 1記事を手動トリガーで投稿し、Xの実スレッドと tmp/posted/ 退避を目視+ファイル観察
- 回帰確認: post_worker.py の変更が Drive 除去と --mock 追加のみであることを `git diff` で確認（アダプタ・オーケストレーション部に差分がない）

## 11. 実装時判断ルール

1. ptc/step1-4.py 移植で現行 SDK と非互換が出たら、本体ロジックを書き換えず askhub_tools.py（shim）側で吸収する。shim でも吸収不能なら §12 に追記してユーザー確認
2. Composio の X アダプタ（upload_media/post_tweet）は引き継ぎ資料が「実APIで確定済み」とする実装を信頼し、presigned 戻りキー（url/key）の実値確認だけ初回実投稿時に行う（コメント済みの ★確認点）
3. プロンプト・スコアリング・画風は ptc/step1-4.py の値を一字も変えずに移植する（改善提案は再稼働後に別タスク化）
4. ④の Drive アップロードは Composio 流用を第一候補、公式 google-api-python-client を第二候補とし、実装が簡単な方を選んでよい（どちらでも「中継」ではないので §2.2 に抵触しない）
5. 新規の抽象化・共通化（例: ①②③の共通 config モジュール）はしない。3スクリプト独立を維持（疎結合が既存設計の核。yagni）
6. tmp/ 配下・.env はコミットしない（実データ）。サンプル JSON は `docs/handover/` ではなく `tests/fixtures/` に架空データで置く

## 12. 未解決事項（ユーザー確認待ち — B-2〜B-3 が実装着手のブロッカー）

- ~~B-1 学習データ.md の提供~~ **解消済み（2026-07-11）**: `twitter_news.zip` 再受領で `ptc/step0-5.py` が判明。② 生成本体・参照データ（メディア一覧・スコア基準・画風プロンプト）はこちらが正（§0参照）
- **B-2【Phase 1 ブロッカー】X 投稿の前提**: 自前 X OAuth2 アプリ（client_id/secret + Bearer）作成、X API 有料プラン契約、Composio への Twitter connect。全てユーザー作業（手順は README に記載する）
- **B-3 リポジトリの public/private**: private 推奨（運用プロンプト・参照データ・収益戦略を含むため）
- B-4 立ち上げ期の目視確認運用（投稿後24h以内チェック）を何週間続けるか（推奨2週間）
- B-5 露出済み COMPOSIO_API_KEY / X client_secret の rotate 実施
- B-6 ①の収集を将来 hermes-relay 系に寄せるか（現状は xAI 直叩きで完結。統合は再稼働後の検討事項）
