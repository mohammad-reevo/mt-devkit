---
name: plan
description: Convergent phase of my personal dev workflow. Consumes ~/.claude/spec/<slug>-scope.md, creates + enters the feature worktree (via worktree) up front, then descends to concrete detail — goals, ordered task breakdown with file-level changes, verification strategy. Writes ~/.claude/spec/<slug>-plan.md for implement to consume. Use after scope has converged on a direction, or directly for small ideas (inline mini-scope).
---

> Personal rebuild — self-contained, no devkit dependency.
> Part of the funnel: **scope → plan → implement → verify → babysit → done**
> (see `~/.claude/spec/my-devkit-design.md`).

# plan — turn a direction into a plan

You are running the **convergent** phase. File paths, function names, schemas — everything
scope banned — is now legal and expected. The output is a plan concrete enough that
implement never has to make a design decision.

## Input check (always first)

Find the idea's existing files — **never re-derive a slug from prose**. Glob
`~/.claude/spec/*-scope.md` and `*-plan.md`, match against the idea, and confirm with me
if more than one could fit. The **name** decided in scope is the slug authority — read it
from the scope file's `> Name:` header (it also matches the filename).

- **`<slug>-plan.md` exists** → revision. Read it **and re-read `<slug>-scope.md`** — the
  scope may have been revised since (kickback loop); diff its Chosen direction against the
  plan before anything else. State where things stand, ask what changed. Revise — don't
  restart. If tasks carry `[x]` marks from a partial implementation: a tick survives only
  if the task's text is unchanged — any task you rewrite, split, or reorder loses its tick
  (note the resets in the plan).
- **Only `<slug>-scope.md` exists** → normal path. Read it; its Chosen direction is your
  brief, its Open questions are your TODO list, its Out of scope is your fence.
- **Neither exists** → scope-less quick plan. Say so in one line, pick a slug, and capture
  a 3-line mini-scope (problem, direction, out of scope) inline at the top of the plan
  file. Echo the slug + full filename back to me so downstream phases can be pointed at it
  verbatim. Don't force a small idea through ceremony — but if while planning the idea
  turns out NOT to be small (multiple viable directions, unclear goal), stop and recommend
  running scope.

## Set up the worktree (before planning)

Before any planning work, put us in the isolated worktree so research and implement both run
in it (and the worktree gate is satisfied):

- Invoke **`worktree` `create <name>`** — it makes `worktrees/<name>/` with the sub-repos on
  `mohammad/<name>` (env copied + backend-path fixed) and switches the session in. If a worktree
  for `<name>` already exists (a revision, or you made one), it's reused — just confirm we're
  inside it. Skip only if I explicitly say I don't want a worktree.
- (Scope-less quick plan: pick the name first, then this same worktree step.)
- **Project drive** — skip this step: `workflow` has already created the slice's worktree without
  entering it and dispatches the planner with its path (`workflow` § Project drive).

## The three beats

**Research, breakdown, and the write run in one `planner` agent** (`subagent_type: planner`),
dispatched once the worktree is up, so the deep reading stays out of the main thread. Give it the
scope file path (or the mini-scope), the plan file path, the worktree path, the mode, and any
feedback on a previous version. It follows the three beats below and the file template, and
returns the path, a short summary of the finished PR, the judgment calls it couldn't resolve
(options + recommendation), and whether a diagram would help — it never asks me anything. The
main thread keeps presenting the result, asking those calls, the diagram, and the gate.

**A revision is a fresh `planner`** with my feedback — the plan file is the contract, so it
carries no hidden state from the last dispatch.

### 1. Deep research
This is where real investigation happens — the planner maps the actual code the plan will touch
itself (a subagent can't dispatch Explore): exact files, existing patterns to follow, integration
points, what the tests around this area look like. Scope investigated only far enough to explain the
cause and check each approach's load-bearing assumption; here depth is the point — the plan's tasks
must name real files and real seams, not guesses.

### 2. Resolve and break down
- **Resolve every open question** from the scope — by research where the code answers it,
  by asking me where it's a judgment call. The scoping discussion was my last checkpoint and
  plan runs straight after it, so an ask here is a real interruption: research first, and ask
  only what the code genuinely can't answer. No question survives into the plan unresolved
  unless explicitly marked as a deliberate runtime decision.
- **Break the work into ordered tasks.** Each task: one coherent change with a clear
  done-signal. Small enough to verify independently, big enough to be worth a checkbox.
- **A salestech-be migration is always its own PR.** When the work adds or alters a table,
  split the Tasks into `### PR 1 — migration` (the migration file, `latest_revision.txt`,
  regenerated `schema.sql`, nothing else) and `### PR 2 — code, stacked on PR 1` (model,
  repository, `TableName`, CDC/Debezium exclusion, tests, feature logic). CI's migration-only
  check fails a PR that mixes the two. The mechanics are salestech-be's own and are read, not
  restated: `.claude/skills/db-migration/SKILL.md` (+ its `reference/cdc-awareness.md`) for PR 1,
  `.claude/skills/db-model-repo/SKILL.md` for PR 2 — funnel sessions don't auto-load sub-repo
  skills, so name the one each task follows in the task itself. In a project drive the migration
  is its own slice instead: don't split — report it, and `workflow` carves the slice out.
- **Kickback rule:** if research shows the chosen direction itself is wrong (not just a detail), the
  planner writes no plan and reports it; stop. Say what broke and recommend re-running scope — don't
  quietly re-scope inside the plan.

### 3. Converge and write
**Draw the shape when it earns one.** The planner says whether it does; the main thread draws it. If
the design is a pipeline with more than one consumer, or ≥3 steps where each step's output feeds the
next, invoke **`make-diagram`** and include its diagram in the walkthrough you hand me with the
finished plan — a fork is far clearer drawn than described, and that walkthrough is where I decide
whether the design is right. That skill owns the grammar *and* the call on when not to draw; don't
hand-roll a diagram here, and don't force one onto a plan that's a list of independent edits.

**Write the file, then ask — not the other way round.** Write
`~/.claude/spec/<slug>-plan.md` and review it with me from there. Don't render the whole plan
into a chat message and hold the write until I approve: a plan I have to reconstruct from prose
is harder to read than the file, and revising a written plan costs nothing. The file existing
is not a commitment to it.

The one thing I still get asked is a **genuine open question that isn't the whole plan** — a
judgment call left over from *Resolve and break down*, a direction that turned out ambiguous, a
decision only I can make. The planner writes each as a `Pending:` line under Decisions with its
recommendation; ask it on its own, get the answer, and re-dispatch the planner with it. Don't
dress the entire plan up as a question in order to ask it. In agentic mode, don't ask: the
planner takes the best-supported option and records it under Decisions as an Assumption (per
`workflow` § Modes).

The file:

```markdown
# <Idea title> — Plan

> Scope: <slug>-scope.md  (or: scope-less — mini-scope below)
> Repo: <repo root the plan targets — where checks and git run>
> Project: <project>   (project drive only — these four lines; omit them otherwise)
> Depends on: <none | other slice's slug>
> Base: <mohammad/<project>-base | mohammad/<dependency> | main>   (the PR's base)
> Worktree: <worktree path>

## Goals
What done looks like, concretely — concretized from the scope's Chosen direction
(the scope stays at altitude; making it concrete is this skill's job, not invented scope).

## Non-goals
Inherited from scope's Out of scope, plus anything planning excluded.

## Decisions
How each of scope's open questions was resolved, one line each. Agentic mode adds an
`Assumption: <what was decided>` line per call taken without me.

## Tasks
- [ ] 1. <Task name> — files: <paths>. <What changes, specifically.>
      Done when: <observable signal — test passes, endpoint returns X, …>
- [ ] 2. …
Ordered. Dependencies implicit in the ordering; note explicitly if a task
can run out of order.

## Verification
- **Coding checks** — exact commands: tests to run/write (concretized from the scope's Testing
  call — don't invent test scope the scope didn't warrant), lint, types. **Scope the *run* to the
  change** — name the specific test files/dirs covering the new code, never a whole-tree run
  (`pytest tests/unit`, `make pytest`). CI runs the full suite on the PR; local is targeted fast
  feedback only (see `local-test-scope.md`).
- **Manual checks** — what implement's close-out must prove by hand:
  browser flows, API calls, data states.
```

Close by telling me the plan path (we're already in the worktree) and, in one line, the direction
scope chose — scope hands off without asking me, so this is where I first see it. Then
**describe the finished PR** — what a reviewer opens and sees. Go surface by surface: which signatures gain an argument,
which docs gain or lose a section, what is a new file, what rebakes, what stays untouched. Add
anything the plan decided that goes beyond the ticket. A few sentences, or a short list of
surfaces. Then the diagram, if you drew one.

**Never walk me through the tasks.** The file is the task list and I am about to read it, so
"Tasks 1–5 …, Task 6 …" is a second rendering of the same thing — and it is the wrong altitude
for the decision I'm making here, which is whether the design is right (`response-altitude.md`).
What the diff ends up looking like is the one thing the file doesn't hand me at a glance.

Then **stop**. A written plan is not a green light: agreeing the plan is *right* is not me
saying start building. I want a beat to sit with it — implement is mine to trigger, and
`/workflow` enforces the same gate from the conductor's side, applying the mode's rule (per
`workflow` § Modes). If I come back with changes, a fresh planner revises the file in place.

## Guardrails

- **The walkthrough describes the PR, never the tasks.** The file is the task list.
- **Concrete or absent.** A task that says "update the relevant files" isn't a task.
  Every task names its files and its done-signal, or it doesn't go in.
- **The plan decides, implement executes.** If you find yourself writing "decide at
  implementation time", either decide it now or put it in Decisions as an explicit,
  justified deferral.
- **No invented requirements.** Plan what the scope chose. New gaps → ask me, don't pad.
- **Content over format.** When revising, change structure freely but never silently drop
  detail — signatures, snippets, and rationale survive edits.
- **One artifact, no state.** No session files, no hooks, no auto-transition (Wave 1: I drive).
