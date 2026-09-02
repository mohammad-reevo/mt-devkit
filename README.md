# mt-devkit

My personal developer-workflow harness — a private, self-contained system for taking a
development idea from raw thought to a merged PR. Built to replace the shared `devkit` framework
with tooling I own end-to-end.

`mt-devkit` is a **parent workspace**: this repo holds the harness (`.claude/`), and the product
sub-repos (`salestech-be`, `frontend-monorepo`, …) are cloned in as gitignored siblings.

## The funnel

An idea flows through a chain of manually-invoked skills, conducted by `workflow`:

```
scope → plan → implement → verify → babysit → done
```

- **scope** — brainstorm a raw idea (or Linear ticket) into a converged direction.
- **plan** — descend to a concrete, file-level task breakdown (sets up the worktree), then stops
  for an explicit go-ahead.
- **implement** — conduct the build via per-task subagents, review, and push a green branch.
- **verify** — prove it works, then open the PR.
- **babysit** — watch CI + PR review threads (opt-in).
- **done** — close out and tear down the worktree.

Plus standalone tools: `worktree`, `db`, `make-diagram`, `kb`, `populate-dev-data`, `env-manager`, and
others.

## Principles

- **Files are the contract.** Each phase reads the previous phase's file and writes its own —
  plain markdown under `spec/`. No hidden session state.
- **I drive, skills assist.** Nothing auto-runs the pipeline; each phase is invoked deliberately.
- **Self-contained.** No dependency on the old `devkit` — every capability lives here.

## Status

Graduating out of `devkit`. See `spec/mt-devkit-migration.md` for the migration plan and
`spec/my-devkit-design.md` for the full design. Skills use bare names (the `mt-` prefix was
dropped in Phase 2 of the migration).
