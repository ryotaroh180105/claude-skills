---
name: hermes-x-search
description: Install, configure, and use Hermes Agent (github.com/NousResearch/hermes-agent) to research X (Twitter) posts, threads, and profiles via its x_search tool, billed against a SuperGrok or X Premium+ subscription instead of per-call X API charges. Use when the user wants daily X research, trend/competitor monitoring, or quote-repost source verification without paying for the X API.
---

# Hermes x_search

Hermes Agent is NousResearch's self-hosted, MIT-licensed AI agent
(`github.com/NousResearch/hermes-agent`). It bundles `x_search`, a tool backed by
xAI's Grok Responses API that searches X (Twitter) posts, threads, and profiles
directly from chat. Grok runs the search server-side and returns synthesized
results with citations — no scraping, no separate X API key.

## Cost reality — read this before promising "free"

`x_search` is **not free by default**. It requires one of these to authenticate:

- **SuperGrok** (~$30/month, standalone subscription via grok.com, no X account needed), or
- **X Premium+** (~$40/month, includes Grok access plus X platform perks)

Plain **X Premium** (the old Blue tier, ~$8/month) does **not** unlock `x_search` —
calls will fail with a 403 "no active Grok subscription" error. If the user already
pays for SuperGrok or Premium+, `x_search` runs against that subscription's quota
with no additional per-call charge — that's the "practically free" case. Confirm
which tier the user has before assuming this path works.

The alternative bundled tool, `xurl` (official X API v2 CLI), is billed per-call
against the X Developer API (new apps require a minimum $5 credit purchase) — use
it only when the user explicitly wants to post, DM, or needs API coverage
`x_search` doesn't provide.

## Installation

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

Installs Python 3.11, Node.js, ripgrep, ffmpeg, and Git automatically — no
prerequisites. Windows: `iex (irm https://hermes-agent.nousresearch.com/install.ps1)`
in PowerShell.

## Enabling x_search

`x_search` is disabled by default. Enable it interactively:

```bash
hermes tools
# select "🐦 X (Twitter) Search"
```

Then authenticate with SuperGrok/Premium+ OAuth (preferred — uses subscription
quota) or an `XAI_API_KEY` (falls back to paid API spend if no OAuth session is
configured). When both are present, OAuth wins.

Verify:

```bash
hermes model      # confirm an LLM provider is configured
hermes tools       # confirm x_search shows as enabled
```

## Usage patterns

Ask in natural language once enabled — Hermes routes to `x_search` automatically
for X-specific asks:

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
- A 403 error almost always means the account isn't on SuperGrok/Premium+, not a
  configuration bug — check the subscription tier before debugging further.
- Never put `XAI_API_KEY` or OAuth tokens in chat/context; configure them via
  `hermes tools` / the credential store, not inline.
- If the user wants zero-subscription-cost scraping instead (accepting slower,
  more fragile results), point them at this same repo's `agent-reach` skill,
  which reads X via browser cookies rather than any paid API or subscription.
