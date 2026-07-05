---
name: hermes-x-search
description: Install, configure, and use Hermes Agent (github.com/NousResearch/hermes-agent) to research X (Twitter) posts, threads, and profiles via its x_search tool, run against the user's existing X/Grok subscription (tier requirements are inconsistently enforced — try before assuming a paid tier is needed) instead of per-call X API charges. Use when the user wants daily X research, trend/competitor monitoring, or quote-repost source verification without paying for the X API.
---

# Hermes x_search

Hermes Agent is NousResearch's self-hosted, MIT-licensed AI agent
(`github.com/NousResearch/hermes-agent`). It bundles `x_search`, a tool backed by
xAI's Grok Responses API that searches X (Twitter) posts, threads, and profiles
directly from chat. Grok runs the search server-side and returns synthesized
results with citations — no scraping, no separate X API key.

## Cost reality — read this before promising "free"

`x_search` via `xai-oauth` needs an xAI/X subscription, but **tier enforcement is
currently inconsistent and not something you can rely on from documentation
alone**:

- Official docs (`docs/guides/xai-grok-oauth.md`) state OAuth requires **SuperGrok**
  (~$30/month, standalone via grok.com) or **X Premium+** (~$40/month).
- In practice, `NousResearch/hermes-agent#26847` (filed 2026-05-16, closed as
  "not planned") reports the backend sometimes enforces **Heavy-tier only**,
  returning 403 even for paying SuperGrok Standard / Premium+ subscribers —
  contradicting the "available on every tier" announcement from the same week.
- Anecdotally, some users report plain **X Premium** (~$8/month, no Plus) passing
  the OAuth check and successfully running `x_search`. This is not documented or
  guaranteed — it may reflect a temporarily lenient backend check, Premium vs.
  Premium+ terminology confusion, or genuine tier-independent behavior. Treat it
  as "worth trying," not as a supported feature.

**Practical guidance:** since running `hermes auth add xai-oauth` and testing costs
nothing extra beyond the subscription the user already has, just try it on whatever
tier the user has (Free/Premium/Premium+/SuperGrok) and check with `hermes -z
"test query"` or the `hermes tools` status. If OAuth 403s, fall back to an
`XAI_API_KEY` (pay-per-token against the standard xAI API, tier-independent) or to
this repo's `agent-reach` skill (free, cookie-based scraping, no subscription at
all).

The alternative bundled tool, `xurl` (official X API v2 CLI), is billed per-call
against the X Developer API (new apps require a minimum $5 credit purchase) — use
it only when the user explicitly wants to post, DM, or needs API coverage
`x_search` doesn't provide.

## Installation

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

Installs Python 3.11, Node.js, ripgrep, ffmpeg, and Git automatically — no
prerequisites.

**Windows: WSL2 is not required.** Native Windows install works for the CLI,
messaging gateway, cron, browser tool, and MCP — everything this skill needs:

```powershell
iex (irm https://hermes-agent.nousresearch.com/install.ps1)
```

The only feature that still needs WSL2 is the web dashboard's embedded `/chat`
terminal tab (it needs a POSIX PTY Windows doesn't provide) — irrelevant for
`x_search` usage from the CLI. Don't tell the user WSL2 is a prerequisite unless
they specifically want that dashboard tab.

## Enabling x_search

`x_search` is disabled by default. Enable it interactively:

```bash
hermes tools
# select "🐦 X (Twitter) Search"
```

Authenticate via browser OAuth against whatever X/Grok subscription the user
already has — don't assume it needs to be SuperGrok/Premium+ first, since tier
enforcement is inconsistent (see Cost reality above):

```bash
hermes auth add xai-oauth
# headless/no browser available: hermes auth add xai-oauth --no-browser
```

When both an OAuth session and `XAI_API_KEY` are present, OAuth wins (so it's used
against subscription quota instead of paid API spend, when it works).

Verify:

```bash
hermes model              # confirm an LLM provider is configured
hermes tools               # confirm x_search shows as enabled
hermes -z "test query"    # smoke-test — a 403 here means OAuth was rejected for this account/tier
```

Notes from real-world use: the first `x_search` call can take ~2-3 minutes —
worth telling the user to expect the wait rather than assume it hung. Run Hermes
from a plain, local terminal (Terminal.app on macOS, or a native Windows/WSL2
console) rather than an editor's integrated terminal or a remote/cloud session —
both VS Code's integrated terminal and remote execution environments have been
reported to kill the OAuth flow or the process mid-request. If a run fails in a
remote/CI environment, retry from a physical machine's terminal before assuming
the setup itself is broken.

## Claude Code as query designer, local machine as executor

**Do not try to run `hermes` yourself from inside a Claude Code remote/cloud
session.** As established above, OAuth and long-running calls are unreliable
there — the working setup (OAuth login, `x_search` access) lives on the user's
local machine, not this session. Claude Code designs queries and formats
results; the local machine executes them.

### Automated relay (preferred — user does nothing per query)

The repo's `hermes-relay` branch is a git-based message queue between Claude
Code and a cron watcher on the user's machine. Once the user has run the
one-time local setup (below), the full round trip is automatic: Claude Code
pushes a query file, the local watcher executes it within ~1 minute, and
pushes the result back. Expected end-to-end latency: **1–4 minutes**.

**One-time local setup** (the only thing the user ever runs by hand; includes
one interactive OAuth browser login). Linux / macOS / WSL2:

```bash
curl -fsSL https://raw.githubusercontent.com/ryotaroh180105/claude-skills/hermes-relay/automation/setup-local.sh | bash
```

Windows native (no WSL; uses Task Scheduler instead of cron — note that in
PowerShell `curl` is an alias for Invoke-WebRequest, so don't hand the user
the bash one-liner there). Use `git clone` rather than `irm ... -OutFile`:
some networks (ISP or endpoint-security DNS filtering) block
`raw.githubusercontent.com` specifically while `github.com` itself resolves
fine, and `irm` against the blocked host fails with a bare "remote name
could not be resolved" that's easy to misdiagnose as a Hermes problem:

```powershell
git clone --branch hermes-relay --single-branch https://github.com/ryotaroh180105/claude-skills.git "$env:USERPROFILE\.hermes-relay"
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\.hermes-relay\automation\setup-local.ps1"
```

If `git` itself isn't found, `winget install Git.Git` then open a *new*
PowerShell window before retrying (PATH doesn't refresh in the same window).

**Per query, from the Claude Code session** — enqueue:

```bash
RELAY="$(mktemp -d)/relay"
git clone -q --depth 1 --branch hermes-relay --single-branch \
  https://github.com/ryotaroh180105/claude-skills "$RELAY"
ID="$(date -u +%Y%m%dT%H%M%SZ)-<topic-slug>"
cat > "$RELAY/automation/queries/pending/${ID}.md" <<'EOF'
（hermes に渡すプロンプト全文。出力フォーマット指定込み — 下の
「Structuring output」の形式をそのまま埋め込む。ワンショット実行で
追加の対話ターンはないので、構造は最初から要求しておくこと）
EOF
git -C "$RELAY" add -A
git -C "$RELAY" commit -qm "hermes-relay: query ${ID}"
git -C "$RELAY" push -q origin hermes-relay
```

Then poll for the result **in a background Bash task** (foreground sleep is
blocked in Claude Code sessions):

```bash
for i in $(seq 1 30); do
  git -C "$RELAY" fetch -q origin hermes-relay
  if git -C "$RELAY" cat-file -e "origin/hermes-relay:automation/results/${ID}.md" 2>/dev/null; then
    git -C "$RELAY" show "origin/hermes-relay:automation/results/${ID}.md"
    exit 0
  fi
  sleep 30
done
echo "TIMEOUT: no result after 15 min — check watcher.log on the local machine"
exit 1
```

Result files carry a frontmatter header (`status: ok` / `status: error`,
`executed_at`, `duration_seconds`) followed by Hermes's raw output. On
`status: error` the body contains stderr — diagnose from that instead of
re-queueing blindly.

**Once the result arrives, Claude Code does the judgment/formatting work**:
separate confirmed facts (with source URLs) from unconfirmed chatter, pull out
post-worthy angles, and flag what needs follow-up. Don't relay Hermes's raw
text unchanged — this formatting step is what the remote side is for.

Relay privacy caveat: if this repo is public, queries and results are public
too. Keep secrets and unpublished strategy out of query text, or point
`HERMES_RELAY_REPO` at a private repo during setup.

### Manual fallback (no relay set up, or watcher is down)

Hand the user a single self-contained command to run in a plain local
terminal, and have them paste back whatever it prints (including errors):

```bash
hermes -z "◯◯についての直近のXの投稿・反応を調べて、次の形式で出力して：
1. 今日見るべき話題 2. 元ポスト/スレッドのURL 3. 投稿に使える切り口
4. 未確認・断定できない点 5. 明日以降も追うべき項目" --accept-hooks
```

`--accept-hooks` registers any hooks in the user's Hermes config without an
interactive prompt; `-z` gives clean stdout with nothing else to parse. On
WSL2 the user runs it as `wsl -d Ubuntu -- hermes -z "..." --accept-hooks`.

## Usage patterns

Hermes routes these kinds of asks to `x_search` automatically once enabled —
use them as the natural-language core of the query you enqueue on the relay
(or hand to the user in the manual fallback):

- "この件についてXでどんな反応が出てるか調べて" → searches recent posts/threads
- "◯◯さんの直近の投稿を要約して" → profile/timeline search
- "このバズってるポストの元スレッドを追って" → thread search

## Structuring output for daily research / posting workflows

Don't just ask Hermes to "summarize" — separate **search** (finding candidate
posts/threads) from **judgment** (what's usable, what's still unconfirmed). For
recurring X research, request a fixed output shape, e.g.:

```
x_search で◯◯についての直近の投稿・反応を調べてください。

出力は次の形式に分けてください：
1. 今日見るべき話題
2. 元ポスト/スレッドのURL（根拠）
3. 引用リポストや投稿に使える切り口
4. 未確認・断定できない点
5. 明日以降も追うべき項目
```

This keeps confirmed facts (with source URLs) separate from unconfirmed chatter,
which matters before quote-reposting or citing something in a written post.

## Turning a working research flow into a reusable skill

Once a research prompt/flow works well repeatedly, use Hermes's own `/learn` to
turn it into a Skill instead of re-typing it each time:

```
/learn この会話で使ったX日次リサーチの手順をSkill化してください。
検索、根拠URLの確認、未確認情報の分離、投稿素材への変換の順番を残してください。
APIキー・個人情報・未公開の戦略は含めないでください。
```

## Caveats to surface to the user

- `x_search` results are Grok's synthesis of X content, not a raw firehose — treat
  it as a research aid, not a guaranteed-complete monitoring feed.
- A 403 on `xai-oauth` doesn't reliably tell you anything about the account's tier
  — per the linked GitHub issue, even paid SuperGrok/Premium+ accounts get 403'd
  sometimes. Don't assume it's a config bug on the user's end; don't assume
  upgrading tiers will fix it either. Retry, or fall back to `XAI_API_KEY`/
  `agent-reach`.
- Never put `XAI_API_KEY` or OAuth tokens in chat/context; configure them via
  `hermes tools` / the credential store, not inline.
- If editing the `.ps1` relay scripts: keep `Write-Host`/comment text ASCII-only.
  Windows PowerShell 5.1 reads `.ps1` files with the system's legacy codepage
  unless the file carries a UTF-8 BOM, so non-ASCII text (e.g. Japanese) reliably
  produces mojibake and string-parsing errors on Japanese-locale Windows.
- If the user wants zero-subscription-cost scraping instead (accepting slower,
  more fragile results), point them at this same repo's `agent-reach` skill,
  which reads X via browser cookies rather than any paid API or subscription.
