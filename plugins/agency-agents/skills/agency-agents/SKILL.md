---
name: agency-agents
description: フロントエンド/バックエンド/マーケティング/セールス/財務/法務など業種別の専門家人格を持つAIサブエージェント（agency-agents、51体）を導入・呼び出したいときに使う導入・実行ガイド。「agency-agentsを使いたい」「フロントエンド専門のエージェントを立てて」「◯◯部門のペルソナで対応して」といった依頼で発動。実体は本家 msitarzewski/agency-agents のインストールを案内するラッパースキルで、このリポジトリにコードは同梱しない。このリポジトリ固有の意思決定ゲート用サブエージェント（red-team等）とは対象が異なり、agency-agentsは他プロジェクトでも使う汎用の業務分野別実務ペルソナ集。英語キーワード: agency agents, subagent personas, frontend developer agent, marketing agent, specialized AI team.
---

# agency-agents — 業務分野別AIサブエージェント人格集

`agency-agents`（`github.com/msitarzewski/agency-agents`、MITライセンス）は、
フロントエンド開発・バックエンド・マーケティング・セールス・財務・法務・GIS・
ゲーム開発など17分野・51体の専門家人格を持つサブエージェント定義集（`.claude/agents/`
形式のMarkdown）。各エージェントは固有の人格・進め方・成果物基準を持つ。

## このリポジトリでの位置づけ（Installer/Wrapper）

コードはこのリポジトリに複製しない。理由:

- 本体は分野別ディレクトリ（`engineering/` `marketing/` `finance/` 等17分野）＋
  `scripts/install.sh`（11ツール対応のインストーラ）から成り、本家が更新を続けている。
- ネイティブアプリ版（`agencyagents.app`）も並行提供されており、GUIでの選択インストールが
  最も簡単。

## 既存スキルとの役割境界

- 本リポジトリの `red-team` 等のサブエージェントは、このリポジトリの設計書・marketplace.json
  追記に対する批判的レビュー専用（`.claude/agents/` に個別配置済み、他プロジェクトには持ち出さない）。
- `agency-agents` は特定プロジェクトに紐付かない汎用の業務分野別実務ペルソナで、
  他プロジェクトでの実装・マーケ・セールス等の実務作業に使う。両者は対象プロジェクトが異なるため
  重複しない。

## 導入手順

Claude Code用に全エージェントをインストール:

```bash
git clone https://github.com/msitarzewski/agency-agents.git
cd agency-agents
./scripts/install.sh --tool claude-code
```

分野を絞る場合:

```bash
cp agency-agents/engineering/*.md ~/.claude/agents/   # 例: エンジニアリング部門のみ
```

または `agencyagents.app`（macOS/Linux/Windowsネイティブアプリ、`brew install --cask
msitarzewski/agency-agents/agency-agents`）でGUIからインストール・更新管理する。

## 使い方

インストール後、Claude Codeセッション内で該当エージェントを名指しして呼び出す:

```
Frontend Developer モードで React コンポーネントを作って
Reddit コミュニティ担当のペルソナで投稿文をレビューして
```

分野一覧（`divisions.json`）: academic / design / engineering / finance /
game-development / gis / healthcare / marketing / paid-media / product /
project-management / sales / security / spatial-computing / specialized /
support / testing

## 注意点

- コードは一切ここに同梱していない。実行は必ず本家 `install.sh` またはアプリ経由。
- `--link`（シンボリックリンク、本家更新が自動反映）と `--path`（配置先上書き）オプションもある。
- 個人利用専用の導入ガイド。本家リポジトリの信頼性・継続性はこのリポジトリでは保証しない。
- 発動時、まず `~/.claude/agents/` 等に該当エージェントが既に配置済みかを確認し、未導入なら
  先に導入手順を案内してから呼び出しに進む。

---
出典: https://github.com/msitarzewski/agency-agents（MITライセンス）
