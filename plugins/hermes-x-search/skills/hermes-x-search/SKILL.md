---
name: hermes-x-search
description: Install, configure, and use Hermes Agent (github.com/NousResearch/hermes-agent) to research X (Twitter) posts/threads/profiles via its x_search tool, and general web content (articles, docs, comparisons) via its web_search tool, both run against the user's existing X/Grok subscription (tier requirements are inconsistently enforced — try before assuming a paid tier is needed) instead of per-call API charges. Use when the user wants daily X research, general web research, trend/competitor monitoring, or quote-repost source verification without paying for the X API. NotebookLM is retired — all research (X and general web) now routes through this single Hermes path.
---

# Hermes research — X search + general web search

Hermes Agent is NousResearch's self-hosted, MIT-licensed AI agent
(`github.com/NousResearch/hermes-agent`). It bundles two research tools usable
directly from chat:

- **`x_search`** — backed by xAI's Grok Responses API, searches X (Twitter)
  posts, threads, and profiles. Grok runs the search server-side and returns
  synthesized results with citations — no scraping, no separate X API key.
- **`web_search`** — general web search (articles, docs, comparisons, blogs).
  Same backend family as `x_search`; enabled the same way via `hermes tools`.

Both tools are selected automatically by Hermes based on the natural-language
query — there is no engine header or manual switch to set. **NotebookLM is
retired** (its Google-account OAuth expired repeatedly and made it unreliable
as a background pipeline); do not route queries to it or reference it as an
option. All general web research that used to go to NotebookLM now goes to
`web_search` on this same Hermes path.

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

## Enabling x_search and web_search

Both tools are disabled by default. Enable them interactively:

```bash
hermes tools
# select "🐦 X (Twitter) Search" for x_search
# select the general web search entry for web_search
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

### Query-design checklist (reshape the user's ask before enqueueing)

The user sends a one-line ask; Claude Code's job is to expand it into the
prompt Hermes actually receives. `-z` is one-shot — there is no follow-up
turn to clarify or reshape, so everything must be in the prompt up front:

1. **Concretize the scope**: name the specific angles the user implied
   ("スキルを取得したい" → include tools/repos/skills as an explicit target).
2. **Fix the output format**: numbered sections, as above. Always include a
   「未確認・断定できない点」section — it's what makes results safe to quote.
3. **Require source URLs** for every claim so the user can verify before
   reposting or citing.
4. **State the language** (日本語で) — Hermes otherwise follows the query's
   language loosely.
5. **Keep it one question**: don't batch unrelated research topics into one
   query file; enqueue separate files so a failure or timeout costs one topic,
   not all of them.
6. **No ASCII double quotes in query text** — write search hints as
   `verifier prompt / judge prompt` or use 「」, never `"verifier prompt"`.
   PowerShell 5.1 splits native-command arguments at embedded `"`, so a
   quoted phrase breaks `hermes -z` mid-string and the query dies in ~1s
   with a hermes usage error (hit twice in production). The watcher now
   escapes quotes as a backstop, but don't rely on it.

### Single engine: Hermes handles both X and general web research

Web research is done by Hermes itself (v0.18+), not by a separate engine.
**NotebookLM is fully retired** (repeated Google OAuth expiry made it
unreliable as a background pipeline) — do not write `engine: notebooklm`
headers; a query file needs no header at all. The user's local Hermes has
`web.backend: xai`, so `web_search` runs through the same xAI Grok OAuth as
x_search — agentic web search (search → read → synthesize), no extra API
key, no per-call charge beyond the existing subscription. Verified working:
a `web_search`-steered query returned source-URL-backed, quote-bearing
results in ~120s.

Every query file runs through `hermes -z` on the local machine. Which tool
Hermes uses is driven by the prompt:

- X (Twitter) posts/threads/profiles → let it use `x_search` (default for
  X-flavored asks like "Xで〜の反応を調べて").
- General web (docs, blogs, articles, comparisons) → steer it explicitly:
  open the prompt with "web_search（Web検索）を使って調べてください。
  x_search は使わないでください。回答末尾に使用ツール名を列挙してください。"
  The tool self-report lets Claude confirm web_search (not x_search) ran.

**web_extract (specific-URL full-text extraction) is NOT available** on this
setup and must not be attempted:
- Grok's web backend is **search-only** — `web_extract` errors with "xAI Web
  Search (Grok) is a search-only backend and cannot extract URL content."
- `browser`/`navigate` fails on this machine: it is **ARM64 Windows**
  (`No binary found for win32-arm64` — Playwright/Chromium has no ARM64
  Windows build). This also explains the earlier `spawn EFTYPE`.
- The paid extract backends (firecrawl/tavily/exa/parallel) are out of scope
  (no-paid-API policy).
- **Consequence**: for "read this specific URL" (UC5), do NOT enqueue a
  web_extract/browser query — it will fail. Ask the user to paste the page
  content instead.

**Hallucination guard (critical).** In the browser test, Hermes reported the
fetch as failed in one field yet **fabricated plausible headings and verbatim
quotes** in the others. So when a web/extract path can fail, the prompt MUST
say: 「取得に成功したソースの内容だけを書くこと。取得できなかった場合は
見出し・要約・引用を推測や創作で埋めず、『取得失敗』とだけ書くこと。」 And
Claude MUST cross-check the tool self-report against the body: if the report
says a fetch failed but the body contains quotes, treat those quotes as
fabricated and discard them.

**Policy: Claude does not do the researching.** Route research through the
relay (X and web both via `hermes`), then do only query design and result
formatting. Claude's own WebSearch is for meta-purposes (debugging this
pipeline, checking tool availability) or for a user-authorized fallback when
the relay is stalled/erroring — not the default path for answering the
user's research questions.

After the result returns, Claude Code still does the editorial pass (verify
suspicious claims, reformat for the user's actual purpose) — reshaping the
input does not replace judging the output.

### Output schema (two layers — don't over-formalize the body)

Result files have two parts with different reliability guarantees:

**Envelope (machine-written by the watcher, safe to parse strictly):**

```
---
id: <query filename without .md>
status: ok | error (exit N) | error (timeout)
executed_at: <UTC ISO8601>
duration_seconds: <int>
---
```

**Body (LLM-written by Hermes/Grok, parse leniently):** request these standard
section headings in every research query so downstream skills (twitter-intel,
sns-auto-posting, article-writer) can reference sections by name:

1. `今日見るべき話題` — summary of what matters and why
2. `元ポスト/スレッドのURL（根拠）` — source URLs, one per claim
3. `投稿に使える切り口` — post-ready angles
4. `未確認・断定できない点` — what NOT to state as fact
5. `明日以降も追うべき項目` — follow-up watchlist
6. `使用ツール` — which internal tool Hermes actually used (x_search /
   web_search / web_extract), so downstream consumers can tell the search
   path without guessing from the content

For non-SNS uses (market research for `biz-ops-guard`, technical research),
rename headings 1/3/5 to fit the purpose. Only 2 (source URLs, one per claim)
and 4 (未確認・断定できない点) are mandatory in every research query.

Do NOT demand strict JSON from Hermes: `-z` output is LLM-generated and
formatting compliance is loose, so a strict parser will intermittently break
on otherwise-good results. The body's consumer is Claude (an LLM), which
handles section-name drift fine. Only introduce a JSON body (with a lenient
parser and raw-text fallback) if a non-LLM consumer ever needs to read
results without Claude in the loop.

### Preserve source material, not just summaries (link-extraction queries)

**Currently inapplicable on this setup** — link extraction requires
`web_extract` or `browser`, both unavailable (see "web_extract … is NOT
available" above). Keep this pattern for the day an extract backend is
configured; until then ask the user to paste page content instead.

A summary alone destroys the source information — it can't be re-verified,
re-quoted, or re-analyzed from a different angle later. Whenever the query
has Hermes read linked content (note articles, blog posts, X Articles via
`web_extract`/browser), require these additional sections in the output:

1. `元ポストURL / リンク先URL` — both links, so the chain of custody from
   tweet to article is preserved.
2. `引用可能な原文抜粋` — key passages quoted **verbatim** in 「」, not
   paraphrased. These are what the user can safely reuse in a quote-repost
   or article without re-reading the source.
3. `全文抽出（生テキスト）` — the full extracted text (or however much was
   readable) appended raw at the end of the result, clearly marked as raw.
   Result files are just text on a git branch; length is not a problem.

Section 3 is the important one: when the user later wants the same article
re-analyzed from a different angle, Claude re-reads the raw appendix from the
existing result file — no re-query, no extra Hermes/Grok cost, no risk the
page has changed or gone down. Also have Hermes state explicitly whether it
read the full text or was cut off (paywall / member-only sections on note).

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
- `web_extract` fails on the xAI backend (search-only) and `browser` has no
  ARM64 Windows binary — see the "web_extract … is NOT available" block in
  the engine section above. Don't promise full-text extraction of a linked
  page; ask the user to paste page content instead.
- If editing the `.ps1` relay scripts: keep `Write-Host`/comment text ASCII-only.
  Windows PowerShell 5.1 reads `.ps1` files with the system's legacy codepage
  unless the file carries a UTF-8 BOM, so non-ASCII text (e.g. Japanese) reliably
  produces mojibake and string-parsing errors on Japanese-locale Windows.
- If a Windows relay's queries sit in `pending` forever after a successful setup
  run: check `schtasks /Query /TN HermesRelayWatcher /V /FO LIST` for
  `前回の実行時刻` stuck at `1999/11/30` and `前回の結果: 267011`
  (`SCHED_S_TASK_HAS_NOT_RUN`) — the task looks "Ready" with a valid next-run
  time forever but has never actually fired. Root cause: `schtasks /Create`
  defaults to "don't start on battery / stop if going on battery," which
  silently blocks the task on any laptop that isn't plugged in. `setup-local.ps1`
  now registers the task via the `ScheduledTasks` module with
  `AllowStartIfOnBatteries`/`DontStopIfGoingOnBatteries` set — if the user is on
  an older copy of the script, have them re-run the latest version rather than
  debugging Hermes itself.
- If a Windows relay's Task Scheduler task is confirmed running (`前回の結果: 0`
  / recent `前回の実行時刻`) but queries still sit in `pending` forever: a stale
  `.watcher.lock.d` from an earlier interrupted run silently no-ops every run
  (exit 0, nothing processed) until it ages past the stale-lock threshold. Have
  the user delete it manually to unblock immediately:
  `Remove-Item "$env:USERPROFILE\.hermes-relay\.watcher.lock.d" -Recurse -Force`.
  `watcher.log` in the relay dir (added after this was hit in testing) logs
  pending-query counts and per-query start/finish, so check that first instead
  of guessing.
- If the user wants zero-subscription-cost scraping instead (accepting slower,
  more fragile results), point them at this same repo's `agent-reach` skill,
  which reads X via browser cookies rather than any paid API or subscription.
