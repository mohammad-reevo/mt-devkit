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

1. **Dispatch an `implementer` subagent** (`subagent_type: implementer`, working in the plan's
   repo) for the task. Give it the task verbatim — files, what changes, the done-signal. The
   `implementer` agent already carries the contract (make exactly that change, run the checks
   for what it touched, return a lean report, never touch the plan file, report drift rather
   than redesign) — don't restate it inline.
2. **On green** → tick the task's checkbox in the plan file. You own the progress record;
   subagents never edit it.
3. **On check failure** → decide: re-dispatch with fix guidance (bounded — ~2 attempts), or
   escalate to me with the distilled error. Never skip, never label pre-existing.
4. **On drift** (the subagent reports it, doesn't redesign) → apply the drift rules below.

After the last task: dispatch one subagent to run the **targeted checks** for what the branch
changed — the tests covering the changed code (the specific test files/dirs named in the plan's
Verification section, **never** the whole `tests/unit` / `tests/integration` tree or `make
pytest`), plus lint and types. It returns pass/fail + distilled failures. All green before
review. GitHub PR CI runs the full suite on every push, so a whole-tree local run only
duplicates CI and pins the machine (see `local-test-scope.md`).

## Code review (finalize the coding)

Once every task is `[x]` and the targeted checks are green — but **before** committing — run one
finalization review over the whole branch diff. This is a **one-shot gate**: it runs once here,
on the completed implementation. Later changes (e.g. fixes verify surfaces) do **not** re-run
it — that's the seam verify relies on.

1. **Dispatch one review subagent** (`general-purpose`, in the plan's repo) over the branch
   diff. Tell it to review against **the repo's own conventions** (its `CLAUDE.md` /
   `.claude/rules/` if present) **plus general quality** — correctness, clarity / dead-code,
   single-source-of-truth duplication, and plausible-but-shallow defects. It returns a
   **verdict** (clean / issues) + findings (each: what, where, why), and does **not** edit code.
2. **Clean** → proceed to commit.
3. **Issues** → dispatch an `implementer` subagent to fix the findings, then re-dispatch the
   reviewer over the new diff. Bounded to **~2 fix→re-review cycles**; still flagging real issues after that →
   stop and escalate to me with the distilled findings. Same discipline as a check failure — a
   finding is fixed or escalated, never waved through.

## Commit & push

Once every task is `[x]`, the targeted checks are green, **and the finalization review is clean**,
dispatch a subagent to: create branch `mohammad/<slug>` off `main` (if not already on a feature
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
  always through the `implementer` subagent. Tempted to "just quickly edit it here"? That's
  exactly the bloat this skill exists to avoid — and `implementer_gate_hook.py` enforces it
  (product-repo edits ≥30 lines from the orchestrator are blocked). See
  [[delegate-product-code]].
- **One task, one subagent.** No bundling multiple tasks into one dispatch — the loop exists
  so a failure points at one task.
- **Main owns the plan file.** Checkboxes, amendments, and kickback decisions are yours;
  subagents return reports and never edit the plan.
- **Lean reports only.** Subagents return pass/fail + distilled failures, not raw logs or file
  dumps. A verbose report is a prompt to tighten the ask, not to paste it forward.
- **Honest reporting.** Failures reported with the (distilled) error; skips named as skips.
  "Done" means checked and green.
- **Coding ends here.** Implement is the last phase that writes feature code. The finalization
  review is a **one-shot** gate on the completed implementation; post-implementation fixes
  (surfaced by verify) don't re-run it.
- **No state, no auto-transition** (Wave 1: I drive). The plan file's checkboxes are the only
  progress record; verify is a separate phase you hand off to, not auto-run.
