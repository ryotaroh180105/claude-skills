---
name: github-trends
description: GitHub のトレンドページとリポジトリ検索から「仕事に活かせそうなスキル/エージェント系リポジトリ」を収集し、3行要約付きの候補として ROADMAP.md の候補リストに追記するスキル。「GitHubトレンドを取り込んで」「今週のトレンド収集」「スキルネタを探して」「Claudeスキル系のリポジトリを調べて」「候補リストに追加して」「トレンド収集を定期実行したい」などの依頼で使う。収集と候補化まで — 採択判断は必ずユーザーが行い、実装には進めない。
---

# GitHub Trends — トレンド収集 → 候補リスト化

GitHub のトレンドとテーマ検索から「スキル化して仕事に活かせそうなリポジトリ」を拾い、
評価・3行要約して ROADMAP.md の候補リストに追記するまでを行うスキル。

## 大原則（最重要）

- **このスキルの出口は「候補リストへの追記」まで。** 採択/見送りの判断は必ずユーザー（Ryo）が行う。
  候補が良さそうに見えても、**勝手にスキルの実装・インストール・クローンまで進めない。**
- 状態列は必ず「候補」で追記する。「採択」「実装中」に変更するのはユーザーの指示があったときだけ。

## 前提セットアップ

必須の API キーはなし。利用可能なものを上から順に自動選択する。

| 手段 | 必要なもの | 備考 |
|---|---|---|
| GitHub MCP（`mcp__github__search_repositories`） | MCP 接続済みであること | 検索はこれを最優先。認証済みなのでレート制限が緩い |
| WebFetch（github.com/trending） | なし | トレンドページ取得はこれ一択（trending に公式 API はない） |
| WebFetch（api.github.com 認証なし） | なし | MCP が無いときの検索フォールバック。**60 リクエスト/時の制限あり** |

セッション開始時に GitHub MCP ツールが見えるか確認し、無ければ WebFetch フォールバックを使う旨を一言添える。

## ワークフロー

### Step 0: 収集条件の確認

依頼に指定が無ければデフォルトで進める（毎回質問しない）:

- **期間**: weekly（週次取り込みの想定）
- **テーマ**: ①Claude スキル/プラグイン ②AI エージェント ③全体トレンド（言語不問）
- **件数**: 候補として出すのは合計 3〜7 件（多すぎると採択判断の負荷になる）

### Step 1: トレンドページの取得（WebFetch）

`github.com/trending` を WebFetch で取得する。URL パターン（動作確認済み）:

| 目的 | URL |
|---|---|
| 全体・週間 | `https://github.com/trending?since=weekly` |
| 全体・日間 / 月間 | `https://github.com/trending?since=daily` / `?since=monthly` |
| 言語別（例: Python 日間） | `https://github.com/trending/python?since=daily` |
| 言語別（例: TypeScript 週間） | `https://github.com/trending/typescript?since=weekly` |

WebFetch の prompt には抽出項目を明示する。例:

> 「このページのトレンドリポジトリを上位10件、owner/name・説明・言語・合計スター数・期間内のスター増分の形式でリストして」

### Step 2: テーマ検索

**GitHub MCP がある場合**（優先）— `mcp__github__search_repositories` を使う。
動作確認済みのクエリ例（`pushed:` の日付は実行日から計算して差し替える。下記は 2026-07-04 実行時の例）:

```
# Claude スキル系（sort=stars, order=desc, perPage=10）
claude skills in:name,description,topics stars:>100 pushed:>2026-06-01

# Claude Code プラグイン系
"claude code" plugin stars:>100 pushed:>2026-06-01

# AI エージェント系・直近1週間に更新されたもの（sort=updated）
AI agent in:name,description stars:>500 pushed:>2026-06-27
```

日付の計算例: `date -u -d '30 days ago' +%Y-%m-%d`（テーマ検索は 30 日、直近更新は 7 日が目安）。

**GitHub MCP が無い場合** — WebFetch で認証なし API を叩く（動作確認済み）。
クエリは URL エンコードが必要（スペース→`%20`、`"`→`%22`、`>`→`%3E`）:

```
https://api.github.com/search/repositories?q=%22claude%20code%22%20plugin%20stars:%3E100%20pushed:%3E2026-06-01&sort=stars&order=desc&per_page=5
```

WebFetch の prompt 例: 「これは GitHub API の JSON。total_count と各 item の full_name / stargazers_count / description を列挙して。エラーなら本文を引用して」

### Step 3: 評価・スコアリング

収集したリポジトリを次の 3 軸で評価し、見込みのないものは落とす:

1. **仕事への活用可能性** — どの目的に効くか（G1: インターン効率化 / G2: 副業・SNS運用 / G3: 就活ネタ）。どれにも紐付かないものは候補にしない
2. **スキル化のしやすさ** — SKILL.md に落とせる手順・CLI・API があるか。単なるライブラリやデモは低評価
3. **勢い** — スター総数と期間内の伸び。伸びているものは「今話題にできる」= G3 でも価値がある

各候補は **3 行要約** にまとめる:

```
- **owner/repo**（★スター数, 言語）[G1/G2/G3]
  - 何ができる: <機能を1行>
  - なぜ刺さる: <どの目的にどう効くか1行>
  - スキル化するなら: <作る SKILL の内容を1行>
```

### Step 4: 候補リストへの追記

追記先はリポジトリの `ROADMAP.md` 末尾「候補リスト（収集したスキルネタ置き場）」の表:

```
| 追加日 | 候補 | ソース | 状態 |
```

手順:

1. **重複チェック**: 候補の repo 名を ROADMAP.md 全体（候補リスト表 + スキル一覧）に対して Grep する。
   既出なら追記せず「既出のためスキップ」と報告する
2. 1 候補 1 行で追記する。**状態は必ず「候補」**:

```markdown
| 2026-07-04 | teng-lin/notebooklm-py — NotebookLM を CLI/skill から操作 [G2] | GitHub検索 "claude skills" | 候補 |
```

   - 追加日: 実行日（YYYY-MM-DD）
   - 候補: `owner/repo — 1行説明 [目的タグ]`（3行要約の全文はチャットに出し、表は1行に圧縮）
   - ソース: `trending(weekly)` / `GitHub検索 "<クエリ概要>"` など出どころが追える書き方
   - 表にプレースホルダ行（`| - | （まだなし） | - | - |`）が残っていたら、最初の追記時にその行を削除する
3. 追記後、チャットに 3 行要約の一覧を出して「採択判断をお願いします」で締める

**リポジトリ外セッションの場合**（ROADMAP.md がカレントに無い）: ファイル編集はせず、
上記の表形式 + 3 行要約を **チャット出力にフォールバック** し、「claude-skills リポジトリのセッションで
ROADMAP.md に貼り付けてください」と案内する。勝手に別ファイルを作らない。

## 定期実行（週次）の設定

Claude Code のスケジュールトリガー（Routine）で週次実行できる。ユーザーが「定期実行したい」と言ったら:

1. `mcp__Claude_Code_Remote__create_trigger` を呼ぶ。設定例:
   - `name`: `github-trends-weekly`
   - `cron_expression`: `0 0 * * 1`（毎週月曜。タイムゾーンは環境依存のため、作成後に返る `next_run_at` を確認して JST 朝になるよう調整する）
   - `prompt`: 「github-trends スキルで今週の GitHub トレンドとテーマ検索（Claude スキル/AI エージェント）を収集し、候補を ROADMAP.md の候補リストに追記して。採択判断は私がやるので追記まで」
2. デフォルトは現在セッションに発火する。毎回まっさらな状態で走らせたいときだけ `create_new_session_on_fire: true` を使う（その場合 prompt は単独で完結する文面にする）
3. 確認・停止は `list_triggers` / `update_trigger`（`enabled: false`）/ `delete_trigger`

トリガー系ツールが見えない環境では、代わりに「週1回このスキルを手動で呼ぶ」運用を案内する。

## エッジケース

- **収集結果ゼロの週**: フィルタ後に候補が 1 件も残らない場合、ROADMAP.md には何も追記しない。
  チャットで「今週は基準（stars/pushed/目的タグ）を満たす新規候補なし。使用クエリ: …」と報告する。
  空行やダミー行を表に入れない
- **重複候補**: 候補リスト・実装済みスキル一覧のどちらかに既出のリポジトリは追記しない。
  「既出: owner/repo（候補リストに YYYY-MM-DD 追加済み）」とだけ報告する
- **レート制限（認証なし API）**: 60 リクエスト/時。応答に `API rate limit exceeded` が返ったら、
  ①GitHub MCP があればそちらへ切替 ②無ければクエリを 1〜2 本に絞り、残りは次回に回す旨を報告する。
  リトライ連打はしない
- **trending ページの取得失敗**: WebFetch がエラー/空を返したら 1 回だけ再試行し、ダメなら
  テーマ検索（Step 2）だけで続行して「trending は今回取得不可」と明記する
- **検索結果の鮮度**: `stargazers_count` は取得時点の値。表やチャットに載せる数値には取得日を添える

## やらないこと

- 候補リポジトリの clone / インストール / スキル実装（採択後に `repo-skill-creator` スキルで別途行う）
- ROADMAP.md の候補リスト表以外の箇所（ステータス表・バッチ計画など）の編集
- 状態を「候補」以外にして追記すること
