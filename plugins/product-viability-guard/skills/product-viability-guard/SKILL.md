---
name: product-viability-guard
description: A business/go-to-market viability design skill for anyone building an app, tool, or skill meant for other people to use. Requires at least one real user signal (a real reply, a signup, actual usage) before implementation begins, then runs a one-page viability sheet, a devil's-advocate pass, a pre-release checklist, and a monthly review. Use when designing a new app/tool/skill meant for others, right after requirements gathering, right before release, when an existing product "isn't being used" or "is a pain to maintain", or when the user says "think about the business/product side" or "make this viable as a product". English keywords: product viability, go-to-market, onboarding design, time-to-first-value, maintenance budget, differentiation, monetization check, real user signal.
---

# Product Viability Guard

Goal: turn "something that works" into "something people keep using".
Core principle: **implementation starts only after you have evidence a real person wants it (a real signal).**
A design process that can be passed with imagined personas and self-generated objections only produces an
elaborate form of self-deception — it doesn't prevent the thing that actually kills products.

Use this right after scoping/requirements ("what to build"), and right before scope-minimization work
("how to build the smallest version").

## When to use

- Designing an app/tool/skill meant for other people to use.
- Requirements are done, implementation hasn't started yet.
- Right before release/launch/distribution.
- An existing product "isn't used", "is a pain to maintain", or "has no differentiation".
- Someone says "think about the business side" or "make this a real product".

## Scope check (do this first)

| Target | Apply? |
|---|---|
| Personal tool (nobody else will use it) | **Skip this skill.** Just keep scope minimal. |
| Something meant for other people | **Full process.** Everything below applies. |
| Portfolio/learning project, used or not | Still go through the sheet, but items without a real signal can be marked "accepted — portfolio mode" instead of blocking. |

"Portfolio mode" = building it is worth doing for the learning/portfolio value even if nobody else ever uses it. Say so explicitly in the sheet rather than silently skipping the gate.

## Choosing a path (one question, before implementation)

**Can you build a working demo of the single core value prop in half a day or less?**

```
Yes → Fast path:
  Build the demo → send it to 3 real people → record their reaction as your real signal
  → fill in the sheet afterward (retroactive filling is explicitly allowed)

No (bigger build) → Design-first path:
  Fill in the sheet → devil's advocate pass (pitch polish) → send a one-line pitch to 3 real people
  → get a real signal → then start implementation
```

**Definition of a real signal** (any one of these; an imagined persona's reaction or an AI agent's
self-generated objection does not count):

- A real person replying "I'd use this" / "I want to try this"
- A signup, pre-order, or waitlist join
- Actual usage of a demo (something you can verify — access logs, etc.)

If you don't get a signal: (1) rework the pitch and resend (up to 2 more times), (2) mark it
"accepted — portfolio mode" and proceed anyway, or (3) don't build it. **Proceeding to implementation
without a real signal and without explicitly choosing one of these three is the one hard rule.**

If you're applying this skill retroactively (already built, about to release), fill in the sheet now
and check honestly whether you already have a real signal. If not, choose one of the three options above.

## Deliverable: the one-page viability sheet

Fill in exactly this (put it in `docs/product-viability.md`, or at the top of / next to the skill's main file). **Every line is 1–2 sentences. If it doesn't fit on one page, you're overwriting.** Being able to fill it in top to bottom, in order, is itself the go/no-go signal — there's no separate checklist to pass first.

```markdown
# <product> Viability Sheet
- Value prop: (who) can (achieve X) without (doing what they do today)
- 3 real users (traits + pain + situation, no real names in public docs):
- Real signal (from whom / what / when):
- Onboarding: steps __ / minutes __ / prerequisites:
- Keep-it-alive: __ min/week budget / what breaks it: / failure alert path: / kill criteria:
- Distribution: channel / first 10 users / deadline: __ weeks after launch:
- Revenue: who pays how much, or what you get back if it's free (portfolio value, leads, learning)
- Metrics: new users / 7-day return rate / referrals
- Deliberately ignoring:
- Devil's advocate: objections → how you addressed them:
```

Example: [examples/sheet-example.md](examples/sheet-example.md) — use it as the calibration for tone and granularity.

- The "real signal" line can't be empty when implementation starts — that's the hard rule made concrete.
- "Deliberately ignoring" is only for things you've decided to skip — don't mix in things that are still pending.
- Don't put real names in a public repo or in outbound research queries; use traits/initials instead.

### Lightweight monetization check

If you're considering charging, validate willingness-to-pay before building payment infrastructure: a smoke
test (a pre-order landing page, measuring clicks/signups), 1:1 conversations in an existing community, or a
behavioral proxy (asking for a referral or extra effort as a proxy for enthusiasm). Developer-facing tools are
notoriously hard to monetize — your buyer can often build it themselves.

## Devil's advocate (5-minute pass, before you send the pitch)

Whoever wrote the sheet or the pitch (including an AI) tends to be optimistic. Before sending the pitch to
real people, have **a separate context/agent** read the sheet and name 3 reasons the target users wouldn't
use or switch to this. Any objection you can't refute in one sentence goes back into the sheet (either fix
the plan or move it to "deliberately ignoring"). Record the objections and how you handled them in the
sheet's devil's-advocate line. This is a polish step before you go get a real signal — it is not a substitute
for one. If no separate agent is available, sleep on it and redo this the next day.

## The three perspectives

Five traditional dimensions (onboarding, maintenance, operations, marketing, differentiation) collapsed into
three questions that actually matter for an indie build.

### 1. Why you, not the alternative (differentiation + value prop)

- **List alternatives first.** Competitors aren't just similar apps — always include "doing it manually",
  "a spreadsheet", "an existing SaaS", and "just asking ChatGPT directly".
- Pick **one** reason to switch. Ten features that are each 10% better lose to one that's 10x better.
  Name your one source of durable advantage (proprietary data, operational know-how, a unique combination,
  a niche). Assume features themselves will be copied.
- Nail the **one-sentence value prop** first: "(who) can (achieve X) without (what they do today)". If a
  feature doesn't serve that sentence, don't build it.
- **Searchability**: put words people actually search into the name and description — a plain, searched
  term beats a clever made-up one.
- No differentiation at all → don't build it, or explicitly mark it "portfolio mode".

### 2. How fast someone gets value (onboarding)

- **Time-to-first-value ≤ 5 minutes, ≤ 3 steps.** Count the steps at design time.
- Prerequisites (API keys, billing, environment, accounts) go in a **table at the top** of the README.
- **Zero-config first** — it should work by default; settings are something you touch after it already works.
- If it's launched without prerequisites configured, don't fail silently — tell the user exactly what's missing.
- **Write the exit path too** (how to uninstall, how to get your data out). A visible exit lowers the barrier to trying it.

### 3. Whether it survives being left alone (maintenance, ops, continued distribution)

- **3-month abandonment test**: does it still work if you don't touch it for 3 months? For each external
  dependency, write one line: what breaks, how you'd notice, what the fallback is.
- **Declare a maintenance budget**: N minutes/week. Two consecutive weeks over budget triggers a decision
  to scale down, freeze, or kill it — don't let it drag on. Use semver + a changelog; don't silently ship
  breaking changes once someone depends on it. Pick **one** feedback channel, not several.
- **Runbook**: list every manual step a human still has to do. The ideal is zero. Make sure failures reach
  you somehow — automation with no failure alert eventually breaks silently. Estimate marginal cost per
  user/use; don't design something that loses money as it grows. State your guarantee level explicitly
  ("best-effort, solo-maintained" is fine — saying nothing is the worst option).
- **Distribution is ongoing, not a one-time launch.** Re-launch with every update. Don't mistake a few
  quiet weeks for "no demand" — giving up too early is one of the most common reasons solo-built products
  die; don't confuse a product flaw with a distribution gap. Keep going until your monthly review says otherwise.

## Research while filling the sheet

Use whatever research capability you actually have (web search, talking to people directly, community
forums) — this skill doesn't prescribe a specific tool. Only research three things; anything more is
overkill:

1. **Do the alternatives really exist** — what do your target users currently use to solve this?
2. **What's the friction** — what do they complain about with existing options? (candidate reasons to switch)
3. **What words do they actually search for** — for naming and discoverability.

Put the results into the relevant sheet lines in 1–2 sentences each; don't produce a separate research
report. One pass is usually enough (two at most) — if results are thin, fill the sheet provisionally and
move on; revisit at the pre-release checklist.

## First action once you have a real signal

Don't let the design stop at paperwork. The moment you have a real signal (or a working fast-path demo),
draft the **first 10 lines of the README** (one-sentence value prop, a demo slot, the 3-step onboarding)
before writing more code. If the sheet can't compress into those 10 lines, the sheet itself is still vague — go fix it.

## Pre-release checklist

- [ ] Got a real signal (or explicitly marked "deliberately ignoring — portfolio mode")
- [ ] Prerequisites are a table at the top of the README
- [ ] A clean-environment install gets to first value in under 5 minutes (verify it yourself if you can; if not, leave this unchecked rather than guessing)
- [ ] The first 10 lines of the README communicate the value prop + a demo
- [ ] Launching without prerequisites configured produces a self-explanatory error
- [ ] There's a changelog / version number
- [ ] There's exactly one feedback channel, and it's documented
- [ ] There's a failure-alert path (for anything automated)
- [ ] The guarantee level is stated
- [ ] The viability sheet is filled in
- [ ] The devil's-advocate pass happened and its objections were addressed

## Monthly review (5 minutes)

Three metrics are enough: **① new users ② returned within 7 days ③ referred/recommended by someone else.**
No analytics stack needed — hosting logs or a manual tally are fine. Decide from those three: **improve /
keep as-is / freeze / kill.**

- Two consecutive maintenance-budget overruns, or zero users for 2 months → seriously consider freeze or kill.
- Freezing or killing is not failure — it's a result. Write down what you learned (why it wasn't adopted) and close it out; it's still worth something (a portfolio story, a lesson).

## Don't over-engineer the process itself

This applies YAGNI to itself.

- Don't build a monitoring dashboard, analytics stack, or automated release pipeline before you have 10 users. Email/Slack is enough for a failure alert.
- Don't add billing, licensing, or i18n until a real user actually asks for it.
- Don't write more documentation than the sheet + checklist.
- If you deliberately cut a corner, leave one line in "deliberately ignoring" explaining the limit — same spirit as a scope-minimization marker comment.

## Sync policy

This skill is a portable, English, dependency-free distillation of a Japanese sibling skill maintained in a
private repo. **They are not kept in sync automatically** — that would violate the anti-over-engineering
principle above. Ports get applied manually, at most quarterly, when something proven there is worth
bringing here.
