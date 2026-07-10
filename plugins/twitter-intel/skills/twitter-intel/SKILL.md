---
name: twitter-intel
description: X（Twitter）から仕事に活かせる情報を収集・要約するスキル。「Xで〜を調べて」「スキルネタを集めて」「バズ投稿を分析して」「◯◯アカウントの発信を追って」「X運用の勝ちパターンを調査して」といった依頼、または sns-ops-team のリサーチ工程から呼ばれたときに使う。claude-skillsリポジトリで作業中（gitがある）ならhermes-relayを最優先、それ以外はxAI x_search / agent-reach / X API v2のうち利用可能な経路を自動選択し、出典URL付きレポートとROADMAP候補リストを出力する。
---

# twitter-intel — X（Twitter）情報収集・要約

X から「仕事に活かせる情報」を集めて要約するスキル。主な用途は3つ:

1. **スキルネタ収集**: Claude スキル / AI エージェント活用事例を集めて ROADMAP 候補化
2. **SNS運用リサーチ**: 勝ちパターン・バズ構造の調査（sns-ops-team のリサーチ工程で利用）
3. **定点観測**: 特定テーマ・特定アカウントの発信を継続的に追う

鉄則: **出典 URL の無い情報は成果物に載せない。捏造は絶対にしない。**

## 前提セットアップ（経路0、またはどれか1つで動く）

**経路0（hermes-relay）が使えるなら常にそれを使う**（CLAUDE.mdの常時適用ルール
「調査は hermes-relay で実行する」に従う）。経路0が使えない環境（このリポジトリの
外、git push権限が無いセッション等）でのみ、経路①〜③の直接API方式にフォール
バックする。

| # | 経路 | 必要なもの | 入手先 / 導入方法 | 品質 |
|---|---|---|---|---|
| 0 | **hermes-relay（最優先）** | `claude-skills` リポジトリへの git push 権限のみ | 詳細は `plugins/hermes-x-search/skills/hermes-x-search/SKILL.md` / `CLAUDE.md`。APIキー・CLI導入・cookie設定は一切不要 | 最高（Grokのx_search、GitHub Actions実行、追加課金なし） |
| 1 | xAI x_search（直接） | `XAI_API_KEY` | https://console.x.ai でキー発行 | 最高（検索+要約を Grok が実行） |
| 2 | agent-reach | `agent-reach` CLI + X 用 cookie | agent-reach スキル（`plugins/agent-reach`）の手順で導入 | 中（cookie 必須、スクレイピング系） |
| 3 | X API v2 | `X_BEARER_TOKEN` | https://developer.x.com でアプリ作成 | 中（直近7日のみ、無料枠は低レート） |

## 収集経路の自動選択（このスキルの核）

作業開始時に **必ず** 以下の判定を上から順に実行し、最初に合格した経路を採用する。
経路0(hermes-relay)が使えるかどうかを最初に確認すること — 「XAI_API_KEYが無いから
セットアップが必要」と即断しない。複数使える場合も優先順位（0 > ① > ② > ③）に
従う。採用した経路をユーザーに1行で報告してから収集に入る
（例:「経路0 hermes-relay を使用します」）。

### 判定コマンド（値は表示しない）

```bash
# 経路0: hermes-relayが使えるか（claude-skillsリポジトリにgit pushできるか）
if git -C . remote -v 2>/dev/null | grep -qi "claude-skills"; then
  git ls-remote --exit-code origin hermes-relay >/dev/null 2>&1 \
    && echo "route0 hermes-relay: OK" || echo "route0 hermes-relay: NG (branch取得失敗)"
else
  echo "route0 hermes-relay: NG (claude-skillsリポジトリ外、またはgit未接続)"
fi

# 経路①: xAI API キー
[ -n "${XAI_API_KEY:-}" ] && echo "route1 xai: OK" || echo "route1 xai: NG"

# 経路②: agent-reach が導入済みか（コマンド存在 + doctor で Twitter/X backend が ready か）
if command -v agent-reach >/dev/null 2>&1; then
  agent-reach doctor 2>&1 | grep -iq "twitter.*\(ready\|active\|ok\)" \
    && echo "route2 agent-reach: OK" || echo "route2 agent-reach: NG (X cookie 未設定)"
else
  echo "route2 agent-reach: NG (未インストール)"
fi

# 経路③: X API Bearer Token
[ -n "${X_BEARER_TOKEN:-}" ] && echo "route3 x-api: OK" || echo "route3 x-api: NG"
```

注意: `agent-reach doctor` の出力形式はバージョンで変わりうる。grep が不合格でも
doctor の出力に X/Twitter が使用可能と読める記載があれば OK と判断してよい。
迷ったら軽いテスト検索を1回実行して動作確認する。

### 経路0: hermes-relay（最優先・既定）

`plugins/hermes-x-search/skills/hermes-x-search/SKILL.md` の「Automated relay」節の
手順どおり、`hermes-relay` ブランチにクエリファイルをpushするだけでよい。
APIキー発行・CLIインストール・cookie設定は一切不要。GitHub Actionsが自動実行し、
数十秒〜数分で結果が返る。クエリの書式（出典URL必須・未確認事項セクション必須・
日本語指定）は本スキルの「収集テンプレート」節をそのままプロンプト本文に使う。

git push権限が無い環境（素のclaude.aiチャット等）では経路0は使えない。その場合は
「Claude Code on the web（claude.ai/code）でこのリポジトリを開いたセッションから
実行する必要がある」とユーザーに伝え、経路①〜③のセットアップを代替として提示する。

### 経路①: xAI x_search（直接・経路0が使えない場合のフォールバック）

hermes-agent-setup スキル（`plugins/hermes-agent-setup`）と同じ Agent Tools API 方式。
旧 Live Search API（`search_parameters`）は 2026-01-12 廃止済みなので使わない。

```bash
curl -sS https://api.x.ai/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d @<リクエストbodyファイル>
```

body は hermes-agent-setup 同梱のテンプレート
`plugins/hermes-agent-setup/skills/hermes-agent-setup/templates/x_search_request.json`
をコピーして `REPLACE_ME_QUERY` を差し替える（原本は書き換えない）。テンプレートが
見つからない場合は最小構成で自作する:

```json
{"model": "<`/v1/models` で確認したモデル名>",
 "input": "<収集クエリ（自然文の指示）>",
 "tools": [{"type": "x_search"}]}
```

モデル名エラー（404）が出たら `GET https://api.x.ai/v1/models` で一覧を確認して差し替え。
アカウント限定は tools オプションの `allowed_x_handles`、期間指定は `from_date` /
`to_date`（ISO8601）。パラメータ起因のエラーが出たら最小構成 `{"type": "x_search"}` に戻す。

### 経路②: agent-reach

agent-reach スキルの使い方に従い、自然言語で依頼するだけでよい（router が backend を選ぶ）:

```bash
agent-reach "Xで「Claude Code skill」の直近1週間の話題投稿を検索して、投稿URL付きで一覧にして"
```

- X はスクレイピング系のため、サイト変更で壊れることがある。エラー時は
  `agent-reach doctor` で状態を確認し、直らなければ次の経路に降格する。
- 個別ツイートの読み取りは URL を渡す（例: `agent-reach "このツイートの内容を教えて <URL>"`）。

### 経路③: X API v2 recent search（直近7日）

```bash
curl -sS -G "https://api.x.com/2/tweets/search/recent" \
  -H "Authorization: Bearer $X_BEARER_TOKEN" \
  --data-urlencode 'query=("Claude Code" skill) -is:retweet' \
  --data-urlencode 'max_results=25' \
  --data-urlencode 'tweet.fields=created_at,public_metrics,text' \
  --data-urlencode 'expansions=author_id' \
  --data-urlencode 'user.fields=username'
```

- 出典 URL は `https://x.com/<username>/status/<tweet id>` で組み立てる
  （username は `includes.users` から引く）。
- 特定アカウントの定点観測は `query=from:<handle> -is:retweet`。
- recent search は **直近7日分のみ**。それより古い調査依頼が来たら制約を伝え、
  経路①（xAI）への切り替えか期間の変更を提案する。
- 429（レート制限）が出たら 60 秒待って1回だけ再試行。ダメなら取得済み分で要約する。

### 経路④（縮退）: 全経路が使用不可の場合

1. まず経路0（hermes-relay）が本当に使えないか再確認する（git push権限の有無）。
   使えるなら経路0を優先し、①〜③のセットアップを依頼する前にそちらを案内する。
   経路0も使えない場合のみ「前提セットアップ」の表を提示し、**どれか1つ** の用意を
   依頼する（最短は `XAI_API_KEY` の発行）。
2. ユーザーが「今すぐ何か欲しい」場合のみ、WebSearch による限定的な代替を提案する。
   ただし次を必ず明記する:
   - `site:x.com` 等の検索は **精度が低く、取りこぼし・古い結果が多い**。
     X の生の検索の代わりにはならない。
   - nitter 系ミラーは **不安定なので使わない**。
   - WebSearch で拾えるのは主に「X の投稿を引用したブログ・まとめ記事」。
     その場合も出典はたどれる範囲で元ポストの URL を優先して記載する。
3. 縮退モードで作った成果物には冒頭に「WebSearch による限定調査（X 直接検索ではない）」
   と注記する。ROADMAP 候補化は元ポスト URL を特定できたものに限る。

## 収集テンプレート（テーマ別クエリ例）

日本語圏の事例は日本語で、世界の最新事例・技術情報は英語で検索する。
**両方が欲しいテーマ（スキルネタ・技術トレンド）は日英セットで実行する**のが既定。
SNS運用系は運用対象アカウントの言語（通常は日本語）に合わせる。

| テーマ | 日本語クエリ例 | 英語クエリ例 |
|---|---|---|
| スキルネタ | Claude Code スキル 活用事例 / Claude エージェント 自動化 事例 | Claude Code skill workflow / Claude agent use case |
| AI 副業 | AI エージェント 副業 収益化 / Claude 案件 効率化 | AI agent side hustle / making money with AI agents |
| X 運用 | X運用 フォロワー増加 事例 / X アルゴリズム 伸びた投稿 | (通常は日本語のみで可) |
| バズ構造 | バズった ポスト 構成 フック / インプレッション 伸びた 理由 | viral post hook structure |
| 技術トレンド | MCP サーバー 活用 / Claude 新機能 | MCP server / Claude Code tips |

経路① では上記キーワードを含む自然文の指示（「〜を直近1週間の X 投稿から探し、
事例ごとに要点と元投稿 URL を挙げて」）に、経路③ では検索演算子付きクエリ
（`-is:retweet`、必要なら `lang:ja` / `lang:en`）に変換して使う。

## お手本アカウント起点リサーチ（追加の収集手法）

キーワード検索より「勝ちパターンを持つ特定アカウント」を起点にした方が精度が高い場合に使う。
「◯◯さんの発信を参考にしたい」「お手本アカウントから伸びる構造を学びたい」で発動。

1. **起点アカウント特定**: ユーザーが指名したアカウント、または対象テーマで実績のある
   アカウントを1〜3件特定する。
2. **伸びた投稿のピックアップ**: 起点アカウントの投稿のうち、インプレッション・エンゲージメントが
   相対的に高いものを日英クエリ例の要領で10〜15件抽出する。
3. **バズ構造分析**: 抽出した投稿を「なぜ刺さるか」列でフック/構成/CTAに分解し、
   共通パターンを見つける（出力フォーマットの収集結果表をそのまま使う）。

出典URLが取れない投稿は分析対象に含めない（鉄則どおり）。

## 出力フォーマット

### 収集結果表（全ユースケース共通）

```markdown
| 要点 | なぜ刺さるか | 出典URL | 収集日 |
|---|---|---|---|
| <投稿の要点1行> | <Ryo の目的 G1/G2/G3 やテーマにどう効くか> | https://x.com/... | YYYY-MM-DD |
```

+ 末尾に全体要約 3〜5 行（傾向・共通パターン・次のアクション案）。
バズ構造分析のときは「なぜ刺さるか」列にフック/構成/CTA の分解を書く。

### スキル化候補 → ROADMAP 候補リストへの追記

収集結果のうち「Claude Code スキルとして再現可能」かつ「出典 URL が特定できる」
ものだけを候補化し、claude-skills リポジトリで作業している場合は `ROADMAP.md` 末尾の
候補リスト表（`| 追加日 | 候補 | ソース | 状態 |`）に追記する:

```markdown
| <今日の日付 YYYY-MM-DD> | <候補名: 1行概要> | <ソースURL> | 候補 |
```

- **状態は必ず「候補」固定**。採択・実装開始の判断は Ryo が行う。勝手に実装しない。
- プレースホルダ行 `| - | （まだなし） | - | - |` が残っていれば最初の追記時に削除してよい。
- リポジトリ外のセッションではファイルを触らず、同じ形式の行をチャットに出力して
  「ROADMAP.md に貼り付けてください」と案内する。
- commit / push はユーザーの指示があるときのみ。

## sns-ops-team との連携

sns-ops-team のリサーチ工程（リサーチ担当エージェント）から呼ばれた場合:

1. 対象アカウントの `sns/<アカウント名>/sns-strategy.md` の発信領域・ペルソナ・トーンを
   読み、**戦略ファイルのテーマに沿ったクエリ** で収集する（汎用クエリで済ませない）。
   戦略ファイルのパスが渡されていない場合は、呼び出しプロンプトに埋め込まれた
   テーマ（発信領域）をそのまま使う。どちらも無ければテーマを呼び出し元に確認する。
2. 成果物は **調査レポート（上記の収集結果表 + 要約）のみ** を呼び出し元に返す。
   **`post-queue.md` には絶対に書き込まない**（投稿案の作成・キュー追記は
   sns-ops-team 側の執筆・レビュー工程の仕事）。
3. ROADMAP 候補化もこのモードでは行わない（依頼が SNS 運用リサーチのため）。
   スキルネタを偶然見つけたら、レポート末尾に「参考: スキル化候補になりそう」と
   1行添えるだけにとどめる。

## エッジケースの扱い

| 状況 | 対応 |
|---|---|
| 全経路が使用不可 | 経路④の手順どおり: セットアップ表を提示して依頼 → 希望があれば WebSearch 縮退（注記必須）。無言で WebSearch に進まない |
| 検索結果ゼロ | クエリを一般化（期間を広げる・キーワードを減らす・日英を切り替える）して1回だけ再試行。それでもゼロなら「ゼロだった」と正直に報告し、結果を捏造しない |
| 日本語/英語の使い分けに迷う | 既定は日英セット（スキルネタ・技術トレンド）。SNS運用系は運用アカウントの言語のみ。ユーザーが言語を指定したらそれに従う |
| 採用経路が途中で失敗（401/403/429/スクレイピング破損） | 認証エラーはキー再発行を依頼（値は表示しない）。レート制限は 60 秒後に1回再試行。復旧しなければ次順位の経路に降格し、降格したことを報告する |
| 直近7日より古い期間の依頼で経路③しか無い | recent search の制約を伝え、期間変更か経路①のセットアップを提案する |
| 出典 URL がリンク切れ・特定不能 | その項目は表に載せない、または「出典未特定」と明記して候補化対象から外す |

## 関連スキル

- **hermes-x-search**: 経路0（hermes-relay）の実行手順・クエリ書式はあちらが正。
  `claude-skills` リポジトリで作業中は基本的にこちらに誘導する。
- **hermes-agent-setup**: 経路①（xAI直APIキー）のセットアップ・テンプレート・
  Hermes Agent常駐運用は あちらが担当。経路0が使えない環境でのみ誘導する。
- **agent-reach**: 経路②の導入手順とプラットフォーム別の注意はあちらを参照。
- **sns-ops-team**: リサーチ工程の下請けとして本スキルが呼ばれる（上記連携ルール）。
