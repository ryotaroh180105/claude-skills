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

## Claude Code as query designer, local terminal as executor

**Do not try to run `hermes` yourself from inside a Claude Code remote/cloud
session.** As established above, OAuth and long-running calls are unreliable
there — the working setup (OAuth login, `x_search` access) lives on the user's
local machine, not this session. Split the work instead:

1. **Claude Code designs the query.** Turn the user's ask ("Xで◯◯の反応を見て")
   into a single, self-contained `hermes -z` command. Fold the fixed output
   shape from "Structuring output" below directly into the prompt text — the
   local run is one-shot with no follow-up turn, so ask for the structure
   up front rather than trying to reshape the answer afterward:

   ```bash
   hermes -z "◯◯についての直近のXの投稿・反応を調べて、次の形式で出力して：
   1. 今日見るべき話題 2. 元ポスト/スレッドのURL 3. 投稿に使える切り口
   4. 未確認・断定できない点 5. 明日以降も追うべき項目" --accept-hooks
   ```

   `--accept-hooks` registers any hooks in the user's Hermes config without an
   interactive prompt; `-z` gives clean stdout with nothing else to parse. On
   WSL2 the user runs it as `wsl -d Ubuntu -- hermes -z "..." --accept-hooks`.

2. **Hand the command to the user, not a tool call.** Tell them to run it in a
   plain local terminal (not this session, not an editor-embedded terminal) and
   paste back whatever it prints — including if it errors or times out.

3. **Claude Code takes the raw pasted output and does the judgment/formatting
   work**: separate confirmed facts (with source URLs) from unconfirmed
   chatter, pull out post-worthy angles, and flag what still needs follow-up.
   Don't just relay Hermes's raw text back to the user unchanged — that
   formatting/judgment step is what this skill's remote side is actually for.

## Usage patterns

Hermes routes these kinds of asks to `x_search` automatically once enabled —
use them as the natural-language core of the `hermes -z` prompt you hand to the
user for local execution:

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
- If the user wants zero-subscription-cost scraping instead (accepting slower,
  more fragile results), point them at this same repo's `agent-reach` skill,
  which reads X via browser cookies rather than any paid API or subscription.
