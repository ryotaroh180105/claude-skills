---
name: ai-berkshire
description: バフェット・マンガー・段永平・李録の4大師視点で個別銘柄の価値投資リサーチ（決算分析・企業深掘り・ポートフォリオレビュー・投資チェックリスト）を行いたいときに使う導入・実行ガイド。「この銘柄を価値投資で分析して」「ai-berkshireを使いたい」「決算を四大師視点でレビューして」「投資チェックリストを通して」といった依頼で発動。実体は本家 xbtlin/ai-berkshire のインストールを案内するラッパースキルで、このリポジトリにコードは同梱しない。市場・競合の事業分析は biz-analysis、投資知識の学習は consulting-quiz が担当し、本スキルとは対象領域が別（個別銘柄の投資可否判断専用）。英語キーワード: value investing, Buffett Munger checklist, earnings review, investment research, stock analysis.
---

# ai-berkshire — 価値投資リサーチSkill集

`ai-berkshire`（`github.com/xbtlin/ai-berkshire`、詳細ライセンスは本家 LICENSE 参照）は、
バフェット（財務・estimation）・マンガー（逆張り思考）・段永平（ビジネスモデル）・李録
（長期確実性）の4視点を対立させて個別銘柄を評価する、Claude Code / Codex 両対応の
投資研究Skill集（19個）。

## このリポジトリでの位置づけ（Installer/Wrapper）

コードはこのリポジトリに複製しない。理由:

- 本体は `skills/*.md`（19個）＋ `scripts/` ＋ `data/`（実盤記録・筛选公司データ）から成り、
  本家が独自に更新を続けている。
- 本家は既に Claude Code / Codex 双方のインストール手順を自己完結して提供しており、
  そちらを直接使うのが最新版を保てて安全。

## 既存スキルとの役割境界

- `biz-analysis`: 市場全体・競合の事業分析（3C/TAM-SAM-SOM等）が対象。個別銘柄の投資可否判断は扱わない。
- `consulting-quiz`: 投資・会計知識の学習クイズが対象。実際の銘柄分析は行わない。
- 個別銘柄を「買う/買わない」まで踏み込む価値投資判断は `ai-berkshire` の専管。

## 導入手順

Claude Code から本家リポジトリを直接 clone してSkillとして使う（本家は marketplace 化していない
ため `/plugin install` ではなく手動配置）:

```bash
git clone https://github.com/xbtlin/ai-berkshire.git
# Claude Code に読み込ませる場合、対象プロジェクト直下に配置するか
# 個別 skill を ~/.claude/skills/ にコピーする
cp ai-berkshire/skills/*.md ~/.claude/skills/  # または任意のプロジェクトへ
```

`AGENTS.md`（Codex向け）と `CLAUDE.md`（Claude Code向け）が本家ルートにあるため、
分析対象プロジェクトの `CLAUDE.md` に取り込みたい場合はそちらも参照する。

## 使い方（主要Skill）

- `investment-research` — 単一銘柄の深掘り投資リサーチ（フルフロー）
- `investment-team` — 4大師視点を並列実行し対立点を可視化
- `earnings-review` / `earnings-team` — 決算レビュー
- `quality-screen` — 初筛（軽量スクリーニング、コスト重視）
- `news-pulse` — 株価変動要因の即時分析
- `investment-checklist` — 鏡子テスト等の投資チェックリスト
- `portfolio-review` — 保有ポートフォリオの棚卸し

深いリサーチ系Skillはトークン消費が大きい設計（複数ラウンド調査・多Agent統合）。
コストを抑えたい場合は `quality-screen` → `news-pulse` → 必要なら `investment-research` の順で
段階的に使う（本家推奨のワークフロー）。

## 注意点

- 実盤運用の免責事項どおり、出力は投資助言ではなく分析フレームワークの適用結果として扱う。
- `data/` `实盘记录/` `筛选公司/` 等は本家が持つ運用データであり、このリポジトリには持ち込まない。
- 個人利用専用の導入ガイド。本家リポジトリの信頼性・継続性はこのリポジトリでは保証しない。
- 発動時、まず `~/.claude/skills/` 等に該当Skillが既に配置済みかを確認し、未導入なら
  先に導入手順を案内してから分析に進む。

---
出典: https://github.com/xbtlin/ai-berkshire
