---
name: implement
description: Build phase of my personal dev workflow. Consumes ~/.claude/spec/<slug>-plan.md and conducts the build — dispatches a subagent per task to implement it and run its checks (keeping raw code and check output out of main context), tracks progress in the plan file, runs a final code-review subagent to finalize all coding, then commits and pushes a reviewed green branch. Hands off to verify for verification and the PR. Use after plan has produced an approved plan.
---

> Personal rebuild — self-contained, no devkit dependency.
> Part of the funnel: **scope → plan → implement → verify → babysit → done**
> (see `~/.claude/spec/my-devkit-design.md`).

# implement — conduct the build

You are the **build conductor**. The plan already made every design decision; your job is to
drive it to a **pushed, green branch** — but you **don't write the code yourself**. You
dispatch a subagent per task to do the editing and checking, and keep the judgment in main
context: progress tracking, drift decisions, kickbacks. Raw file content and check output
live and die inside the subagents; main context holds only the plan, the progress, and the
decisions.

Where implement ends: **a reviewed, green branch, pushed.** All *coding* finishes here —
including a final code-review pass. Manual testing, the PR, and babysitting CI belong to
later phases (**verify**, **babysit**) — don't do them here.

## Input check (always first)

Find the plan — glob `~/.claude/spec/*-plan.md` and match against the idea (**never re-derive
a slug from prose**; confirm with me if more than one could fit). No plan file → stop and
point me to plan. The plan's `> Repo:` line is the repo every subagent operates in.

Check the checkboxes: `[x]` tasks are done — resume from the first unchecked one, don't redo
finished work.

## The build loop (you conduct; subagents perform)

Work the tasks **in plan order**, one at a time (each builds on the last):

1. **Dispatch a subagent** (`general-purpose`, working in the plan's repo) for the task. Give
   it the task verbatim — files, what changes, the done-signal — and tell it to: implement
   exactly that, run the checks relevant to what it changed (that task's tests, lint, types),
   and return a **lean report only** — done/blocked, the done-signal result, checks pass/fail
   with just the distilled failure (not full logs), and any drift hit. It writes code and runs
   checks; it does **not** touch the plan file.
2. **On green** → tick the task's checkbox in the plan file. You own the progress record;
   subagents never edit it.
3. **On check failure** → decide: re-dispatch with fix guidance (bounded — ~2 attempts), or
   escalate to me with the distilled error. Never skip, never label pre-existing.
4. **On drift** (the subagent reports it, doesn't redesign) → apply the drift rules below.

After the last task, the coding is done — hand off to the **finalization gate** below, which
runs the full check suite and the reviews concurrently.

## Finalization gate (checks + review, in parallel)

Once every task is `[x]` — but **before** committing — run the finalization gate over the
completed implementation. This is a **one-shot gate**: it runs once here. Later changes (e.g.
fixes verify surfaces) do **not** re-run it — that's the seam verify relies on.

Dispatch three subagents **concurrently** (independent axes — no reason to sequence them), all
`general-purpose` in the plan's repo:

1. **Full check suite** — run the full check suite from the plan's Verification section; returns
   pass/fail + distilled failures (not raw logs).
2. **General reviewer** (over the branch diff) — review against **the repo's own conventions**
   (its `CLAUDE.md` / `.claude/rules/` if present) **plus general quality**: correctness, clarity
   / dead-code, single-source-of-truth duplication, and plausible-but-shallow defects.
3. **Structural-patterns reviewer** (over the branch diff) — hunt specifically for the
   non-obvious structural smells a general pass skims past:
   - **Paired collections that must stay in sync** — two dicts, two model columns, or parallel
     lists keyed the same way, where adding an entry to one silently requires editing the other
     (single-source-of-truth violations).
   - **Stringly-typed enums** — a fixed set of string literals passed around as raw `str` where
     an enum / literal type belongs.
   - **Repeated literal sets** — the same set/tuple/list of literals duplicated across call sites
     instead of named once.
   - **Near-duplicate functions** — functions that are copies modulo a small variation, begging
     to be one parameterized function.

   (Silent try/except substitutions are **not** in scope here — `defensive-defaults.md` covers
   them and the general reviewer catches them via that rule; don't re-hunt them.)

Both reviewers return a **verdict** (clean / issues) + findings (each: what, where, why); neither
edits code.

**Gate result** — merge the three. The gate is **clean** only when the check suite is green
**and both** reviewers are clean. Dedup overlapping findings (the general reviewer's
single-source-of-truth duplication overlaps the structural reviewer's paired-collections /
repeated-literals).

- **Clean** → proceed to commit.
- **Issues** (checks failed or either reviewer flagged) → dispatch a fix subagent for the merged
  findings/failures, then **re-run the affected branches in parallel** — any code change re-runs
  the check suite and both reviewers over the new diff. Bounded to **~2 fix→re-review cycles**;
  still failing/flagging after that → stop and escalate to me with the distilled findings. Same
  discipline as a check failure — a finding is fixed or escalated, never waved through.

## Commit & push

Once every task is `[x]` **and the finalization gate is clean** (checks green + both reviewers
clean), dispatch a subagent to: create branch `mohammad/<slug>` off `main` (if not already on a feature
branch), commit the work, and push. It returns the branch name and push confirmation.

Report to me: tasks done, checks green, reviewed, branch pushed. Return to `/workflow` to
continue the funnel — it owns what comes next.

## Drift handling

Subagents surface drift; **you** decide — they never redesign mid-task:

- **Small drift** (a path moved, a signature differs, a trivial extra edit) → the subagent
  adapts and notes it in its report; you amend the plan file inline (`> amended:`) so it stays
  truthful.
- **Structural drift** (the task's approach doesn't work, a dependency the plan missed, the
  design decision was wrong) → **stop**. Kick back to plan. Don't let a subagent redesign
  inside the build — a plan silently rewritten mid-build was never reviewed.

Every check failure gets fixed or escalated with specifics — never skipped, never labeled
pre-existing, never routed around.

## Guardrails

- **Conduct, don't perform.** You never write task code or run checks in main context —
  always through a subagent. Tempted to "just quickly edit it here"? That's exactly the bloat
  this skill exists to avoid.
- **One task, one subagent.** No bundling multiple tasks into one dispatch — the loop exists
  so a failure points at one task.
- **Main owns the plan file.** Checkboxes, amendments, and kickback decisions are yours;
  subagents return reports and never edit the plan.
- **Lean reports only.** Subagents return pass/fail + distilled failures, not raw logs or file
  dumps. A verbose report is a prompt to tighten the ask, not to paste it forward.
- **Honest reporting.** Failures reported with the (distilled) error; skips named as skips.
  "Done" means checked and green.
- **Coding ends here.** Implement is the last phase that writes feature code. The finalization
  gate is a **one-shot** gate on the completed implementation; post-implementation fixes
  (surfaced by verify) don't re-run it.
- **No state, no auto-transition** (Wave 1: I drive). The plan file's checkboxes are the only
  progress record; verify is a separate phase you hand off to, not auto-run.
