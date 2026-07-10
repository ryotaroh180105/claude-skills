# Example: "standup-digest" (a Slack bot that summarizes yesterday's PRs into a standup update) — Viability Sheet

Path taken: fast path (a working demo was buildable in an afternoon).
Calibration: every line 1–2 sentences; provisional items say so honestly.

- Value prop: an engineer on a small team can post a ready standup update without re-reading their own git history every morning
- 3 real users: teammate A (opens 4–5 PRs/week, always forgets what he did), teammate B (remote, standup is async in Slack), myself (same problem)
- Real signal: A replied "send me the link, I'll try it tomorrow" (Slack DM, 7/6); B actually posted the bot's output in real standup channel twice (message history, 7/6–7/7)
- Onboarding: 2 steps / 3 minutes / prerequisites: a GitHub token, a Slack webhook URL
- Keep-it-alive: 20 min/week budget / breaks if: GitHub token expires or Slack webhook is revoked / failure alert: bot posts an error message to a DM instead of failing silently / kill criteria: budget overrun twice in a row, or 0 active users for 2 months
- Distribution: shared directly in the team's Slack, then posted to r/ExperiencedDevs / first 10 users / deadline: 3 weeks after launch
- Revenue: free. Return is a portfolio story + it removes 10 min/day of my own tedious work
- Metrics: number of teammates who installed the webhook / how many mornings/week they actually post the generated summary / anyone who shared it outside the team
- Deliberately ignoring: multi-workspace support, a hosted version (self-host only for now), non-GitHub sources
- Devil's advocate: 3 objections (① "I already write my own standup in 30 seconds" ② "another bot posting in Slack is just noise" ③ "what if it summarizes something embarrassing from a PR title") → addressed: ① addressed by A's actual signal (still wanted it despite this) — real evidence beats the objection; ② mitigated by posting only on request, not automatically; ③ added a redaction step for PR titles matching a configurable pattern
