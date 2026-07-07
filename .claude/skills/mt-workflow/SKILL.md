---
name: mt-workflow
description: Orchestrates my personal dev funnel — drives an idea or Linear ticket from raw idea to an open PR through mt-scope → mt-plan → mt-implement → mt-verify, with a hard post-scope gate (summary + my approval) and kickback routing, then hands off to opt-in mt-babysit + explicit mt-done. Detects phase from the spec files + git/PR state. Also a status view across every in-flight idea. Use to run the whole workflow, resume mid-funnel, or check where things stand. Triggers on "run the workflow", "take this through the funnel", "drive <idea/TICKET-ID> through", "where am I", "workflow status".
---

> Personal rebuild — `mt-` prefix temporary (stripped at graduation to standalone repo).
> The conductor over the funnel: **mt-scope → mt-plan → mt-implement → mt-verify → mt-babysit
> → mt-done** (see `~/.claude/spec/my-devkit-design.md`).

# mt-workflow — drive an idea through the funnel

You are the **conductor**. You invoke the phase skills (via the Skill tool) and manage the
handoffs — you never do their work. Compose, never duplicate: each phase's logic lives in its
own skill. The spec files + git/PR state **are** the state (Wave 1: no session file).

Purpose: drive an idea from raw idea to an **open PR** (scope → plan → implement → verify),
enforce the one hard gate, route kickbacks — then hand off to the opt-in tail (babysit) and
explicit close-out (done).

## Two modes

- **No specific idea given** (or "status" / "where am I") → **status view** (below).
- **An idea or ticket given** → **drive it** (below).

## Status view

Scan `~/.claude/spec/*-scope.md` and `*-plan.md`. For each idea, one line:

- scope file only → **scoped — ready to plan**
- plan, some tasks `[ ]` → **implementing — N/M tasks done**
- plan all `[x]`, no PR for `mohammad/<name>` → **built — ready to verify**
- plan all `[x]`, PR open → **in review — <PR link> (babysit / done when green)**

The last two rows need a quick `gh pr list --head mohammad/<name>` per built idea. Read-only —
this advances nothing.

## Drive it

### 1. Locate the idea & detect the phase
Resolve the name (fresh idea → mt-scope will decide it; existing → read the `> Name:` from the
scope/plan file; a Linear ticket → identifier lowercased). Detect where it stands:

| On disk / state | Enter at |
|---|---|
| no `<name>-scope.md` | **scope** |
| scope only | **plan** |
| plan with unchecked `[ ]` tasks | **implement** |
| plan all `[x]`, no PR for `mohammad/<name>` | **verify** |
| plan all `[x]`, PR open | **in review** — babysit (opt-in) / done (when green) |

State where we are and the phase you're entering. Invoking me mid-funnel is my go-ahead to run
that phase.

### 2. Run phases, respecting the gates & stops
Invoke each phase skill and let it run to completion — each handles its own internal pauses
(mt-scope agrees the direction, mt-plan approves the plan, mt-verify is user-directed). Then:

- **scope → plan — HARD GATE.** Scope is the deep-context phase: a full, in-depth look at the
  work before we commit more to it, so I have real context and a conversation going. After the
  scope file lands, **stop and give me a quick summary of what we're doing** — the direction,
  the approach we picked and why, the testing call, and any open questions. Then wait for my
  **explicit go-ahead** before starting plan. Never cross this on your own.
- **plan → implement — no gate.** mt-plan already got my approval before writing the plan; that
  *is* the checkpoint. Flow straight in. (mt-plan creates + enters the worktree at its start.)
- **implement → verify — no gate, but verify is user-directed.** mt-implement ends at a pushed,
  reviewed, green branch (no PR). Flow into mt-verify — it pulls me in to direct the testing and
  then opens the PR. This is my post-implement touchpoint.
- **verify → STOP.** Once mt-verify opens the PR, the auto-drive is **done**. Surface the next
  moves but **don't run them**: **mt-babysit is opt-in** (never auto-start — my
  `feedback_babysit_opt_in` rule), and **mt-done is explicit** (`/mt-done` when CI's green +
  threads resolved). Report the PR link and stop.

### 3. Route kickbacks
- mt-plan finds the **direction** wrong → back to **mt-scope** (revision) → re-summarize at the
  gate → forward again.
- mt-implement hits **structural drift** → back to **mt-plan** (revision) → forward into implement.
- mt-verify's own fixes stay in verify (post-build); only a structural problem kicks to mt-plan.

Sub-skills are re-entrant and detect their own files — your job is to route and pick the flow
back up.

## Guardrails

- **Conduct, don't perform.** Never write scope/plan/implement content or open the PR yourself —
  always through the owning skill.
- **The post-scope gate is real** — a genuine summary + my actual go-ahead, never a rubber-stamp.
  Scope earns the commitment to plan.
- **Never auto-run babysit or done.** They're opt-in / explicit; the workflow only surfaces them.
- **No new state.** Detect from spec files + git/PR every time; never cache the phase or invent a
  tracking file (Wave 1: files are the contract, I drive).
- **One idea per drive.** The status view is the cross-idea overview.
