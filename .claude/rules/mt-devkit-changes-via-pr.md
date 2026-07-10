# mt-devkit harness changes go through a PR — never in-place, never left uncommitted

## When to Apply
Any time you edit the mt-devkit harness itself — anything tracked under
`mt-devkit/.claude/` (skills, rules, hooks, agents, settings templates) or other
tracked files of the `mt-devkit` repo. This is about the **harness repo**, not the
product sub-repos (`salestech-be`, `frontend-monorepo`), which have their own flow.

## Rule
A change to the mt-devkit harness lands through the normal git flow: a dedicated
worktree/branch → commit → **pushed PR** (ready for review, per `github.md`). Two things
are forbidden:

1. **Never edit the harness in the primary `mt-devkit` checkout in place.** The primary
   stays pristine; the worktree gate blocks it anyway.
2. **Never leave a harness edit sitting uncommitted in a feature worktree.** A feature
   worktree (`worktrees/<name>/`) is for the product idea it was created for. An
   uncommitted `.claude/` edit there is invisible to every other session and is
   **destroyed** when `/done` tears the worktree down.

Make the harness change on its own branch (a `.claude/worktrees/<name>` worktree is the
convention), commit it, open a PR, and let it be reviewed/merged like any other change.
A harness improvement is still a change to shared tooling — it earns the same PR
discipline as product code.

## Why
An uncommitted harness edit in a feature worktree helps only the current session and
dies on teardown; nothing durable, nothing shared, nothing reviewed. Routing every
harness change through a PR makes it durable, reviewable, and available to all future
sessions — and keeps feature worktrees clean so `/done` can tear them down without
losing work.

This applies across all sessions working in this workspace.
