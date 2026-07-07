# Always work in a git worktree (never the primary checkout)

Before making **code changes** or doing a **branch review** in any git repo,
work inside a dedicated **git worktree** — never the repo's primary checkout.
The primary checkout (the clone that sits on `main`) stays pristine so multiple
tasks can be in flight at once and every new task branches from fresh
`origin/main`.

## Code changes — hard-enforced

A global PreToolUse hook (`~/.claude/hooks/worktree_gate_hook.py`) **blocks**
`Edit`/`Write` whose target resolves into a repo's primary checkout (`.git` is a
*directory*). A linked worktree (`.git` is a *file*) passes. This is a guarantee,
not a reminder — you cannot edit the primary tree.

When blocked: call **`EnterWorktree`** (or `git worktree add <path> origin/main`)
and make the change inside the worktree, then retry. A hook can't relocate the
session — the first blocked edit is the signal to enter a worktree.

- **Escape hatch:** `CLAUDE_WORKTREE_GATE=0` disables the gate for a session —
  use only when you deliberately mean to touch a primary checkout.
- **Always-allowed:** non-git paths (worktrees need git) and everything under
  `~/.claude/` (config must stay editable).

## Reviews — by convention

The Edit/Write gate can't see a review (reviews don't mutate files). So for
reviewing a PR/branch, **don't `git checkout` the branch in the primary
checkout** — that dirties `main`. Add a worktree for the branch
(`git worktree add ../review-<branch> <branch>`), review there, and remove it
when done.

## Why

One pristine `main` per repo + a worktree per task = parallel work that never
collides and always starts from current `origin/main`. See
[[feedback_push_gate_stamp_nested_worktree.md]] for the `.git` file-vs-directory
detection the gate relies on. This is personal global tooling, deliberately
independent of devkit ([[project-moving-off-devkit]]); it overrides devkit's
in-place editing where they conflict.

This applies across all repositories and projects.
