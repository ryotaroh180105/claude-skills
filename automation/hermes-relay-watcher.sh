#!/usr/bin/env bash
# hermes-relay watcher
#
# Runs on the user's local machine (cron, every minute). Picks up query
# files queued on the hermes-relay branch by Claude Code sessions,
# executes them against the local Hermes Agent (x_search etc.), and
# pushes the results back so the remote session can read them.
#
# Installed by setup-local.sh. Safe to run manually at any time.

set -uo pipefail

RELAY_DIR="${HERMES_RELAY_DIR:-$HOME/.hermes-relay}"
BRANCH="hermes-relay"
QUERY_TIMEOUT="${HERMES_QUERY_TIMEOUT:-900}"

# cron runs with a minimal PATH; watcher.env pins the hermes binary
# location captured at setup time.
[ -f "$RELAY_DIR/watcher.env" ] && . "$RELAY_DIR/watcher.env"
export PATH="$HOME/.local/bin:/usr/local/bin:/opt/homebrew/bin:$PATH"
HERMES_BIN="${HERMES_BIN:-$(command -v hermes || true)}"
if [ -z "$HERMES_BIN" ] || [ ! -x "$HERMES_BIN" ]; then
  echo "$(date -u +%FT%TZ) hermes binary not found (set HERMES_BIN in $RELAY_DIR/watcher.env)" >&2
  exit 1
fi

cd "$RELAY_DIR" || exit 1

# Single-instance lock. mkdir is atomic and works on macOS (no flock).
# x_search runs can exceed the 1-minute cron interval, so overlapping
# invocations must bail out immediately.
LOCKDIR="$RELAY_DIR/.watcher.lock.d"
if ! mkdir "$LOCKDIR" 2>/dev/null; then
  # Break locks older than 60 min — a crashed run, not a live one.
  if [ -n "$(find "$LOCKDIR" -maxdepth 0 -mmin +60 2>/dev/null)" ]; then
    rmdir "$LOCKDIR" 2>/dev/null || true
    mkdir "$LOCKDIR" 2>/dev/null || exit 0
  else
    exit 0
  fi
fi
trap 'rmdir "$LOCKDIR" 2>/dev/null' EXIT

git fetch -q origin "$BRANCH" || exit 1
git checkout -q "$BRANCH" 2>/dev/null || git checkout -qb "$BRANCH" "origin/$BRANCH"
git reset -q --hard "origin/$BRANCH"

shopt -s nullglob
PROCESSED=0
for q in automation/queries/pending/*.md; do
  id="$(basename "$q" .md)"
  out="automation/results/${id}.md"
  tmp_out="$(mktemp)"
  start=$(date +%s)
  if command -v timeout >/dev/null 2>&1; then
    timeout "$QUERY_TIMEOUT" "$HERMES_BIN" -z "$(cat "$q")" --accept-hooks >"$tmp_out" 2>&1
  else
    "$HERMES_BIN" -z "$(cat "$q")" --accept-hooks >"$tmp_out" 2>&1
  fi
  rc=$?
  end=$(date +%s)
  {
    echo "---"
    echo "id: ${id}"
    if [ "$rc" -eq 0 ]; then
      echo "status: ok"
    else
      echo "status: error (exit ${rc})"
    fi
    echo "executed_at: $(date -u +%FT%TZ)"
    echo "duration_seconds: $((end - start))"
    echo "---"
    echo
    cat "$tmp_out"
  } > "$out"
  rm -f "$tmp_out"
  mv "$q" "automation/queries/done/${id}.md"
  git add -A
  git -c user.name="${GIT_AUTHOR_NAME:-hermes-relay}" \
      -c user.email="${GIT_AUTHOR_EMAIL:-hermes-relay@local}" \
      commit -q -m "hermes-relay: result for ${id}"
  PROCESSED=1
done

if [ "$PROCESSED" -eq 1 ]; then
  git push -q origin "$BRANCH" \
    || { git pull -q --rebase origin "$BRANCH" && git push -q origin "$BRANCH"; }
fi
