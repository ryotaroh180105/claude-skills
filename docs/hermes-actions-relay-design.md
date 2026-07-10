# Hermes リレー実行系の GitHub Actions 移行 設計書

実装セッション（Sonnet）向け。このドキュメントだけで実装が完結すること（会話の文脈を前提にしない）。
実装対象は `hermes-relay` ブランチの `.github/workflows/hermes-relay-exec.yml`（新規）。
`automation/hermes-relay-watcher.sh` は原則無改修で再利用する。

## 0. 背景と決定

- 現行リレーの enqueue 側（クエリ設計→`hermes-relay` ブランチへ push→結果整形）は
  claude.ai / スマホから既に完結する。**実行側（`hermes -z` を叩く watcher）だけが
  ユーザーの実機 PC（ARM64 Windows, Task Scheduler 毎分起動）に固定**されており、
  PC が起動していない間はキューが滞留する（既知の制約 §9 in
  `docs/hermes-web-engine-design.md`）。
- ユーザーの要求: 「スマホ / claude.ai から触れれば実行場所は問わない」。
  つまり要件は **実行系を常時稼働のホストに移すこと** のみ。enqueue 側は変更不要。
- **決定: GitHub Actions（push トリガ）で既存 `hermes-relay-watcher.sh` を実行する。**
  - リポジトリは public → Actions 標準ランナーは無料・分数無制限。
  - enqueue の push がそのまま実行トリガになる（毎分ポーリング不要、キュー滞留なし）。
  - 実装・受け入れテストとも Claude Code セッションだけで完結（VPS 契約・SSH 不要）。
  - 障害調査も GitHub MCP（`actions_list` / `get_job_logs`）でセッションから可能。
    現行は watcher.log が PC の中にあり、スマホから見えない — ここも改善する。
  - PC 側 watcher は削除せず**無効化のみ**（ロールバック = 再有効化）。
- 見送った代替案:
  - **VPS + 既存 setup-local.sh**: レイテンシは現行同等だが、契約・SSH・月額費用・
    保守がユーザーの手作業になり「スマホだけで完結」に反する。Actions 案が
    H1（下記）で全滅した場合の fallback として §8 に残す。実装はしない。
  - **Hermes gateway（Telegram等）でスマホから直接操作**: PC 常時起動が前提のままで
    目的を満たさない上、Claude のクエリ設計・整形・捏造チェックを挟む現行方針と矛盾。対象外。

## 1. 工程分解と担当（第一原理・移行前後）

| # | 工程 | 現行の担い手 | 移行後 | 変更 |
|---|---|---|---|---|
| 1 | クエリ設計（出力形式・捏造ガード込み） | Claude セッション | 同左 | なし |
| 2 | enqueue（pending へ push） | Claude セッション | 同左 | なし |
| 3 | 起動トリガ | PC の Task Scheduler（毎分） | GitHub push イベント | **変更** |
| 4 | 実行環境の維持（hermes 本体） | PC に常駐インストール | ランナー使い捨て + actions/cache | **変更** |
| 5 | 認証の保持（xai-oauth） | PC の `~/.hermes` | repo Secret からランナーへ毎回シード | **変更** |
| 6 | `hermes -z` 実行・結果 commit/push | `hermes-relay-watcher.ps1`（PC） | `hermes-relay-watcher.sh`（ランナー、既存品） | ホストのみ変更 |
| 7 | 結果整形・捏造チェック | Claude セッション | 同左 | なし |
| 8 | 監視・障害調査 | PC の watcher.log（スマホから不可視） | Actions run ログ（GitHub MCP で可視） | **改善** |
| 9 | ロールバック | — | schtasks 再有効化（PC 操作 1 回） | 新設 |

意図的に対象外: NotebookLM 復活（廃止済み）/ web_extract の有料 backend 契約（方針外）/
Hermes gateway 経由のスマホ直接操作（上記の通り）。

## 2. アーキテクチャ

```
Claude セッション ──push(query)──▶ hermes-relay ブランチ
                                      │ push イベント
                                      ▼
                    GitHub Actions (ubuntu-latest, x86_64)
                      1. checkout hermes-relay
                      2. actions/cache で hermes インストールを復元（なければ install.sh）
                      3. Secret HERMES_SEED_B64 → ~/.hermes に展開（auth+config）
                      4. bash automation/hermes-relay-watcher.sh   ← 既存品そのまま
                         （pending 全件を hermes -z 実行 → results/ に commit → push）
                                      │ push(results)
                                      ▼
Claude セッション ◀──fetch/show─── hermes-relay ブランチ
```

- **watcher.sh の再利用が本設計の核**。lock（mkdir）・fetch/reset・pending ループ・
  frontmatter 付き結果生成・done 移動・rebase リトライ付き push を全部持っている。
  ランナー上では `HERMES_RELAY_DIR=$GITHUB_WORKSPACE` を指すだけで動く想定。
- 直列化: workflow の `concurrency: group` で run を直列化（`cancel-in-progress: false`）。
  待たされた run は起動時に pending が空なら watcher が即終了する（十数秒）。
- 再帰防止: watcher の結果 push は `GITHUB_TOKEN` 経由 → GitHub の仕様で
  **GITHUB_TOKEN による push は workflow を再トリガしない**。よって paths フィルタは
  付けない（付けないことで、空コミット push による手動再キックも可能になる）。
  ※将来 PAT で push するよう変えるならこの前提が崩れる — その時はガード必須（YAGNI、今は不要）。
- 想定レイテンシ: push→run 起動 10〜30 秒 + 環境復元 1〜2 分 + クエリ実行 2〜3 分 =
  **1 クエリ 3〜6 分**（現行 1〜4 分よりやや遅い。ユーザー了承済みの前提で進める）。

### workflow ファイル（`.github/workflows/hermes-relay-exec.yml`、hermes-relay ブランチに置く）

push イベントは「push されたブランチ上の workflow 定義」を使うため、
**このファイルは hermes-relay ブランチにコミットする**（main 系ブランチではない）。

```yaml
name: hermes-relay-exec
on:
  push:
    branches: [hermes-relay]
  workflow_dispatch: {}
concurrency:
  group: hermes-relay-exec
  cancel-in-progress: false
permissions:
  contents: write
jobs:
  run-queries:
    runs-on: ubuntu-latest
    timeout-minutes: 45
    steps:
      - uses: actions/checkout@v4
        with:
          ref: hermes-relay
      - uses: actions/cache@v4
        with:
          path: |
            ~/.hermes/hermes-agent
            ~/.local/bin
            ~/.local/share/uv
          key: hermes-install-${{ runner.os }}-v1
      - name: Install hermes if missing
        run: |
          export PATH="$HOME/.local/bin:$PATH"
          if ! command -v hermes >/dev/null 2>&1; then
            curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
          fi
          echo "$HOME/.local/bin" >> "$GITHUB_PATH"
          hermes --version
      - name: Seed hermes auth/config from secret
        env:
          HERMES_SEED_B64: ${{ secrets.HERMES_SEED_B64 }}
        run: |
          if [ -z "$HERMES_SEED_B64" ]; then
            echo "::error::HERMES_SEED_B64 secret is not set"; exit 1
          fi
          printf '%s' "$HERMES_SEED_B64" | base64 -d | tar -xzf - -C "$HOME"
          # 中身は絶対に echo/cat しない（public リポジトリ。マスクされるのは
          # Secret の文字列そのものだけで、展開後のファイル内容はマスクされない）
      - name: Run relay watcher
        env:
          HERMES_RELAY_DIR: ${{ github.workspace }}
          GIT_AUTHOR_NAME: hermes-relay-actions
          GIT_AUTHOR_EMAIL: actions@hermes-relay
        run: bash automation/hermes-relay-watcher.sh
```

注意（実装時に確認して合わせる）:
- cache の path は「hermes の実インストール配置」に合わせる。上記は
  `~/.hermes/hermes-agent`（本体）+ `~/.local/bin`（ランチャ）+ uv 環境の想定。
  初回 run のログで実配置を確認し、ズレていたら path を直し `key` の `v1` を上げる。
- auth/config（`~/.hermes/auth.json` 等）は **cache に絶対含めない**（上記 path は
  `~/.hermes` 全体ではなく `hermes-agent` サブディレクトリに限定している。変更時も維持）。
- watcher.sh は `$RELAY_DIR/watcher.env` が無ければスキップし、PATH 上の hermes を
  拾う（`GITHUB_PATH` 追記で解決）。`git checkout hermes-relay` / `reset --hard` /
  push は actions/checkout が残す認証でそのまま通る。

### Secret のシード形式

- Secret 名: `HERMES_SEED_B64`。中身: `~/.hermes` の **認証+設定ファイルのみ** を
  tar.gz → base64 した文字列。
- **GitHub Secret の上限は 48KB**。auth.json + 設定ファイルなら余裕のはずだが、
  超えた場合はファイルを絞る（S1 で実機のファイル一覧を見てから決める）。
- 含める: `auth.json`、モデル/ツール設定ファイル（`web.backend: xai` の設定を含むもの）。
  含めない: `hermes-agent/`（本体）、ログ、履歴、キャッシュ。

## 3. 手戻り防止: 仮説と対策（検証順に。H1 が go/no-go）

- **H1: xAI OAuth がデータセンター IP（Azure/Actions レンジ）を拒否し 401/403**
  → **最初に検証**（T0）。これが落ちたら本方式は不成立 — §8 の VPS fallback か、
  ユーザー承認の上で `XAI_API_KEY`（従量課金・IP 不問）に切り替える判断をユーザーに仰ぐ。
  作り込み（cache 調整等）は T0 合格後に行うこと。
- **H2: refresh token のローテーションで静的 Secret が陳腐化**（初日は動くが翌日 401）
  → T4 で検証（連日実行し、run 内で実行前後の auth.json の sha256 **ハッシュのみ** ログに
  出して差分有無を見る。中身は出さない）。ローテーションが確認されたら contingency C1
  （§7）を実装。確認されるまでは実装しない（YAGNI）。
- **H3: PC と Actions の同時稼働で OAuth セッションが競合**（同じ refresh token を
  双方が更新→どちらかが失効）
  → 手順で回避: Secret シード後、**T0 実行前に PC の Task Scheduler を無効化**（§5 P2）。
  移行後は PC 上で hermes を直接使わない運用にする（使うと Actions 側が死に得る）。
  もし失効したら §6 の再シード手順。
- **H4: install.sh がランナーで非対話に完走しない / 配置が想定と違う**
  → T0 のログで確認。対話プロンプトで止まる場合は該当ステップに `yes ""` パイプや
  環境変数スキップを検討（install.sh の中身を読んで対処）。配置ズレは cache path 修正。
- **H5: auth.json だけでは足りず、モデル/ツール設定不足で `hermes -z` が失敗**
  （Hermes 自身の推論 LLM 設定、`web.backend: xai` など）
  → S1 で実機の `~/.hermes` 一覧と `hermes model` の出力を確認してからシード対象を決める。
  T0 の `ping` 応答で最終確認。
- **H6: 48KB Secret 上限超過**
  → S1 の一覧からファイルを絞る。どうしても超える場合のみ Secret を 2 分割
  （`HERMES_SEED_B64_1/2` を連結して復元）。
- **H7: 複数 push の競合で結果 push が衝突**
  → `concurrency` 直列化 + watcher 既存の rebase リトライで足りる想定。T5 で検証。

過去にこのリレーで実際に起きた障害（非ASCII .ps1 / 埋め込み `"` / バッテリー時タスク
不起動 / 生きているロックの誤破壊）は PC 側 watcher 固有のもの。**bash watcher と
workflow には持ち込まれないが、watcher.sh を改修する場合は既存の防御コード
（mkdir ロック、stale lock 60 分、rebase リトライ）を消さないこと。**

## 4. 実装手順（Sonnet セッションの段取り）

- **S1: 実機情報の確認（ユーザーに依頼、§5 P1 と同じ座りで済ませる）**
  `~/.hermes` のファイル一覧と `hermes model` の出力を貼ってもらい、シード対象を確定する。
- **S2: workflow を hermes-relay ブランチへ commit/push**
  §2 の YAML を土台に。この時点では Secret 未登録なので run は seed ステップで
  明示エラーになる（それで正常）。
- **S3: ユーザー操作 P1（Secret 登録）+ P2（PC watcher 無効化）**（§5）
- **S4: 受け入れテスト T0→T5 を順に**（§6。1 本でも落ちたら次に進まず、該当仮説の対策へ）
- **S5: 合格後のみドキュメント更新**
  `CLAUDE.md`（「ローカルPCのタスクスケジューラ常駐の watcher」の記述を Actions に差し替え、
  レイテンシ 3〜6 分に更新）/ `plugins/hermes-x-search/skills/hermes-x-search/SKILL.md`
  （「Automated relay」節のローカルセットアップ記述を Actions 運用に差し替え。
  ローカル手順は「fallback（VPS/実機）」として残す）/ relay ブランチ README。

## 5. ユーザー操作（PC の前に座るのはこの 1 回だけ。以後は不要）

### P1: シード作成 + Secret 登録

- **意図**: Actions ランナーは使い捨てのため、PC にしかない xai-oauth 認証と Hermes 設定を
  リポジトリ Secret として渡す必要がある（Secret は public リポジトリでも非公開・
  ログでは自動マスク）。Claude はユーザーの PC を操作できないため依頼する。
- **内容**（PowerShell。②のファイル名は S1 で確定したものに差し替える）:
  ```powershell
  # ① 現状確認（この出力を Claude に貼る → シード対象を確定）
  dir $env:USERPROFILE\.hermes
  hermes model

  # ② シード作成（例: auth.json と設定ファイルのみ。hermes-agent 本体は含めない）
  cd $env:USERPROFILE
  tar -czf hermes-seed.tgz .hermes/auth.json .hermes/<設定ファイル名>
  [Convert]::ToBase64String([IO.File]::ReadAllBytes("$env:USERPROFILE\hermes-seed.tgz")) | Set-Clipboard

  # ③ 登録後に必ず削除
  del $env:USERPROFILE\hermes-seed.tgz
  ```
  ブラウザで `github.com/ryotaroh180105/claude-skills` → Settings → Secrets and
  variables → Actions → New repository secret → Name: `HERMES_SEED_B64`、
  Value: クリップボードの内容を貼り付け → Add secret。
- **確認方法**: Secrets 一覧に `HERMES_SEED_B64` が表示される（値は見えなくて正常）。
  チャット・Issue・コミットに base64 文字列を**絶対に貼らない**（Secret 登録画面のみ）。

### P2: PC watcher の無効化（H3 対策。P1 と同じ座りで）

- **意図**: PC と Actions が同じ OAuth セッションを同時に使うと認証が壊れ得るため、
  Actions のテスト開始前に PC 側を止める。削除ではなく無効化（ロールバック用に残す）。
- **内容**:
  ```powershell
  schtasks /Change /TN HermesRelayWatcher /DISABLE
  ```
- **確認方法**: `schtasks /Query /TN HermesRelayWatcher` の「状態」が「無効」になっている。

ロールバック（Actions 案を破棄する時）: `schtasks /Change /TN HermesRelayWatcher /ENABLE`
のみで現行運用に完全復帰（PC 側は何も変更していないため）。これも PC 操作なので、
テスト期間中にリレーを使う予定があるなら P2 のタイミングをユーザーと相談すること。

## 6. 受け入れテスト（この順に。1 本でも落ちたら次に進まない）

| # | 内容 | 合格基準 |
|---|---|---|
| T0 | **OAuth go/no-go**: workflow_dispatch で起動し「relay OK とだけ返す」クエリ 1 本 | run が成功し、結果 frontmatter `status: ok`、401/403 がログにない |
| T1 | E2E: Claude セッションから通常手順で enqueue → 結果 fetch | push から **10 分以内**に `automation/results/<id>.md` が返る |
| T2 | X 回帰: 既存形式の x_search クエリ | 出典 URL 付きで従来同等の結果 |
| T3 | Web 回帰: web_search 誘導クエリ（捏造ガード文言込み） | 使用ツール自己申告が web_search、x_search に流れていない |
| T4 | 翌日再実行（H2 検証） | 前日シードのまま `status: ok`。auth.json ハッシュ差分の有無を記録 |
| T5 | 連投: 1 push に 2 クエリ + 実行中にもう 1 push | 3 本全部 ok、結果 push の衝突なし（rebase リトライ含め成功） |
| T6 | （任意・非ブロッキング）x86_64 Linux での browser/web_extract 検証 | 動けば UC5（特定URL全文）が復活する。動かなくても本移行の合否に影響しない |

T6 補足: 現行 PC は ARM64 Windows で Playwright バイナリが無く browser 系が全滅だったが、
ubuntu ランナーは x86_64。xAI backend の search-only 制約は変わらないため、動くとすれば
`browser` ツール経路。合格した場合のみ SKILL.md の「web_extract は不可」節を更新する。

## 7. Contingency（発動条件付き。条件成立まで実装しない）

- **C1（H2 成立時）: 認証ファイルの自動持ち回り**
  Secret を静的シードから「ブランチ内暗号化ファイル」に切り替える:
  `automation/auth.enc`（`openssl enc -aes-256-cbc -pbkdf2`、パスフレーズは Secret
  `HERMES_SEED_KEY`）を run 冒頭で復号して `~/.hermes` へ、run 末尾で auth.json が
  変化していたら再暗号化して結果と一緒に commit。これで refresh ローテーションに追従する。
  平文・base64 を絶対にコミットしないこと（暗号化後のみ）。
- **C2（push イベント取りこぼしが観測された時）: 定期バックストップ**
  schedule は default branch の workflow しか動かない仕様のため、default branch に
  「30 分毎に hermes-relay を checkout して watcher を叩く」workflow を追加する。
  取りこぼしが実際に起きるまで追加しない。手動の再キックは
  `git commit --allow-empty -m "hermes-relay: kick" && git push` で足りる。

## 8. Fallback: VPS 案（H1 不成立時のみ。ここでは実装しない）

x86_64 Linux VPS（例: 最安クラスの月額 500〜1000 円帯）に SSH し、既存の
`automation/setup-local.sh` をそのまま実行（hermes インストール → `hermes auth add
xai-oauth --no-browser` → cron 毎分登録）。watcher.sh は無改修で動く。
ユーザー作業: VPS 契約、SSH 接続、OAuth の URL 踏み 1 回。恒常コストと保守
（OS 更新・障害時 SSH）が発生するため、Actions 案が IP 起因で全滅した場合の次善策。

## 9. やらないこと（YAGNI）

- VPS 移行（§8 は fallback 設計のみ）
- C1/C2 の先回り実装（発動条件成立まで）
- watcher.sh の書き換え・多重化・並列度調整（現行ロジックで足りる）
- PC 側 watcher / setup スクリプトの削除（ロールバック用に温存）
- 有料検索/抽出 API の契約（方針外・変更なし）

## 10. 変わらない既知の制約

- `web_extract`（特定 URL 全文抽出）は xAI backend が search-only のため**ホストを
  変えても不可**（T6 の browser 経路が動いた場合のみ例外）。UC5 は引き続き
  「ページ内容をユーザーに貼ってもらう」運用。
- リポジトリが public のため、クエリ・結果も public（秘密情報をクエリに書かない）。
- 捏造ガード必須・使用ツール自己申告との突き合わせ・Claude は整形のみ、の運用ルールは全て不変。
- レイテンシは 1〜4 分 → 3〜6 分にやや悪化（トレードオフとしてユーザー了承の前提）。
