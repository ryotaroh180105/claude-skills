---
name: agent-reach
description: Install, configure, and use Agent-Reach (github.com/Panniantong/Agent-Reach) so Claude can search and read across Twitter/X, Reddit, YouTube, GitHub, LinkedIn, Instagram, Bilibili, XiaoHongShu, RSS, and general web pages via CLI tools instead of paid APIs. Use when the user wants cross-platform social media research, competitor monitoring, or trend gathering without scrolling each app manually.
---

# Agent-Reach

Agent-Reach is a third-party open-source CLI (`Panniantong/Agent-Reach`) that gives an
agent a unified way to search and read content across many platforms by routing to
existing CLI tools (`gh`, `yt-dlp`, `twitter`, `bili-cli`, Jina Reader, etc.) instead of
calling per-platform paid APIs. It is not an Anthropic product — verify the repo/install
script before running it in a sensitive environment.

## When to use this skill

- The user asks to research a topic, competitor, or trend across multiple social
  platforms at once (e.g. "Xでバズってるツイートと関連するYouTube動画をまとめて").
  Reddit/Twitter, YouTube subtitles, GitHub repos, etc.
- The user wants Agent-Reach installed or configured in this environment.
- The user asks whether a given platform needs login/cookies before Agent-Reach can
  read it.

## Installation

```bash
pip install https://github.com/Panniantong/agent-reach/archive/main.zip
agent-reach install --env=auto
```

To register it as a Claude Code skill directly (alternative to a manual pip install):

```bash
npx skills add Panniantong/Agent-Reach@agent-reach
```

Use `--safe` on `agent-reach install` to preview what would be installed/configured
without letting it touch system packages automatically:

```bash
agent-reach install --env=auto --safe
```

After installing, verify what's working:

```bash
agent-reach doctor
```

This reports which backends are active, which are ready to use, and which still need
configuration (cookies/login).

## Platform setup reference

| Platform | Setup type | What's needed |
|---|---|---|
| YouTube | Zero config | Works immediately via `yt-dlp` (subtitles, metadata) |
| Bilibili | Zero config | Uses `bili-cli`, no login for search/details |
| GitHub | Zero config (basic) | Public repos work immediately; `gh auth login` unlocks private repos/full functionality |
| RSS/Atom | Zero config | Handled automatically via feedparser |
| Web pages (general) | Zero config | Jina Reader API converts any URL to clean Markdown |
| LinkedIn | Zero config (public) | Public pages readable as-is; full profile access needs extra setup |
| Twitter/X | Cookie-based | Export browser cookies to unlock search/read/post |
| Reddit | Optional login | Use OpenCLI (desktop, reuses browser session) or `rdt-cli` after `rdt login` |
| Instagram | Desktop only | OpenCLI reuses the local Chrome session — no server-side option |
| XiaoHongShu | Multi-option | Desktop via OpenCLI, or server-side via `xiaohongshu-mcp` with QR login |

Notes:
- Cookie/login-gated platforms (Twitter/X, Reddit, Instagram, XiaoHongShu) will not
  work zero-config — tell the user this upfront instead of assuming full coverage.
- OpenClaw users must set the tool profile to `coding` (not the default `messaging`)
  to grant `exec` permission before installing.
- A paid proxy (~$1/month) is only needed on networks that block the underlying
  services; local/unrestricted networks don't need one.

## Usage patterns

Once installed, invoke it with natural language — Agent-Reach's agent picks the
right backend:

- "この記事を読んで要約して" → Jina Reader extracts the page
- "このGitHubリポジトリの概要を教えて" → `gh repo view owner/repo`
- "この動画の字幕を取得して" → `yt-dlp --dump-json URL`
- "このツイートの内容を教えて" → `twitter tweet URL` (requires cookie auth)
- "◯◯というフレームワークをGitHubで検索して" → `gh search repos "query"`

For cross-platform research (the main selling point), phrase the request as a single
combined ask, e.g. "Reddit・X・YouTubeで◯◯についての最新の反応をまとめて" — Agent-Reach's
router dispatches to each platform's backend and Claude aggregates the results.

## Caveats to surface to the user

- Scraping-based platforms (Twitter/X, Instagram, XiaoHongShu) can break when the
  target site changes its markup, or may violate that platform's terms of service —
  mention this risk before recommending heavy automated use.
- "Real-time" is relative: results reflect whatever the underlying CLI/scraper can
  fetch at request time, not a live streaming feed.
- Treat cookie exports and login sessions as credentials: don't commit them to a repo
  or share them in logs.
