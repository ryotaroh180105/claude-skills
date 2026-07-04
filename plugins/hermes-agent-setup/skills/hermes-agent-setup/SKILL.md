---
name: hermes-agent-setup
description: Hermes Agent（Nous Research）+ MCP + xAI Grok の X/ウェブ検索を組み合わせた情報収集基盤のセットアップと運用。「Hermes をセットアップして」「Grok/X で〜を調べて」「スキルネタを収集して」「情報収集基盤の疎通確認をして」「収集結果を ROADMAP の候補リストに追加して」といった依頼で使う。API キー未設定時は不足項目を列挙してユーザーに要求する。
---

# hermes-agent-setup — Hermes Agent + Grok/X Search 情報収集基盤

Hermes Agent（Nous Research 製 OSS エージェント）と xAI Grok API の検索ツール
（`x_search` / `web_search`）を組み合わせ、X やウェブから「仕事に活かせるスキル・
エージェント活用事例」を収集する基盤を **キーを入れれば即動く状態** にするスキル。

ゴールは2つ:
1. **セットアップ**: 必要キーの確認 → 設定テンプレートの差し替え → スモークテスト合格
2. **運用**: 収集クエリ実行 → 要約とスキル化候補の抽出 → ROADMAP 候補リストへの追記

## 前提セットアップ（最重要）

作業開始時は必ずこの表の順に充足を確認する。未設定の項目があれば **勝手に進めず、
不足一覧を提示してユーザー（Ryo）に値の入力を依頼する**。

| # | 必要なもの | 必須度 | 用途 | 入手先 / 導入方法 |
|---|---|---|---|---|
| 1 | `XAI_API_KEY` | **必須**（検索実行に） | Grok API の `x_search` / `web_search` | https://console.x.ai でキー発行 |
| 2 | Hermes Agent 本体 | 任意（常駐運用したい場合） | 収集の常駐実行・Telegram/Discord 等からの操作 | 下記インストールコマンド |
| 3 | Hermes 用 LLM キー（`OPENROUTER_API_KEY` 等いずれか1つ） | #2 を使う場合のみ | Hermes Agent の推論エンジン | Nous Portal / OpenRouter / Anthropic / OpenAI |
| 4 | MCP サーバー設定 | 任意 | Hermes / Claude Code の機能拡張 | 下記「MCP 設定」節 |

補足:
- **このスキルの最小構成は #1 のみ**。`XAI_API_KEY` があれば Claude Code から curl で
  収集ワークフロー全体（収集→要約→ROADMAP 追記）が動く。Hermes Agent は
  「Claude Code のセッション外でも収集を回したい」場合の拡張。
- 同梱テンプレート `templates/env.example` の `REPLACE_ME` を実キーに差し替えて
  `~/.hermes-intel.env` 等に保存し、`source` すれば環境変数の準備は完了。
  **キーの値をリポジトリにコミットしない・チャットログに平文で残さない。**

### キー確認コマンド（値を表示しない）

```bash
for v in XAI_API_KEY OPENROUTER_API_KEY ANTHROPIC_API_KEY OPENAI_API_KEY; do
  eval "val=\${$v:-}"; if [ -n "$val" ]; then echo "$v: set"; else echo "$v: NOT SET"; fi
done
```

### 重要: xAI API の仕様変更（2026年1月）

旧 Live Search API（リクエストの `search_parameters` フィールド）は **2026-01-12 に
廃止済み**。現行は Agent Tools API 方式:
`POST https://api.x.ai/v1/responses` に `tools: [{"type": "x_search"}]` /
`{"type": "web_search"}` を付ける。ネット上の古い記事の `search_parameters` 手順は
使わないこと。モデル名は変わりうるので、エラーが出たら
`curl -sS https://api.x.ai/v1/models -H "Authorization: Bearer $XAI_API_KEY"`
で利用可能モデルを確認し、テンプレート内のモデル名を差し替える。

## セットアップ手順

### Step 1: Grok 検索の疎通（最小構成）

1. 上のキー確認コマンドで `XAI_API_KEY` の有無を確認。未設定なら入手先を伝えて依頼。
2. `templates/env.example` をコピーして値を差し替え、`source` する。
3. スモークテスト（下記）を実行して合格を確認。

### Step 2: Hermes Agent 本体（任意）

公式インストーラで導入する（Linux / macOS / WSL2）:

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
source ~/.bashrc
hermes            # ターミナル UI 起動
```

- 導入先は `~/.hermes/hermes-agent`。プロバイダ/モデル設定は `hermes model`、
  Nous Portal 経由の簡易セットアップは `hermes setup --portal`、個別設定は
  `hermes config set`。
- 第三者 OSS を curl | bash で入れることになるため、**実行前にユーザーへ一言確認**
  し、慎重な環境ではインストールスクリプトの中身を先に見せる。
- Telegram / Discord / Slack 等から使う gateway 設定は本スキルの範囲外。必要なら
  公式ドキュメント（https://hermes-agent.nousresearch.com/docs/）を参照して案内する。

### Step 3: MCP 設定（任意）

- Hermes Agent は MCP サーバー接続に対応している。設定ファイルの正確な形式は
  バージョンで変わるため、**勝手に推測で書かず**
  https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp を確認してから
  設定する。確認できない場合は「どの MCP サーバーを何のためにつなぎたいか」を
  ユーザーにヒアリングした上で、公式ドキュメントの参照を依頼する。
- Claude Code 側に MCP サーバーを足す場合は `claude mcp add` を使う（こちらは
  通常の Claude Code の手順で良い）。

## スモークテスト（セットアップ完了の判定）

同梱の `scripts/smoke_test.sh` を実行するか、以下を手動で実行する。

```bash
# 1. 認証確認（200 でモデル一覧が返れば OK）
curl -sS https://api.x.ai/v1/models \
  -H "Authorization: Bearer $XAI_API_KEY"

# 2. X 検索の最小実行（テンプレートの body を使用）
curl -sS https://api.x.ai/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d @templates/x_search_request.json
```

合格条件: 2 のレスポンスに検索結果を踏まえたテキスト出力が含まれ、HTTP エラーが
ないこと。Hermes Agent を導入した場合は `hermes --help` が通ることも確認する。

## 運用ワークフロー（収集 → 候補化）

### ① セットアップ確認

毎回、キー確認コマンドを先に実行。`XAI_API_KEY` 未設定なら不足一覧を提示して
停止し、代替として agent-reach（下記）を提案する。

### ② 収集クエリ実行

`templates/x_search_request.json`（X 検索）/ `templates/web_search_request.json`
（ウェブ検索）の `REPLACE_ME_QUERY` を差し替え、スモークテスト節の 2 と同じ
curl 形式（`-d @<テンプレートのコピー>`）で `/v1/responses` に POST する。
テンプレート原本は書き換えず、コピーを作って編集する。
定番クエリテンプレート（そのまま使うか、日付だけ「直近7日」等に調整）:

| テーマ | クエリ例 |
|---|---|
| スキルネタ | 「Claude Code のスキル/プラグインの実用的な活用事例を直近1週間の X 投稿から探し、事例ごとに要点と元投稿 URL を挙げて」 |
| 副業 | 「AI エージェントを使った副業・収益化の具体的な取り組み事例を X から集めて。再現可能な手順があるものを優先」 |
| SNS 運用 | 「X アカウント運用で伸びている投稿の勝ちパターン（フック・構成・頻度）を実例付きで集めて」 |
| 技術トレンド | 「MCP サーバーの新しい活用例・話題のリポジトリを X とウェブから集めて」 |

絞り込みが必要なときは tools オブジェクトにオプションを追加できる
（`allowed_x_handles`: 特定アカウントのみ / `from_date`・`to_date`: ISO8601 の期間
指定）。**パラメータ起因のエラーが出たら最小構成 `{"type": "x_search"}` に戻す。**

### ③ 要約とスキル化候補の抽出

レスポンス本文から、次の基準で「スキル化候補」を抽出して表にする:
- Ryo の目的（G1 インターン効率 / G2 副業 / G3 就活実績）のどれかに効くか
- Claude Code のスキルとして再現可能か（手順が具体的か）
- 出典 URL が特定できるか（できないものは候補にしない）

出力形式: `| 候補名 | 概要(1行) | 効く目的 | ソースURL |` の表 + 全体要約 3〜5 行。

### ④ ROADMAP 候補リストへの追記

このリポジトリ（claude-skills）で作業している場合のみ、`ROADMAP.md` 末尾の
「候補リスト」表に追記する:

```markdown
| <今日の日付 YYYY-MM-DD> | <候補名: 1行概要> | <ソースURL> | 候補 |
```

- 表の形式は `| 追加日 | 候補 | ソース | 状態 |`。初期のプレースホルダ行
  `| - | （まだなし） | - | - |` が残っていれば最初の追記時に削除してよい。
- **状態は必ず「候補」で追加**。採択/見送りの判断と実装開始は Ryo が行う。
  勝手に実装に進まない。commit / push もユーザーの指示があるときのみ。
- リポジトリ外のセッションで実行した場合はファイルを触らず、同じ表形式の行を
  チャットに出力して「ROADMAP.md に貼り付けてください」と案内する。

## エッジケースの扱い

| 状況 | 症状 | 対応 |
|---|---|---|
| `XAI_API_KEY` 未設定 | curl が 401 / 変数が空 | 不足一覧を提示して入力を依頼。急ぎなら agent-reach 代替を提案 |
| キーが無効 | HTTP 401 / 403 | コンソール（console.x.ai）でキー再発行を依頼。キーの値は表示させない |
| レート制限 / 残高不足 | HTTP 429 / 402 | 60 秒待って1回だけ再試行。ダメなら残りのクエリを保留し、実行済み分だけで要約を出す |
| モデル名エラー | 404 / model not found | `/v1/models` で一覧を取得し、テンプレートのモデル名を差し替えて再実行 |
| 検索結果ゼロ | 出力に該当情報なし | クエリを一般化（期間を広げる・キーワードを減らす）して1回だけ再試行。それでもゼロなら「ゼロだった」と正直に報告し、候補を捏造しない |
| Hermes インストール失敗 | install.sh がエラー | エラー全文を確認し、Python 3.11+ / ネットワークを疑う。解決しない場合は Hermes なし（最小構成）で運用を続行 |

## 代替経路: xAI キーが無い場合

`XAI_API_KEY` が用意できない場合は、同リポジトリの **agent-reach スキル**
（`plugins/agent-reach`）で代替できる。agent-reach は API キーなしで
YouTube / GitHub / RSS / 一般ウェブを即読め、X はブラウザの cookie エクスポートで
対応する。X のリアルタイム検索品質は Grok の `x_search` が上だが、
「今すぐ無料で動かす」なら agent-reach を先に案内する。

## 同梱ファイル

パスはすべて **この SKILL.md があるディレクトリ基準**（例:
`plugins/hermes-agent-setup/skills/hermes-agent-setup/templates/env.example`）。

- `templates/env.example` — 環境変数テンプレート（`REPLACE_ME` を差し替えるだけ）
- `templates/x_search_request.json` — X 検索リクエスト body（`/v1/responses` 用）
- `templates/web_search_request.json` — ウェブ検索リクエスト body
- `scripts/smoke_test.sh` — キー確認 + API 疎通の一括チェック
