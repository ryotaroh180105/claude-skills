---
name: last30days
description: Reddit・X(Twitter)・YouTube・TikTok・Instagram・Hacker News・Polymarket・GitHub・Bluesky・Pinterest・Webを横断し、直近30日の実際のエンゲージメント（アップボート・いいね・視聴数・賭け金）で重要度を判定してトピックの「今何が語られているか」を調べたいときに使う導入・実行ガイド。「◯◯について最近のXやRedditの反応を調べて」「last30daysを使いたい」「競合の話題を横断的にリサーチして」「トレンドを複数プラットフォームで確認したい」といった依頼で発動。実体は本家 mvanhorn/last30days-skill のインストールを案内するラッパースキルで、このリポジトリにコードは同梱しない。英語キーワード: last30days, cross-platform research, engagement ranking, Reddit Twitter YouTube TikTok search, social listening.
---

# last30days — 直近30日クロスプラットフォーム・リサーチ

`last30days`（`github.com/mvanhorn/last30days-skill`、MITライセンス）は、単一トピックについて
Reddit・X・YouTube・TikTok・Instagram・Hacker News・Polymarket・GitHub・Bluesky・Pinterest・Web を
並列検索し、編集者の選別ではなく**実際のエンゲージメント量**（アップボート数・いいね数・視聴数・
Polymarketの賭け金）でランキングして1本のブリーフに統合する Claude Code スキルである。

## このリポジトリでの位置づけ（Installer/Wrapper）

このスキルは last30days のコードをこのリポジトリに複製しない。理由:

- 本体は Python 3.12+ の巨大なエンジン（`skills/last30days/scripts/lib/` 配下に
  reddit / x / youtube / tiktok / instagram / polymarket / github などのバックエンドが
  40ファイル超）＋ Go 製 MCP サーバー＋ブラウザCookie抽出（Chrome/Safari/Firefox/Edge）を含み、
  頻繁にリリースされている（確認時点で v3.11.1）。
- 本家は既に Claude Code 用マーケットプレイスとして自己完結しており（`.claude-plugin/marketplace.json`
  に plugin `last30days` を登録済み）、素直にそちらを直接インストールするのが最も安全で
  最新版を保てる。
- 部分的にコピーすると本家の更新に追従できず、動作保証もできないため、このスキルは
  「導入手順の案内」と「呼び出し方の整理」に徹する。

## 前提セットアップ

| 種別 | 名前 | 用途 | 未設定時の挙動 |
|---|---|---|---|
| ランタイム | Python 3.12+ | last30days 本体の実行環境 | インストールスクリプトが要求。未導入ならユーザーに導入を依頼 |
| 任意 | `yt-dlp`（`brew install yt-dlp` 等） | YouTube 動画の文字起こし取得 | 未導入でも動くが YouTube ソースの深度が下がる |
| 任意 | Reddit / Hacker News / Polymarket / GitHub | 追加設定なしで検索可能 | キー不要（無料枠） |
| 任意 | X/Twitter 用ブラウザCookie または `XQUIK_API_KEY` / `XAI_API_KEY` | X検索の精度向上 | 未設定でも動くが X カバレッジが弱まる |
| 任意 | ScrapeCreators キー | TikTok/Instagram/Threads/Pinterest | 未設定ならこれらのソースはスキップ |
| 任意 | Perplexity（Sonar）または OpenRouter フォールバック | Web横断検索の補強 | 未設定ならWeb専用モードに縮退 |
| 任意 | Brave Search キー | Web検索の補強（月2000回まで無料） | 未設定でも動作 |

いずれのキーも `.env` または macOS Keychain 経由で本家が管理する。未設定でも Reddit / Hacker News /
Polymarket / GitHub / Web だけで動作は継続する（本家は「キー0個でも動く。多いほど精度が上がる」設計）。
ユーザーがキーの要否を尋ねたら、この表を見せて「まず無設定で試し、カバレッジ不足を感じたソースだけ
追加する」と案内する。

## 導入手順

Claude Code から本家マーケットプレイスを追加してインストールする:

```
/plugin marketplace add mvanhorn/last30days-skill
/plugin install last30days@last30days-skill
```

インストール後、初回実行時に本家のセットアップウィザードが Python 依存関係の確認・任意APIキーの
入力を対話的に案内する。`/plugin list` で `last30days` が enabled になっていることを確認する。

その他の導入経路（Claude Code 以外での利用や、ユーザーが既にそちらを使っている場合のみ案内）:

- Agent Skills 対応ホスト全般: `npx skills add mvanhorn/last30days-skill -g`
- Claude Desktop: リリースページから `.mcpb` バンドルをダウンロードして Settings にドラッグ
- claude.ai（web）: `last30days.skill` を Settings > Capabilities > Skills からアップロード

## 使い方

インストール後は `/last30days` コマンドとしてそのまま呼び出せる:

```
/last30days Peter Steinberger
/last30days OpenAI --competitors
/last30days Universal Epic Universe --emit=html
```

- 単純なトピック名 → 一般リサーチ（GENERAL）
- `--competitors` → 競合比較モード
- `A vs B` 形式のクエリ → 並列比較（COMPARISON）
- `--emit=html` → Slack/メール/Notion 共有向けのHTMLブリーフを出力（ダークモード・印刷対応）

出力は根拠URL付きの引用と「Best Takes」（バズった/秀逸な投稿の抜粋）、ELI5モードなどを含む
本家独自のフォーマットに従う。詳細な出力仕様（LAWs等）はユーザーがインストール後に本家
`SKILL.md` を直接参照する（本リポジトリには複製しない）。

## 注意点

- **コードは一切ここに同梱していない**。実行は必ず本家プラグインのインストール経由で行う。
  このリポジトリの `plugins/last30days/` を直接動かそうとしても何も実行できない。
- **ブラウザCookie抽出機能がある**（X認証の簡略化のため、Chrome/Safari/Firefox/Edgeの
  Cookieデータベースをローカルでのみ読む）。ネットワーク送信コードは含まず、外部への
  データ送信は確認していないが、企業端末や共有端末で使う場合はユーザー自身に本家
  `CONFIGURATION.md` の該当箇所を確認してもらう。
- 本家は頻繁に更新される（確認時点でv3.11.1）。`/plugin marketplace update
  last30days-skill` で追従する。

---
出典: https://github.com/mvanhorn/last30days-skill（MITライセンス）
