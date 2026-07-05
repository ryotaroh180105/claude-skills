#!/usr/bin/env bash
# hermes-x-search: one-time local setup
#
# Run this once on the machine that will execute Hermes queries
# (Linux / macOS / WSL2 Ubuntu):
#
#   curl -fsSL https://raw.githubusercontent.com/ryotaroh180105/claude-skills/hermes-relay/automation/setup-local.sh | bash
#
# What it does:
#   1. Installs Hermes Agent if missing
#   2. Runs X/Grok OAuth login (the ONLY interactive step; skipped if done)
#   3. Clones the hermes-relay branch to ~/.hermes-relay
#   4. Registers a cron job that runs the relay watcher every minute
#
# After this, queries pushed to the hermes-relay branch by Claude Code
# are executed automatically and results pushed back — no manual steps.

set -euo pipefail

REPO_URL="${HERMES_RELAY_REPO:-https://github.com/ryotaroh180105/claude-skills.git}"
RELAY_DIR="${HERMES_RELAY_DIR:-$HOME/.hermes-relay}"
BRANCH="hermes-relay"

echo "== hermes-x-search local relay setup =="

# 1. Hermes Agent
if ! command -v hermes >/dev/null 2>&1; then
  echo "-- Hermes Agent が見つからないためインストールします"
  curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
  export PATH="$HOME/.local/bin:$PATH"
  hash -r
fi
if ! command -v hermes >/dev/null 2>&1; then
  echo "!! hermes が PATH にありません。新しいターミナルを開いてこのスクリプトを再実行してください" >&2
  exit 1
fi
echo "-- hermes: $(command -v hermes)"

# 2. X/Grok OAuth (唯一の手動ステップ。認証済みならスキップ)
if [ ! -f "$HOME/.hermes/auth.json" ]; then
  echo "-- X/Grok OAuth ログインを開始します（ブラウザが開きます。X Premium のアカウントでログイン）"
  hermes auth add xai-oauth
else
  echo "-- OAuth 認証済み (~/.hermes/auth.json あり) — スキップ"
fi

# 3. リレー用クローン（hermes-relay ブランチのみ）
if [ ! -d "$RELAY_DIR/.git" ]; then
  echo "-- $RELAY_DIR にリレー用クローンを作成"
  git clone --branch "$BRANCH" --single-branch "$REPO_URL" "$RELAY_DIR"
else
  echo "-- リレー用クローンあり — スキップ"
fi
if ! git -C "$RELAY_DIR" push --dry-run origin "$BRANCH" >/dev/null 2>&1; then
  echo "!! $REPO_URL に push できません。'gh auth login' か SSH/PAT を設定してから再実行してください" >&2
  exit 1
fi

# 4. watcher 環境ファイル（cron の PATH は最小限なので hermes の実体パスを固定する）
printf 'HERMES_BIN=%s\n' "$(command -v hermes)" > "$RELAY_DIR/watcher.env"
chmod +x "$RELAY_DIR/automation/hermes-relay-watcher.sh"

# 5. cron 登録（毎分。多重起動は watcher 側のロックで防止）
CRON_LINE="* * * * * HERMES_RELAY_DIR=$RELAY_DIR $RELAY_DIR/automation/hermes-relay-watcher.sh >> $RELAY_DIR/watcher.log 2>&1"
( crontab -l 2>/dev/null | grep -vF "hermes-relay-watcher.sh" ; echo "$CRON_LINE" ) | crontab -
echo "-- cron 登録完了（毎分実行）"

if grep -qi microsoft /proc/version 2>/dev/null; then
  if ! pgrep -x cron >/dev/null 2>&1; then
    echo "ℹ WSL2 では cron が自動起動しないことがあります。次を実行してください:"
    echo "    sudo service cron start"
    echo "  （恒久化は /etc/wsl.conf に [boot] systemd=true など）"
  fi
fi

# 6. 一度だけ即時実行（pending が空なら何もしません）
"$RELAY_DIR/automation/hermes-relay-watcher.sh" || true

echo ""
echo "✅ セットアップ完了"
echo "   以後、Claude Code が hermes-relay ブランチに置いたクエリは毎分自動実行され、"
echo "   結果が自動で push されます。ユーザー操作は不要です。"
echo "   ログ: $RELAY_DIR/watcher.log"
