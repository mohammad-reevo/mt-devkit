---
name: mt-plan
description: Convergent phase of my personal dev workflow. Consumes ~/.claude/spec/<slug>-scope.md, creates + enters the feature worktree (via mt-worktree) up front, then descends to concrete detail — goals, ordered task breakdown with file-level changes, verification strategy. Writes ~/.claude/spec/<slug>-plan.md for mt-implement to consume. Use after mt-scope has converged on a direction, or directly for small ideas (inline mini-scope).
---

> Personal rebuild — `mt-` prefix temporary (stripped at graduation to standalone repo).
> Part of the funnel: **mt-scope → mt-plan → mt-implement → mt-verify → mt-babysit → mt-done**
> (see `~/.claude/spec/my-devkit-design.md`).

# mt-plan — turn a direction into a plan

You are running the **convergent** phase. File paths, function names, schemas — everything
mt-scope banned — is now legal and expected. The output is a plan concrete enough that
mt-implement never has to make a design decision.

## Input check (always first)

Find the idea's existing files — **never re-derive a slug from prose**. Glob
`~/.claude/spec/*-scope.md` and `*-plan.md`, match against the idea, and confirm with me
if more than one could fit. The **name** decided in mt-scope is the slug authority — read it
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
  running mt-scope.

## Set up the worktree (before planning)

Before any planning work, put us in the isolated worktree so research and mt-implement both run
in it (and the worktree gate is satisfied):

- Invoke **`mt-worktree` `create <name>`** — it makes `worktrees/<name>/` with the sub-repos on
  `mohammad/<name>` (env copied + backend-path fixed) and switches the session in. If a worktree
  for `<name>` already exists (a revision, or you made one), it's reused — just confirm we're
  inside it. Skip only if I explicitly say I don't want a worktree.
- (Scope-less quick plan: pick the name first, then this same worktree step.)

## The three beats

### 1. Deep research
This is where real investigation happens — dispatch Explore agent(s) to map the actual code
the plan will touch: exact files, existing patterns to follow, integration points, what the
tests around this area look like. Unlike mt-scope's reconnaissance, depth is the point —
the plan's tasks must name real files and real seams, not guesses.

### 2. Resolve and break down
- **Resolve every open question** from the scope — by research where the code answers it,
  by asking me where it's a judgment call. No question survives into the plan unresolved
  unless explicitly marked as a deliberate runtime decision.
- **Break the work into ordered tasks.** Each task: one coherent change with a clear
  done-signal. Small enough to verify independently, big enough to be worth a checkbox.
- **Kickback rule:** if research shows the chosen direction itself is wrong (not just a
  detail), stop. Say what broke and recommend re-running mt-scope — don't quietly re-scope
  inside the plan.

### 3. Converge and write
Present the full plan in conversation first. Discuss; I approve. Only then write
`~/.claude/spec/<slug>-plan.md`:

```markdown
# <Idea title> — Plan

> Scope: <slug>-scope.md  (or: scope-less — mini-scope below)
> Repo: <repo root the plan targets — where checks and git run>

## Goals
What done looks like, concretely — concretized from the scope's Chosen direction
(the scope stays at altitude; making it concrete is this skill's job, not invented scope).

## Non-goals
Inherited from scope's Out of scope, plus anything planning excluded.

## Decisions
How each of scope's open questions was resolved, one line each.

## Tasks
- [ ] 1. <Task name> — files: <paths>. <What changes, specifically.>
      Done when: <observable signal — test passes, endpoint returns X, …>
- [ ] 2. …
Ordered. Dependencies implicit in the ordering; note explicitly if a task
can run out of order.

## Verification
- **Coding checks** — exact commands: tests to run/write (concretized from the scope's Testing
  call — don't invent test scope the scope didn't warrant), lint, types.
- **Manual checks** — what mt-implement's close-out must prove by hand:
  browser flows, API calls, data states.
```

Close by telling me the plan path (we're already in the worktree). Return to `/mt-workflow` to
continue the funnel — it owns what comes next.

## Guardrails

- **Concrete or absent.** A task that says "update the relevant files" isn't a task.
  Every task names its files and its done-signal, or it doesn't go in.
- **The plan decides, implement executes.** If you find yourself writing "decide at
  implementation time", either decide it now or put it in Decisions as an explicit,
  justified deferral.
- **No invented requirements.** Plan what the scope chose. New gaps → ask me, don't pad.
- **Content over format.** When revising, change structure freely but never silently drop
  detail — signatures, snippets, and rationale survive edits.
- **One artifact, no state.** No session files, no hooks, no auto-transition (Wave 1: I drive).
