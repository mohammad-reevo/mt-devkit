---
name: workflow
description: Orchestrates my personal dev funnel — drives an idea or Linear ticket from raw idea to a watched PR through scope → plan → implement → verify → babysit, with two hard gates (after scope and after plan, each needing my explicit go-ahead) and kickback routing, then stops at explicit done. Detects phase from the spec files + git/PR state. Also a status view across every in-flight idea. Use to run the whole workflow, resume mid-funnel, or check where things stand. Triggers on "run the workflow", "take this through the funnel", "drive <idea/TICKET-ID> through", "where am I", "workflow status".
---

> Personal rebuild — self-contained, no devkit dependency.
> The conductor over the funnel: **scope → plan → implement → verify → babysit
> → done** (see `~/.claude/spec/my-devkit-design.md`).

# workflow — drive an idea through the funnel

You are the **conductor**. You invoke the phase skills (via the Skill tool) and manage the
handoffs — you never do their work. Compose, never duplicate: each phase's logic lives in its
own skill. The spec files + git/PR state **are** the state (Wave 1: no session file).

Purpose: drive an idea from raw idea to a **PR that's open and being watched** (scope → plan →
implement → verify → babysit), enforce both hard gates, route kickbacks — then stop at the
explicit close-out (done).

## Two modes

- **No specific idea given** (or "status" / "where am I") → **status view** (below).
- **An idea or ticket given** → **drive it** (below).

## Status view

Scan `~/.claude/spec/*-scope.md` and `*-plan.md`. For each idea, one line:

- scope file only → **scoped — ready to plan**
- plan, some tasks `[ ]` → **implementing — N/M tasks done**
- plan all `[x]`, no PR for `mohammad/<name>` → **built — ready to verify**
- plan all `[x]`, PR open → **in review — <PR link> (babysit watching / done when green)**

The last two rows need a quick `gh pr list --head mohammad/<name>` per built idea. Read-only —
this advances nothing.

## Drive it

### 1. Locate the idea & detect the phase
Resolve the name (fresh idea → scope will decide it; existing → read the `> Name:` from the
scope/plan file; a Linear ticket → identifier lowercased). Detect where it stands:

| On disk / state | Enter at |
|---|---|
| no `<name>-scope.md` | **scope** |
| scope only | **plan** |
| plan with unchecked `[ ]` tasks | **implement** |
| plan all `[x]`, no PR for `mohammad/<name>` | **verify** |
| plan all `[x]`, PR open | **babysit** — pick the watch back up; done (when green) is mine |

State where we are and the phase you're entering. Invoking me mid-funnel is my go-ahead to run
that phase.

### 2. Run phases, respecting the gates & stops
Invoke each phase skill and let it run to completion — each handles its own internal pauses
(scope agrees the direction, plan approves the plan, verify is user-directed). Then:

- **scope → plan — HARD GATE.** Scope is the deep-context phase: a full, in-depth look at the
  work before we commit more to it, so I have real context and a conversation going. After the
  scope file lands, **stop and give me a quick summary of what we're doing** — the direction,
  the approach we picked and why, and the testing call. Then handle open questions properly
  instead of dumping them on me:
  - **Resolve what you can yourself first.** For each open question, try to answer it — a
    targeted read/research pass, or reasoning from what scope already found. Don't punt a
    question you could settle in a minute. Say which ones you resolved and how.
  - **Ask the rest straight.** Surface only the questions that genuinely need *my* call, and
    ask each as a clear, direct, answerable question — with your recommendation — not a vague
    "things to resolve" list. Use **AskUserQuestion** when they're discrete choices so I can
    just pick.

  Then wait for my **explicit go-ahead** before starting plan. Never cross this on your own.
- **plan → implement — HARD GATE.** Plan approval covers the *breakdown* — it is me agreeing the
  design is right, not me saying start building. After the plan file lands, **stop** and wait for
  my explicit go-ahead. Report the plan path, and if plan drew a `make-diagram` diagram, leave it
  in view: that's what I'm reading before I commit to the build. Never cross this on your own.
  (plan creates + enters the worktree at its start.)
- **implement → verify — no gate, but verify is user-directed.** implement ends at a pushed,
  reviewed, green branch (no PR). Flow into verify — it pulls me in to direct the testing and
  then opens the PR. This is my post-implement touchpoint.
- **verify → babysit — no gate.** Once verify opens the PR, report the PR link and **go straight
  into babysit** — don't ask, don't wait for me. A freshly-opened PR always needs watching, so
  making me say "yes, watch it" was pure friction; the only thing that ever came of the pause was
  a delay. Invoke the `babysit` skill and let it run its poll loop.
- **babysit → STOP.** babysit paces itself to a ~25-minute CI run (≈10-minute polls, so review
  comments still surface quickly) and reports what it finds — it does **not** fix, and reaching
  green does **not** close anything out. **done stays explicit**: `/done` is mine to invoke once
  CI's green and threads are resolved. Surface it as the next move; never run it.

### 3. Route kickbacks
- plan finds the **direction** wrong → back to **scope** (revision) → re-summarize at the
  gate → forward again.
- implement hits **structural drift** → back to **plan** (revision) → forward into implement.
- verify's own fixes stay in verify (post-build); only a structural problem kicks to plan.

Sub-skills are re-entrant and detect their own files — your job is to route and pick the flow
back up.

## Guardrails

- **Conduct, don't perform.** Never write scope/plan/implement content or open the PR yourself —
  always through the owning skill.
- **The post-scope gate is real** — a genuine summary + my actual go-ahead, never a rubber-stamp.
  Scope earns the commitment to plan.
- **So is the post-plan gate.** A written plan is not consent to build. Wait for the word, even
  when the plan is obviously good and the tasks are obviously next.
- **babysit auto-runs as the tail; done never does.** Flowing verify → babysit is the drive
  finishing its job. `/done` is the one transition that stays mine — the workflow only surfaces it.
- **No new state.** Detect from spec files + git/PR every time; never cache the phase or invent a
  tracking file (Wave 1: files are the contract, I drive).
- **One idea per drive.** The status view is the cross-idea overview.
