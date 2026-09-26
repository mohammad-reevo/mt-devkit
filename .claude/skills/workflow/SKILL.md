---
name: workflow
description: Orchestrates my personal dev funnel — drives an idea or Linear ticket from raw idea to a watched PR through scope → plan → implement → verify → babysit, with one hard gate (after plan, needing my explicit go-ahead — scope hands off on its own once no question needs my call) and kickback routing, then stops at explicit done. Runs in one of three modes — assistant (default), agentic (takes the recommended option at every gate), investigate (scope only). Detects phase from the spec files + git/PR state. Several tickets at once run as a project drive — one slice per ticket, scoped, planned, and built in parallel, each to its own PR on a shared project base. Also a status view across every in-flight idea and project. Use to run the whole workflow, resume mid-funnel, or check where things stand. Triggers on "run the workflow", "take this through the funnel", "drive <idea/TICKET-ID> through", "where am I", "workflow status".
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
- **Several ideas or tickets given** (`workflow <T1> <T2> …`), or a project name whose
  `~/.claude/spec/<project>-project.md` exists → **project drive** (§ Project drive).

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

Then scan `~/.claude/spec/*-project.md`: one block per project — its name, mode, and base — with
one line per slice (slug, ticket, status, PR link) read from the index. A slice's scope/plan files
carry `> Project:`; list them under their project, not again as standalone ideas.

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

## Project drive (several tickets)

`workflow [mode] [project <name>] <T1> <T2> …` drives several tickets or ideas at once, each as
a **slice** (default: one ticket = one slice) with its own normal `<slug>-scope.md` /
`<slug>-plan.md`, worktree, branch, and PR. Everything in § Drive it holds per slice; this section
is only what differs. § Modes applies unchanged — one mode for the whole project.

**Project + index.** The name is mine if given, else derived (kebab-case, from the shared theme or
the tickets' Linear project). The index `~/.claude/spec/<project>-project.md` is the main
session's only view of the project — update it at every status change:

```markdown
# <Project title> — Project

> Mode: <assistant | agentic | investigate>
> Repo(s): <every repo a slice touches>
> Base: mohammad/<project>-base

| Slice | Ticket | Status | Depends on | Base | Worktree | PR | Files |
|---|---|---|---|---|---|---|---|
| <slug> | <ID or —> | scoping | none | mohammad/<project>-base | <path> | — | [scope](<slug>-scope.md) · [plan](<slug>-plan.md) |
```

Status is one of `scoping / scoped / planned / building / PR open / merged`. Each slice's scope
and plan files carry `> Project: <project>`. Re-invoking with the project name resumes: read the
index, then detect each slice's phase with the § 1 table.

The main session stays at the **mt-devkit root** for the whole drive — never `EnterWorktree`: a
session that has entered one worktree is blocked from running git in the others. Every slice is
reached by path (`git -C <wt>/<repo>`, a subagent given `<wt>`).

1. **Scope, in parallel.** Name each slice (scope's naming rule), write the index, then dispatch
   one `scoper` per slice in **one message** (several Agent calls), each with scope's usual brief
   plus `> Project:`. Collect every scoper's open questions and resolve them in **one batched
   ask** (assistant) or take the recommended options as Assumptions (agentic) — per § Modes — and
   record the answers into each slice's scope file (re-dispatching a scoper only where an answer
   needs new research). A premise-changed report stops that slice alone. Investigate → stop here,
   every slice `scoped`.
2. **Branches.** In each affected repo, create the project base off fresh main — once, and never
   push to main: `git -C <primary repo> fetch origin`, then
   `git -C <primary repo> push origin origin/main:refs/heads/mohammad/<project>-base`.
   A slice's base is the project base — or, only when it would otherwise conflict or needs another
   slice's code, the slice it depends on (stack only when needed). **Migrations and paths another
   team owns** become their own slices with base `main`: feed the paths a scope names to
   `python3 .claude/lib/code_owners.py owners` (from primary salestech-be, paths on stdin); a
   `required` row for a team other than mine is such a path. Re-run it on the plans' task files once they
   land — a plan that turns up one splits the slice and re-plans both halves. A slice that needs a
   migration slice's table depends on it.
3. **Worktree per slice.** `worktree create <slug> --no-enter` per slice, **one after another**
   (the setup script fast-forwards the shared primaries, so parallel creates race). Then point
   each slice's branch at its base, per repo:
   `git -C <wt>/<repo> switch -C mohammad/<slug> origin/<base>`. A dependent slice is re-pointed
   at its dependency's branch once that is pushed.
4. **Plan, in parallel.** One `planner` per slice in one message, each with its worktree path;
   each records `> Project:`, `> Depends on:`, `> Base:`, and `> Worktree:` in its plan header.
   **One gate over all plans**: assistant — present every plan (per plan's close, one after
   another) and wait for one go; agentic — proceed (per § Modes). Status → `planned`.
5. **Build + PR, in parallel.** Run `implement` and then `verify` per slice with its explicit
   **plan path + worktree path**. Independent slices build together: a subagent can't dispatch the
   implementers implement needs, so parallel means **interleaved** — each round, one message
   carries the next dispatch (task, final checks, reviewer trio, commit) for every slice that is
   building. A dependent slice starts once the slice below has pushed, not once it merges. verify
   opens each PR against **its base** (project base, dependency branch, or main). The moment a
   slice's PR is open, set `PR open` + link and move on — **never wait on PR approval**; I review
   whenever. A slice that stops (escalation, kickback) stops alone; the rest carry on.
6. **Watch.** Once every slice PR is open, show the index table, run `pr-explanation` per PR,
   then `babysit <project>`. `done <project>` stays mine.

Landing — merging slices and the final base→main PR — is not yet part of the drive.

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
  tracking file (Wave 1: files are the contract, I drive). A project drive's index is the one
  exception, and it is a spec file like the rest (§ Project drive).
- **One idea per drive, or one project.** The status view is the cross-idea overview.
