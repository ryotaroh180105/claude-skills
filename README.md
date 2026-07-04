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

## 新しいスキルを追加する

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
git add .
git commit -m "Add: <new-skill>"
git push
```

GitHub Actions（`.github/workflows/validate-skills.yml`）が push / PR のたびに
`validate_skills.py` を実行し、`marketplace.json` に登録されたスキルの
frontmatter（`name` / `description`）が揃っているかを自動チェックする。
