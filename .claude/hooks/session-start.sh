#!/bin/bash
set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# MISTAKES.md の再発防止ルールを毎セッションのコンテキストに注入する。
# ローカル・リモート両方で実行する（skills コピーより前）。
if [ -f "$PROJECT_DIR/MISTAKES.md" ]; then
  sed -n '/<!-- rules:start -->/,/<!-- rules:end -->/p' "$PROJECT_DIR/MISTAKES.md"
fi

# Claude Code on the web (Cowork remote sessions) has no /plugin command, so
# marketplace skills in plugins/*/skills/*/ never become invokable there.
# This hook copies every skill directly into ~/.claude/skills/ so remote
# sessions get the same skills as a local CLI with the marketplace installed.
# Local CLI users already get skills via /plugin install, so skip there.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

SKILLS_DIR="${HOME}/.claude/skills"
mkdir -p "$SKILLS_DIR"

count=0
for skill_path in "$PROJECT_DIR"/plugins/*/skills/*/; do
  [ -d "$skill_path" ] || continue
  [ -f "${skill_path}SKILL.md" ] || continue
  skill_name="$(basename "$skill_path")"
  rm -rf "${SKILLS_DIR:?}/${skill_name}"
  cp -r "$skill_path" "$SKILLS_DIR/$skill_name"
  count=$((count + 1))
done

echo "session-start: installed $count skill(s) from plugins/*/skills/* into $SKILLS_DIR"
