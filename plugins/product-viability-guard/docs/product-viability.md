# product-viability-guard — Viability Sheet

This skill is its own first real-world application of the v2.0 process (per the design doc's implementation
order: creating this skill doubles as the first end-to-end test of the fast/design-first path). Filled in
2026-07-10.

- Value prop: an English-speaking solo/indie builder can catch "I built it but nobody wanted it" before writing code, using one page and one real-world reaction, instead of a market-research phase
- 3 real users: Ryo (maintains this repo, already uses the Japanese sibling skill on every product he ships), an anonymous member of the Claude Code skills community who upvoted/starred similar guard-style skills in this repo's github-trends scans, a third is not yet identified (provisional)
- Real signal: none yet — this skill has not been distributed outside this repo
- Onboarding: 2 steps / 3 minutes / prerequisites: Claude Code + this marketplace added
- Keep-it-alive: 20 min/month budget (lighter than the Japanese sibling — no relay/CLAUDE.md coupling to maintain) / breaks if: the sibling skill's process changes and this port drifts / failure alert: none automated yet (manual quarterly sync check) / kill criteria: zero installs/stars/mentions 4 weeks after first public distribution attempt
- Distribution: (1) PR to anthropics/skills or another public skills marketplace (2) this repo's own marketplace with an English README (3) a mention in the English-speaking Claude Code / indie-hacker community on X / first 10 users / deadline: 4 weeks after first distribution attempt
- Revenue: free. Return = validates the guard-skill pattern itself, a portfolio artifact for Ryo (G3-equivalent), potential adoption signal for the sibling skill's design choices
- Metrics: stars/installs on whichever channel it's distributed through / any GitHub issue or mention referencing it
- Deliberately ignoring: localization beyond English, a hosted/SaaS version, any dependency on this repo's private infra (hermes-relay etc.) — kept intentionally dependency-free
- Devil's advocate: 3 objections (below) → 1 partially addressed, 2 accepted as unresolved risk

## Devil's advocate (separate-context pass, 2026-07-10)

1. **"The core value is one Claude prompt away."** A builder can just ask Claude for 3 reasons an idea fails and get most of this skill's value with zero install. *Addressed (partially):* the skill's actual differentiator isn't the devil's-advocate prompt itself — it's (a) a persistent, versioned artifact instead of a one-off chat answer, and (b) a hard rule that blocks moving to implementation without a real signal, which a one-off suggestion doesn't enforce. This is a real weakness the sheet doesn't fully resolve — a one-off prompt is genuinely competitive for casual use.
2. **The guard-skill genre is already crowded in this exact repo** (yagni-guard, biz-ops-guard, claude-env-audit, structured-task-execution). *Not resolved — accepted as risk.* This skill did not run its own "list alternatives first" research step against itself before writing the sheet; that's a real gap, not just a hypothetical one.
3. **The distribution plan has no warm channel** — 2 of the 3 "real users" are hypothetical, and all 3 distribution channels are cold. *Accepted, not fabricated around.* Per this skill's own principle (freeze/kill is not failure), if the 4-week deadline passes with zero signal, that's a valid, honest outcome to record — not something to route around with a channel that doesn't actually exist yet.

## Honest conclusion

No real signal exists yet, and 2 of 3 devil's-advocate objections remain genuinely unresolved rather than talked away. Per this skill's own hard rule: don't claim "world-wide adoption" as an achieved goal — this is "accepted, proceeding under portfolio/first-test rationale" until real distribution produces a real signal (or doesn't, within 4 weeks, in which case the honest next step is freeze/kill per this skill's own criteria — not quietly extending the deadline). The next concrete action is distribution, not further design work.
