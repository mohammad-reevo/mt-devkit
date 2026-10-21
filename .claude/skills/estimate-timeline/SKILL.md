---
name: estimate-timeline
description: Estimate a project's timeline from measured velocity instead of a gut call — measure the throughput of a past project I name (PRs, tickets and net lines per week, from Linear and GitHub), size this project in the same units, cross-check against the critical path through its blocked-by graph scheduled over parallel streams, adjust for what the reference didn't have (another team's dependency, a vendor spike, a second repo, a real third-party API), and report an aggressive (peak) and a likely (average) date for each release stage — UAT, beta, all customers — with the assumptions next to them. Writes to the project's scratch dir only; I decide where the dates go. Standalone, and the `timeline` step of project-discovery. Triggers on "estimate the timeline", "how long will <project> take", "give me dates for <project>", "/estimate-timeline".
---

# estimate-timeline — dates I can defend

I don't trust my gut for a timeline, so this is a data-centric estimate: measure what a past
project actually did, size this one in the same units, and show the spread. The output is two
dates per release stage — aggressive and likely — never one number that hides the slip.

## 1. Settle the assumptions first

Ask once (AskUserQuestion), and write the answers at the top of the output:

- **The reference project** — a past project of mine whose Linear tickets and PRs set the unit
  rate. Prefer one with a similar shape (same codebase, same kind of work).
- **The project being estimated** — its Linear project or implementation doc, with the
  blocked-by relations between tickets.
- **Start date, who builds it, and how many parallel streams** (e.g. solo; or me
  orchestrating 2–4 agent streams).
- **Release-stage shape** — whether this project has a beta, and how long UAT and beta run.
  Stage names per `knowledge-base/concepts/release/release-stages.md`.
- **Known calendar constraints** — holidays, a freeze.

## 2. Measure the reference velocity

Dispatch a research subagent (Linear MCP + `gh`) so the raw data stays out of the main thread.
Per week of the reference project: PRs merged, tickets closed, net lines (with and without
tests), review turnaround. Then two rates:

- **Peak** — the best *sustained* window (two weeks or more), not a single spike. Say what made
  it peak: no blockers, a known codebase, agent-assisted.
- **Average** — across the project's active span. Exclude weeks I was mostly on other work,
  and say which weeks were excluded and why; an average dragged down by ramp weeks is not a
  likely rate.

## 3. Size this project in the same units

- **Tickets**, weighted S / M / L against a typical reference ticket — the ones bigger than
  anything the reference had (an inbound pipeline, a trigger, an AI agent) weighted up.
- **Net lines** as a second unit, when the reference's lines-per-ticket is meaningful.
- **Name the weakest number.** A size multiplier ("≈ 2x the reference") is a guess until a real
  ticket breakdown replaces it — say so, and re-run once the implementation doc or tickets exist.

## 4. Two methods, one answer

- **Throughput** — size ÷ rate, once at peak and once at average.
- **Critical path** — schedule the blocked-by graph: a duration per ticket (working days,
  including the PR), then list-schedule it over the agreed number of parallel streams. The
  longest chain is a floor no pace beats. A throwaway script in the scratch dir is the right
  tool once the graph has more than a handful of tickets.

When they disagree, the later one wins and the gap is a finding.

## 5. Adjust for what the reference didn't have

- **Another team's dependency** — eng complete is the *later* of our build and their delivery.
  List which tickets wait on whom, and which ETAs are still missing.
- **A vendor spike or test org** — what it gates, and by when it has to exist.
- **A second repo, a real third-party API, unbuilt infrastructure with no ticket.**
- **Calendar** — holidays and freezes from §1.

## 6. Output

Write `~/.claude/tmp/<project>/timeline.md` — nowhere else. Not the eng doc, not Linear, not
Slack: I place the dates.

```markdown
# <Project> — timeline estimate (<date>)

**Assumptions:** <reference project, start date, who, streams, stage shape — from §1>

**Reference rate:** peak <n>/wk (<window>, <why it peaked>) · average <n>/wk (<span>, <weeks excluded>)
**Size:** <n tickets (S/M/L), ~<n> net lines> — <the weakest number, named>

| Stage | Aggressive (peak) | Likely (average) | Basis |
|---|---|---|---|
| Eng complete | <date> | <date> | <throughput vs critical path; dependency floor> |
| UAT | <date> | <date> | <UAT length> |
| Beta | <date> | <date> | <or "skipped"> |
| All customers | <date> | <date> | <beta / pilot length, calendar> |

## What moves it
- <dependency, spike, unbuilt piece, calendar — each with the date it has to land by>

## In short
<The two dates for all customers, and the one thing most likely to move them.>
```

## Guardrails

- **Measured, not guessed** — every rate traces to the reference's real tickets and PRs.
- **Always both dates** — never collapse to the aggressive one; I choose what to commit to.
- **Scratch file only** — never write dates into a doc, a ticket or a message.
- **Re-run, don't patch** — when the ticket breakdown changes, redo §3–§5 rather than nudging
  the old dates.
