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

## In the mt-devkit workspace — create worktrees via the `worktree` skill

Inside this workspace, create worktrees with the **`worktree` skill**
(`/worktree` → create), **not** the built-in `EnterWorktree`. The skill sets up
what the funnel needs and `EnterWorktree` does not: the parent **plus the product
sub-repos** (`salestech-be`, `frontend-monorepo`, `reevo-realtime`) each on `mohammad/<name>`,
env/settings copied, and the frontend→backend path fixed for the worktree.
`EnterWorktree` makes a bare parent-only worktree, so a session that used it for
product work would be missing the sub-repo worktrees the funnel relies on.

This holds **even for harness-only edits** (changing `mt-devkit/.claude/`
itself): the skill sets the sub-repos up unused, which is accepted overhead for a
single consistent way in. Tear a worktree down the same way — the `worktree`
skill (`remove <name>`) or `/done`, **not** `ExitWorktree` (which only knows how
to remove a bare `EnterWorktree` worktree, not the skill's parent+sub-repo set).

The generic `EnterWorktree` / `git worktree add` mechanism above still applies in
**other** repos that have no `worktree` skill.

## One worktree per session — reuse it across branches and PRs

The unit of isolation is the **Claude Code session**, not the branch or the task:
each session gets **one** worktree and stays in it. When you finish a task and
start another — or land a PR and open the next — **don't create a second
worktree**. Cut the new branch off fresh `origin/main` **in place**, in whichever
repo the change touches:

```
git fetch origin
git -C <worktree> switch -c mohammad/<name> origin/main                 # parent / harness change
git -C <worktree>/salestech-be switch -c mohammad/<name> origin/main    # a sub-repo PR
```

This holds **broadly, including sub-repo PRs** — reuse the session's existing
sub-repo worktrees, switching the relevant one to a new branch. Create a fresh
worktree (via the `worktree` skill) only for a genuinely separate, **parallel**
session that needs its own isolated tree.

## Reviews — by convention

The Edit/Write gate can't see a review (reviews don't mutate files). So for
reviewing a PR/branch, **don't `git checkout` the branch in the primary
checkout** — that dirties `main`.

**In this workspace**, create the review tree with the `worktree` skill's
`create-review <name> <subrepo> <ref>` mode and tear it down with `/done` —
the same way in and the same way out as every other worktree. It builds the
parent plus only the repo under review, detached at that ref, skipping env and
`uv sync` (a review runs nothing), so it costs ~390M rather than the ~4-6G of a
feature worktree. **The reviewer never removes it**; leaving teardown to `/done`
is what keeps it reachable for posting and re-review, and what stops review
checkouts accumulating unowned.

Two things that must not drift: the tree is **detached**, never on a local
branch — a branch tracking the author's ref makes `/done` gate *their* PR, so my
cleanup would wait on their CI and their threads — and the session enters the
**parent**, never the sub-repo, which loads its own Bash-blocking hook.

In **other** repos with no `worktree` skill, use a plain
`git worktree add ../review-<branch> <branch>` and remove it when done.

## Why

One pristine `main` per repo + a worktree per session = parallel work that never
collides and always starts from current `origin/main`. See
[[feedback_push_gate_stamp_nested_worktree.md]] for the `.git` file-vs-directory
detection the gate relies on. This is personal global tooling, deliberately
independent of devkit ([[project-moving-off-devkit]]); it overrides devkit's
in-place editing where they conflict.

This applies across all repositories and projects.
