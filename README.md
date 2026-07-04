# claude-skills

Claude Code / Claude.ai で使う Skill 集を管理するリポジトリ。

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
/plugin install session-start-hook@claude-skills
```

更新を取り込むとき：

```bash
/plugin marketplace update claude-skills
```

インストール後は `/session-start-hook:session-start-hook` のようにプラグイン名で呼び出せる。

### Claude.ai（web）

1. `scripts/sync_to_claude_ai.sh` を実行して `dist/*.skill` を生成
2. claude.ai の Settings > Capabilities > Skills から該当の `.skill` ファイルをアップロード

```bash
./scripts/sync_to_claude_ai.sh
```

## スキル一覧

| Plugin | 説明 |
|---|---|
| `session-start-hook` | Claude Code on the web 向けの SessionStart フックを設計・実装するスキル |
| `agent-reach` | Agent-Reach (Twitter/X・Reddit・YouTube・GitHub・LinkedIn・Instagram 等を横断検索する OSS CLI) の導入・設定・利用を支援するスキル |
| `requirements-definition` | 曖昧な依頼からイシュー特定→MECE分解→ピラミッド構造化で要件定義書を作るスキル |
| `work-approach-playbook` | 仕事の進め方プレイブック（作業前チェックリスト・報連相・完了報告・振り返り） |
| `skill-creator` | このリポジトリでスキルを作成・改善・導入確認するメタスキル |
| `task-management` | TODO.md ベースのタスク管理（分解・優先順位付け・週次振り返り） |
| `model-switcher` | タスク種別に応じた Claude モデルの選択・切り替え（コスト最適化） |
| `voicememo-pipeline` | 録音→文字起こし→議事録+フィードバック→Drive/Slack 送信の自動パイプライン |
| `sns-ops-team` | SNS運用のマルチエージェントオーケストレーション（企画・執筆・レビュー・キュー管理） |
| `hermes-agent-setup` | Hermes Agent + MCP + Grok/X Search の情報収集基盤セットアップ・運用 |
| `code-review-adr` | 観点別コードレビュー + アーキテクチャ判断の ADR 記録 |
| `pr-review` | GitHub PR のレビュー実行（取得→レビュー→承認後にコメント投稿） |
| `github-trends` | GitHub トレンドからスキルネタを収集し候補リスト化（採択はユーザー判断） |
| `lp-builder` | LP制作副業（ヒアリング→構成→実装→デプロイ→修正対応） |
| `article-writer` | note記事の企画・執筆・推敲（文体メモ運用付き） |
| `owned-media` | SEO記事作成（KW選定→競合分析→執筆→E-E-A-Tチェック） |
| `twitter-intel` | X からの情報収集・要約（収集経路の自動選択） |
| `sns-auto-posting` | 投稿キューの approved 行を X に投稿（Instagram/TikTok は手動整形） |
| `testcase-usecase` | ユースケース・テストケースの網羅的洗い出し（TSV納品対応） |
| `document-creation` | 議事録・提案書・報告書・社外メールの型付き作成 |

今後の追加予定と優先順位は [ROADMAP.md](ROADMAP.md)、各スキルの要件定義は [docs/skill-requirements.md](docs/skill-requirements.md) を参照。

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
`skill-creator` スキル（`plugins/skill-creator`）が正。ここは最小手順のみ。

GitHub Actions（`.github/workflows/validate-skills.yml`）が push / PR のたびに
`validate_skills.py` を実行し、`marketplace.json` に登録されたスキルの
frontmatter（`name` / `description`）が揃っているかを自動チェックする。
