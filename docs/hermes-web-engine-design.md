# Hermes Web調査エンジン移行 設計書

実装セッション向け。このドキュメントだけで実装が完結すること（会話の文脈を前提にしない）。
実装対象は `hermes-relay` ブランチの `automation/hermes-relay-watcher.ps1` / `automation/setup-local.ps1` と、
本ブランチの `CLAUDE.md` / `plugins/hermes-x-search/skills/hermes-x-search/SKILL.md`。

## 0. 背景と決定

- 現状のリレーは 2 エンジン: `hermes`（x_search、X調査、5並列）/ `notebooklm`（Web調査、1並列）。
- NotebookLM は「1回クロール→溜めたソースに質問」の図書館型。実測 100〜196 秒/クエリで品質も良好だが、
  **検索→読解→再検索の反復（agentic 調査）が構造的に不可能**。改造は不適（ブラウザ自動化の多重往復になり遅く脆くなるだけ）。
- ユーザーの実機 Hermes は **v0.14.0 (2026.5.16)、5117 コミット遅れ**。実測で `web_extract` ツールが存在せず、
  `browser_navigate` は native Windows で `spawn EFTYPE` エラー（`automation/results/20260705T110607Z-link-extract-test.md` 参照）。
- 最新 Hermes は web 読み込みが大幅改善（2026-06-30 発表、web_search / web_extract、スクレイピングバックエンド直結）。
- **決定**: `hermes update` 後、Web調査の主経路を Hermes の web ツール群に移行（新エンジン `hermes-web`）。
  NotebookLM は「同一ソース群への反復質問（蓄積型QA）」専用に降格。**経路自体は削除しない**（互換・ロールバック用）。

## 1. ユースケース（何を検索し、どんな出力が欲しいか）

実際に流れたクエリからの帰納。テンプレは §6。

| # | ユースケース | 検索する内容の例 | 欲しい出力 |
|---|---|---|---|
| UC1 | SNS運用の素材調査 | note で伸びる記事の書き方 / AIっぽくない文章術 / SEO記事の構成・画像配置 | テクニックの箇条書き + **逐語引用**（記事にそのまま使える）+ 出典URL |
| UC2 | 競合・市場調査 | テニス動画分析アプリの価格・日本での評判・市場規模・解約理由 | **比較表** + 出典 + 未確認事項の分離 + 差別化の示唆 |
| UC3 | 技術・運用調査 | Claude Code のコスト最適化 / loop engineering の実践 | 公式ドキュメントと実践者ブログの**区別**、数値は原文のまま、逐語引用 |
| UC4 | 日次トレンド確認 | ツール・モデルの新機能や発表の一次確認 | 一次ソースURL + 日付 + 断定/未確認の分離 |
| UC5 | 特定URLの深掘り | X で見つけた note 記事・ブログの全文読解 | 見出し構成 + 逐語引用 + **生テキスト付録** + 全文読了/途中切れの明示 |

共通要件（既存 SKILL.md の出力スキーマを踏襲）: 出典URL必須 / 逐語引用「」/ 未確認・断定できない点セクション必須 /
日本語指定 / 後から再分析できる素材の保存（生テキスト付録）。

## 2. エンジンルーティング設計（後方互換）

クエリファイル先頭ヘッダの拡張:

```
engine: hermes | hermes-web | notebooklm   （省略時 hermes。未知の値は hermes 扱い＝既存仕様）
topic: <短いトピック>                       （notebooklm のみ意味を持つ。既存仕様）
timeout: <秒>                               （新設・任意。省略時 900。上限 1800 にクランプ）
```

| engine | 用途 | 実行 | 並列上限 |
|---|---|---|---|
| `hermes` | X(Twitter)調査 | `hermes -z <prompt> --accept-hooks`（現行のまま） | `HERMES_MAX_PARALLEL_HERMES`=5 |
| `hermes-web` **(新)** | Web の反復調査（UC1〜UC5） | `hermes -z <prompt> --accept-hooks` + web ツール指定（§3 H4） | `HERMES_MAX_PARALLEL_WEB`=2 (新設) |
| `notebooklm` | 蓄積型QA（同一ソース群に反復質問）のみ | 現行のまま（topic グルーピング含む） | 1（現行のまま） |

hermes-web の並列を 2 に絞る理由（仮説）: web 抽出は Playwright/スクレイピングでメモリ・CPU 消費が大きく、
無料検索バックエンドはレート制限がある。実測で安定していれば環境変数で引き上げる。

`timeout:` ヘッダ新設の理由: 深い Web 調査は x_search の実測（120〜200秒）より長くなり得る。
ただしロック保持が延びるので 1800 秒でクランプする。

## 3. 手戻り防止: 仮説と対策（実装前に必ず読む）

過去にこのリレーで実際に起きた障害: PS5.1 の非ASCII `.ps1` パースエラー / `$ErrorActionPreference=Stop` が
git の正常 stderr で死ぬ / 埋め込み `"` で引数分断 / cp932 文字化け / バッテリー時タスク不起動 /
生きているロックの誤破壊→git 競合。**watcher 改修時はこれらの既存対策コードを消さないこと**（各所のコメント参照）。

更新・移行に固有の仮説:

- **H1: `hermes update` で config 形式が変わり起動不能**（5117コミット分の破壊的変更）
  → 更新直後に `hermes --version` と `hermes -z "ping"` で確認。壊れたら `hermes doctor`、最悪はインストーラ再実行。
  実装時に `hermes update --help` でロールバックオプションの有無を確認しておく。
- **H2: 更新で xai-oauth の再ログインが必要になる**
  → `~/.hermes/auth.json` が温存されるか確認。求められたら `hermes auth add xai-oauth`（ユーザー操作1回）。
- **H3: `-z` / `--accept-hooks` / `-t` のフラグ名が変わっている**
  → 更新直後に `hermes --help` を取得し、watcher の呼び出しと突き合わせる。変わっていたら watcher 側を合わせる。
- **H4: web ツールの指定方法が不明確**。プロンプト誘導だけだと x_search に流れる恐れ。
  → 優先: `-t TOOLSETS` フラグ（v0.14 の usage に存在）で web 系トールセットを強制。
  **トールセット名は実機の `hermes tools` 出力で確認してから** `watcher.env.ps1` の `$HermesWebToolset` に設定
  （既定は未設定＝ `-t` を付けずプロンプト誘導のみ、で安全に始める）。
  併用: hermes-web 用プロンプト冒頭に「x_search は使わず、web_search / web_extract（web検索・ページ抽出）を使うこと。
  回答の末尾に実際に使ったツール名を列挙すること」を必ず入れる（テンプレ §6 に組込済み）。
  ツール自己申告により、意図しない x_search 使用を Claude 側で検知できる。
- **H5: 検索バックエンド未設定で web_search が動かない**（Brave/DDGS/xAI 等の選択制の可能性）
  → T4 で判明する。無料の DDGS があれば選択。API キーが必要なバックエンドは選ばない（コスト方針）。
- **H6: native Windows で browser 系 `spawn EFTYPE` が再発**（v0.14 で実際に発生）
  → 更新で直っている仮説をまず検証（T3）。直らなければ非ブラウザのスクレイピングバックエンドに限定。
  それも不可なら**ロールバック**: Web 経路を notebooklm に戻す（ルーティング表の書き換えのみで済む設計にする）。
- **H7: 更新中にキュー処理と衝突**
  → 手順に組込済み（タスク DISABLE → 全 hermes プロセス停止 → update → ENABLE）。§4。
- **H8: 深い Web 調査で結果ファイルが肥大し git リポジトリが膨らむ**
  → 生テキスト付録は「読めた範囲の全文」だが、テンプレで「付録は最大でも数万字程度、超える場合は主要部分を優先」と指示。
  当面はガイドラインのみ（実測してから機械的制限を検討。YAGNI）。

## 4. 更新手順（ユーザーに依頼する操作。CLAUDE.md の説明義務形式で案内すること）

意図: Hermes を最新化して web_search / web_extract を使えるようにする。キュー処理と衝突しないよう先にタスクを止める。
確認方法: `hermes --version` が 0.14.0 から進んでいること、最後の `hermes -z "ping"` が応答すること。

```powershell
schtasks /Change /TN HermesRelayWatcher /DISABLE
Stop-Process -Name hermes -Force -ErrorAction SilentlyContinue
hermes update
hermes --version
hermes -z "ping"
schtasks /Change /TN HermesRelayWatcher /ENABLE
```

失敗時: エラー全文を貼ってもらう。H1〜H3 の対策を適用。

## 5. 受け入れテスト（全てリレー経由で、この順に。1本でも落ちたら次に進まない）

| # | 内容 | 合格基準 |
|---|---|---|
| T1 | engine なし、「relay OK とだけ返す」 | status: ok、本文 relay OK（更新後の基本動作） |
| T2 | X回帰: 既存形式の x_search クエリ1本 | 従来同等の結果（出典URL付き） |
| T3 | `engine: hermes-web` で特定URL（公開 note 記事）の読解 | 見出し構成+引用が返る。EFTYPE 等のツールエラーが出ない |
| T4 | `engine: hermes-web` でオープンな調査（UC3系） | 出典URL 5件以上、使用ツールの自己申告に web 系ツール名、x_search 単独でない |
| T5 | 並列: hermes-web 2本 + hermes 2本を同時投入 | 4本全部 ok、混線なし、ロック超過なし |
| T6 | `timeout: 300` 付きクエリ | frontmatter の挙動に反映（実装確認） |

T3/T4 不合格（H6 該当）時のロールバック: ドキュメントのルーティング表で Web を notebooklm に戻すだけ。
watcher の notebooklm 経路・hermes-web 分岐はどちらも残す（コード削除しない）。

## 6. クエリテンプレ（hermes-web 用。冒頭2行が H4 対策）

UC1（SNS素材）:
```
engine: hermes-web

x_search は使わず、web検索とページ抽出ツール（web_search / web_extract 相当）で Web 記事を調査してください。
回答の末尾に、実際に使ったツール名を列挙してください。

テーマ: note で伸びる記事の書き方・構成の実践知
（1) 検索で記事候補を集め、(2) 有用な記事は本文を抽出して読み、(3) 統合してください。

出力は日本語で:
1. 要点（各項目に出典URL）
2. 引用可能な原文抜粋（「」逐語引用 + 出典URL。最も厚く）
3. 出典リスト
4. 未確認・断定できない点
5. 全文抽出（生テキスト付録。読めた記事の本文。長すぎる場合は主要記事を優先）
```

UC2（競合調査）: 上記の骨格 + 「比較表（製品/価格/特徴/評判/出典）」セクションを追加。
UC5（特定URL深掘り）: テーマの代わりに URL を明示し「このページを抽出して読む。読了できたか途中で切れたかを明示」を追加。

## 7. 実装変更点チェックリスト（watcher / setup）

- [ ] `automation/hermes-relay-watcher.ps1`:
  - 定数 `$MaxParallelWeb`（env `HERMES_MAX_PARALLEL_WEB`、既定2）
  - ヘッダパーサに `hermes-web` と `timeout:`（900 既定、1800 クランプ）
  - hermes-web 分岐: hermes と同じジョブ + `$HermesWebToolset` が設定されていれば `-t $HermesWebToolset`
  - バッチ分割: hermes / hermes-web / notebooklm の 3 群でそれぞれの cap を適用
  - Wait-Job のタイムアウトはバッチ内最大の timeout を使用
  - 結果 frontmatter に `engine: hermes-web`
  - **ASCII のみ / 既存の防御コード温存**
- [ ] `automation/setup-local.ps1`: `watcher.env.ps1` に `$HermesWebToolset = ""` の雛形行を追記（コメントで説明）
- [ ] テスト合格後のみ: `CLAUDE.md` ルーティング表 / `SKILL.md` / relay ブランチ README を更新
  （X→hermes、Web反復調査→hermes-web、蓄積型QA→notebooklm、Claude は整形のみ）

## 8. やらないこと（YAGNI）

- notebooklm 経路の削除（互換・ロールバック用に残す）
- Hermes の REST/MCP 常駐化、VPS 移行
- 有料検索 API（Tavily/Exa/Firecrawl 等）の新規契約 — Hermes 更新で足りるかを先に検証
- 結果ファイルサイズの機械的制限（まずガイドライン運用で実測）

## 9. 既知の制約（変わらないもの）

- 実機 PC が起動している間だけ処理される（スリープ中はキューに滞留、起床後に自動処理）
- notebooklm-py・Hermes とも非公式/自己ホスト。Google/xAI 側の変更で壊れ得る
- リポジトリが public の場合、クエリ・結果も public（秘密情報をクエリに書かない）
