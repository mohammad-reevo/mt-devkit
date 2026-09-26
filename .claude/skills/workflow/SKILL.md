---
name: workflow
description: Orchestrates my personal dev funnel — drives an idea or Linear ticket from raw idea to a watched PR through scope → plan → implement → verify → babysit, with one hard gate (after plan, needing my explicit go-ahead — scope hands off on its own once no question needs my call) and kickback routing, then stops at explicit done. Runs in one of three modes — assistant (default), agentic (takes the recommended option at every gate), investigate (scope only). Detects phase from the spec files + git/PR state. Also a status view across every in-flight idea. Use to run the whole workflow, resume mid-funnel, or check where things stand. Triggers on "run the workflow", "take this through the funnel", "drive <idea/TICKET-ID> through", "where am I", "workflow status".
---

> Personal rebuild — self-contained, no devkit dependency.
> The conductor over the funnel: **scope → plan → implement → verify → babysit
> → done** (see `~/.claude/spec/my-devkit-design.md`).

# workflow — drive an idea through the funnel

You are the **conductor**. You invoke the phase skills (via the Skill tool) and manage the
handoffs — you never do their work. Compose, never duplicate: each phase's logic lives in its
own skill. The spec files + git/PR state **are** the state (Wave 1: no session file).

Purpose: drive an idea from raw idea to a **PR that's open and being watched** (scope → plan →
implement → verify → babysit), enforce the one hard gate, route kickbacks — then stop at the
explicit close-out (done).

## Status or drive

- **No specific idea given** (or "status" / "where am I") → **status view** (below).
- **An idea or ticket given** → **drive it** (below).

## Modes

A drive runs in one of three modes. Every gate in the funnel — a clarifying question, a judgment
call, the post-plan gate, a comment table waiting for "go" — cites this section and applies its
decision rule; the rule lives here and nowhere else.

| Mode | At a gate |
|---|---|
| **assistant** (default) | Present the options with the recommendation marked, and wait. Today's behavior. |
| **agentic** | Take the recommended/default option, don't wait, and record it as one line: `Assumption: <what was decided>`. |
| **investigate** | Report the open question in the findings; don't decide it. The drive stops after scope. |

- **Choosing it.** An explicit word in the invocation (`workflow agentic <idea>`, `workflow
  investigate <idea>`), else assistant. Scope records it once in the scope file's header
  (`> Mode: <mode>`), so every later phase and a resumed session read the same mode. A later
  explicit mode word overrides it and updates that line.
- **Where an Assumption lands.** In the phase's spec file — scope's `## Assumptions`, plan's
  `## Decisions` — and verify carries them into the PR body, which outlives both files.
- **No recommended option, no Assumption.** A gate with nothing to recommend stops in every mode.
- **Agentic never skips a real failure** — these stop in every mode: implement's escalation after
  ~2 failed fix attempts or reviewer cycles, implement's structural drift kicking back to plan,
  babysit's same-check-failed-on-two-pushes stop. `done` stays manual, and I alone merge,
  request reviews, and message people.
- **Agentic covers only my own PR's flow.** `pr-review` of a teammate's PR is never agentic —
  posting there is outward-facing — and a human comment asking to talk still comes to me.

## Status view

Scan `~/.claude/spec/*-scope.md` and `*-plan.md`. For each idea, one line:

- scope file only → **scoped — ready to plan** (plan didn't follow scope; pick it back up), or
  **investigated — scope only** when its header reads `> Mode: investigate`
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
| scope only | **plan** — unless `> Mode: investigate` and I named no other mode: stop |
| plan with unchecked `[ ]` tasks | **implement** |
| plan all `[x]`, no PR for `mohammad/<name>` | **verify** |
| plan all `[x]`, PR open | **babysit** — pick the watch back up; done (when green) is mine |

State where we are and the phase you're entering. Invoking me mid-funnel is my go-ahead to run
that phase.

### 2. Run phases, respecting the gates & stops
Invoke each phase skill and let it run to completion — each handles its own internal pauses
(scope agrees the direction, plan approves the plan, verify is user-directed). Then:

- **scope → plan — no gate; the scoping discussion is the checkpoint.** Scope is the
  deep-context phase: a full, in-depth look at the work, with every question that needs my call
  asked in conversation. Once none remain, scope writes its file without waiting for a
  "we're done". Once the scope file lands, **go straight into plan — don't summarize, don't
  re-ask, don't wait for me** (investigate mode excepted — next bullet). Everything I need to weigh in on belongs *inside* the scoping
  discussion (scope's Discuss phase owns asking it); whatever still lands in the file's Open
  questions is plan's to resolve by research or to ask about as a judgment call. My next review
  point is the written plan.
- **investigate → STOP after scope.** The scope file is the deliverable: no plan, no worktree, no
  plan file. Report the path and the open questions it carries.
- **plan → implement — HARD GATE.** Plan approval covers the *breakdown* — it is me agreeing the
  design is right, not me saying start building. After the plan file lands, **stop** and wait for
  my explicit go-ahead. Report the plan path, and if plan drew a `make-diagram` diagram, leave it
  in view: that's what I'm reading before I commit to the build. Never cross this on your own in
  assistant mode; in agentic, report the same and proceed into implement (per § Modes).
  (plan creates + enters the worktree at its start.)
- **implement → verify — no gate.** implement ends at a pushed, reviewed, green branch (no PR).
  **Go straight into verify — don't ask, don't wait for me.** Once running, verify opens the PR
  and then proves whatever it can prove unattended. Verification that needs me at a keyboard is
  written into the PR body as a pending check list — my touchpoint is when I pick the PR up to
  review it, not a pause anywhere inside the drive.
- **verify → babysit — no gate, with an explanation in between.** Once verify opens the PR,
  report the PR link, then run `pr-explanation` on it — the PR is the first thing I read, and the
  moment it opens is when I want orienting. Then **go straight into babysit** — don't ask, don't
  wait for me. A freshly-opened PR always needs watching, so making me say "yes, watch it" was
  pure friction; the only thing that ever came of the pause was a delay. Invoke the `babysit`
  skill and let it run its poll loop. The explanation is orientation, not a gate: it never waits
  for a reply before babysit starts.

  **This hop keys off the PR being open, not off verification having passed.** Manual testing is
  mine to schedule, so verification I couldn't run unattended rides along as an outstanding
  reminder — it never holds the drive. Only a *structural* problem stops here (kickback to plan);
  an expired credential or my being away from the keyboard does not.
- **babysit → STOP.** babysit paces itself to a ~25-minute CI run (≈10-minute polls, so review
  comments still surface quickly) and reports what it finds — it does **not** fix, and reaching
  green does **not** close anything out. It ends by announcing **"ready for your review"** with
  the PR link — that line comes first, because my review is the next step. **done stays
  explicit**: `/done` is mine to invoke after that review, once CI's green and threads are
  resolved. Surface it after the ready line as the move that follows; never run it — and surface
  any verification still outstanding alongside it, so I know what's left for me to run.
- **Review comments → `address-comments`, handed over by babysit.** When a poll finds unresolved
  threads, babysit schedules its next wakeup and then enters `address-comments` in the same turn.
  That is not auto-fixing: the skill triages every thread into a numbered report, finalizes it,
  and waits for my explicit go before it implements or replies — unless every comment verifies
  as Implement, in which case it executes from the report because there is nothing to decide
  (an agentic drive executes without waiting too, per § Modes).
  The gate I want — which comments get acted on — stays; the one I don't — whether to go and
  look at them — goes.

### 3. Route kickbacks
- plan finds the **direction** wrong → back to **scope** (revision) → once no question
  needs my call → straight back into plan.
- implement hits **structural drift** → back to **plan** (revision) → forward into implement.
- verify's own fixes stay in verify (post-build); only a structural problem kicks to plan.

Sub-skills are re-entrant and detect their own files — your job is to route and pick the flow
back up.

## Guardrails

- **Conduct, don't perform.** Never write scope/plan/implement content or open the PR yourself —
  always through the owning skill.
- **The scope → plan hop is gate-less.** The trigger is the scope file landing — not a phrase
  from me. Scope stops only for questions that need my call; I halt it myself if I want to
  steer, and my review point is the written plan. An investigate drive never takes the hop.
- **The post-plan gate is real.** A written plan is not consent to build. Wait for the word, even
  when the plan is obviously good and the tasks are obviously next. Only an agentic drive crosses
  it without one (§ Modes).
- **Only that one is a gate.** Naming phases when you kick me off ("scope, plan and implement
  without me") is me listing what's pending, not withholding permission for the rest. A
  gate-less hop stays gate-less; an incidental phase list in the kickoff never invents a second
  gate.
- **babysit auto-runs as the tail; done never does.** Flowing verify → babysit is the drive
  finishing its job. `/done` is the one transition that stays mine — the workflow only surfaces it.
- **Outstanding manual testing is never a gate.** The drive runs to a watched PR whether or not
  I've tested it yet; pending verification is reported as a reminder, not a reason to stop one
  step short of done.
- **No new state.** Detect from spec files + git/PR every time; never cache the phase or invent a
  tracking file (Wave 1: files are the contract, I drive).
- **One idea per drive.** The status view is the cross-idea overview.
