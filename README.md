# claude-skills

Claude Code / Claude.ai で使う Skill 集を管理するリポジトリ。

**目的**: ①インターン業務の効率と質を上げる ②個人開発・副業（SNS運用・ウェブ系）で稼ぐ ③就活で話せる実績を作る。
各スキルの要件定義・目的タグ（G1/G2/G3）は [docs/skill-requirements.md](docs/skill-requirements.md)、優先順位と運用方針は [ROADMAP.md](ROADMAP.md) を参照。

```
claude-skills/
├── .claude-plugin/
│   └── marketplace.json          # Plugin Marketplace 定義
├── plugins/
│   └── <plugin-name>/
│       ├── .claude-plugin/
│       │   └── plugin.json       # プラグインのメタデータ
│       └── skills/
│           └── <skill-name>/
│               └── SKILL.md      # 実際のスキル本体
├── .github/workflows/validate-skills.yml
├── scripts/
│   ├── validate_skills.py        # marketplace.json とスキルの整合性チェック
│   ├── package_skill.py          # スキルを .skill (zip) に固める
│   └── sync_to_claude_ai.sh      # 全スキルをまとめて .skill 化
└── README.md
```

## インストール方法

### Claude Code（推奨・自動更新される）

```bash
/plugin marketplace add ryotaroh180105/claude-skills
/plugin install requirements-definition@claude-skills
```

更新を取り込むとき：

```bash
/plugin marketplace update claude-skills
```

インストール後は `/requirements-definition:requirements-definition` のようにプラグイン名で呼び出せる（多くはトリガー条件に合う依頼をするだけで自動発動する）。

### Claude.ai（web・モバイル）

claude.ai の個人スキルアップロードには公開APIが無く、Settings > Capabilities > Skills
からの手動アップロードが必須（自動化不可）。Claude Code セッションでは
`.skill` ファイルの生成・配布まで代行し、ユーザーの作業はドラッグ&ドロップの
アップロードだけに絞る。

1. `scripts/sync_to_claude_ai.sh` を実行して `dist/*.skill` を生成
2. claude.ai の Settings > Capabilities > Skills から該当の `.skill` ファイルをアップロード

```bash
./scripts/sync_to_claude_ai.sh
```

## スキル一覧

### Tier1: 基盤スキル（他のスキル・作業の土台）

| Plugin | 説明 |
|---|---|
| `requirements-definition` | 曖昧な依頼からイシュー特定→MECE分解→ピラミッド構造化で要件定義書を作る |
| `work-approach-playbook` | 仕事の進め方プレイブック（作業前チェックリスト・報連相・完了報告・振り返り） |
| `repo-skill-creator` | このリポジトリでスキルを作成・改善・導入確認するメタスキル（公式skill-creatorと別物） |
| `task-management` | TODO.md ベースのタスク管理（分解・優先順位付け・週次振り返り） |
| `model-switcher` | タスク種別に応じた Claude モデルの選択・切り替え（コスト最適化） |
| `loop-engineering` | 定型作業を Trigger/Doer/Verifier/Stop Rules/Memory/Skills の自律ループとして設計する |
| `biz-ops-guard` | 導入・保守・運用・マーケティング・差別化の5観点でプロダクト成立性を設計する |

### Tier2: 高難易度スキル

| Plugin | 説明 |
|---|---|
| `hermes-agent-setup` | Hermes Agent + MCP + Grok/X Search の情報収集基盤セットアップ・運用 |
| `voicememo-pipeline` | 録音→文字起こし→議事録+フィードバック→Drive/Slack 送信の自動パイプライン |
| `sns-ops-team` | SNS運用のマルチエージェントオーケストレーション（企画・執筆・レビュー・キュー管理） |
| `code-review-adr` | 観点別コードレビュー + アーキテクチャ判断の ADR 記録 |
| `pr-review` | GitHub PR のレビュー実行（取得→レビュー→承認後にコメント投稿） |
| `github-trends` | GitHub トレンドからスキルネタを収集し候補リスト化（採択はユーザー判断） |

### Tier3: 目的直結スキル

個人開発・副業:

| Plugin | 説明 |
|---|---|
| `lp-builder` | LP制作副業（ヒアリング→構成→実装→デプロイ→修正対応） |
| `article-writer` | note記事の企画・執筆・推敲（文体メモ運用付き） |
| `owned-media` | SEO記事作成（KW選定→競合分析→執筆→E-E-A-Tチェック） |
| `twitter-intel` | X からの情報収集・要約（収集経路の自動選択） |
| `sns-auto-posting` | 投稿キューの approved 行を X に投稿（Instagram/TikTok は手動整形） |

インターン業務:

| Plugin | 説明 |
|---|---|
| `testcase-usecase` | ユースケース・テストケースの網羅的洗い出し（TSV納品対応） |
| `document-creation` | 議事録・提案書・報告書・社外メールの型付き作成 |
| `pickup-automation` | 条件抽出ピックアップ業務の自動化（定義ファイル運用） |

学習・知識:

| Plugin | 説明 |
|---|---|
| `consulting-quiz` | コンサル・営業知識クイズ（出題・採点・弱点管理） |
| `aws-exam-practice` | AWS 認定試験（SAA）の模試・演習・弱点復習 |
| `token-saver` | 応答・コンテキスト両面でトークン消費を削減する簡潔応答モードスキル |
| `yagni-guard` | 実装前後にYAGNIの観点でチェックし、過剰設計・不要な抽象化を防ぐスキル |

### その他

| Plugin | 説明 |
|---|---|
| `session-start-hook` | Claude Code on the web 向けの SessionStart フックを設計・実装するスキル |
| `agent-reach` | Agent-Reach (Twitter/X・Reddit・YouTube・GitHub・LinkedIn・Instagram 等を横断検索する OSS CLI) の導入・設定・利用を支援するスキル |
| `hermes-x-search` | Hermes Agent (NousResearch/hermes-agent) の `x_search` を使い、手持ちのX/Grokサブスク枠でX(Twitter)の投稿・スレッド・プロフィールを調査するスキル |

## 作って終わりにしない：壁打ち→ブラッシュアップの運用

v1.0.0 のスキルは叩き台。実際のタスクで使い、Claude と壁打ちしてフィードバックを SKILL.md に反映し、version を上げていくサイクルで練度を上げる（詳細は `repo-skill-creator` スキルと [ROADMAP.md](ROADMAP.md) の運用方針、テストケース生成〜採点の具体的なループは [docs/skill-quality-loop.md](docs/skill-quality-loop.md) を参照）。

X・GitHub トレンド等から新しいスキルネタを収集し（`twitter-intel` / `github-trends`）、[ROADMAP.md](ROADMAP.md) の候補リストに追記→ユーザーが採択判断→実装、というサイクルも継続する。

### hermes-x-search の自動リレー

Claude Code（リモート）と実機の Hermes Agent をつなぐメッセージキューが `hermes-relay` ブランチにある。実機で以下を1回実行すれば、以後は Claude Code がクエリを push するだけで結果が自動で返る：

```bash
curl -fsSL https://raw.githubusercontent.com/ryotaroh180105/claude-skills/hermes-relay/automation/setup-local.sh | bash
```

詳細は `hermes-relay` ブランチの README と `plugins/hermes-x-search` の SKILL.md を参照。

## 新しいスキルを追加する

**ゴールは「作った」ではなく「Claude Codeに実際に導入されている」こと。** リポジトリへのコミット・pushはゴールへの手段であり、以下のどちらかを最後に確認して初めて完了とする：

- Claude Code CLI: `/plugin marketplace add ryotaroh180105/claude-skills` → `/plugin install <new-skill>@claude-skills` を実行し、`/plugin list` でインストール済み・enabledになっていることを確認する
- Claude.ai（web）: `scripts/sync_to_claude_ai.sh` で `.skill` を生成し、Settings > Capabilities > Skills からアップロードして一覧に表示されることを確認する

コミット・push・`validate_skills.py` の通過だけでは未完了。実際にインストールまで確認してから完了報告する。

```bash
mkdir -p plugins/<new-skill>/.claude-plugin plugins/<new-skill>/skills/<new-skill>

cat > plugins/<new-skill>/.claude-plugin/plugin.json << 'EOF'
{
  "name": "<new-skill>",
  "description": "スキルの説明",
  "version": "1.0.0",
  "author": { "name": "ryotaroh180105" }
}
EOF

cat > plugins/<new-skill>/skills/<new-skill>/SKILL.md << 'EOF'
---
name: <new-skill>
description: スキルの説明
---

# <new-skill>

（内容）
EOF
```

`.claude-plugin/marketplace.json` の `plugins` 配列に以下を追記：

```json
{
  "name": "<new-skill>",
  "source": "./plugins/<new-skill>",
  "description": "スキルの説明"
}
```

検証してから commit・push する：

```bash
python3 scripts/validate_skills.py
git add plugins/<new-skill> .claude-plugin/marketplace.json README.md
git commit -m "Add: <new-skill>"
git push
```

手順の詳細（description のトリガー設計・前提セットアップ節の書き方・練度向上の回し方）は
`repo-skill-creator` スキル（`plugins/repo-skill-creator`）が正。ここは最小手順のみ。

GitHub Actions（`.github/workflows/validate-skills.yml`）が push / PR のたびに
`validate_skills.py` を実行し、`marketplace.json` に登録されたスキルの
frontmatter（`name` / `description`）が揃っているかを自動チェックする。
