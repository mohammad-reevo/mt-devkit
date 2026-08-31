# mt-devkit — workspace instructions

This is my personal developer-workflow harness (see `README.md`). You are the **orchestrator** of
a manually-invoked funnel that takes a development idea to a merged PR. Keep the main conversation
lean — delegate wide reads and substantial coding to subagents; think in the main thread.

## The funnel

Each phase is a skill I invoke; nothing auto-runs the chain:

```
scope → plan → implement → verify → babysit → done   (conducted by workflow)
```

- **scope** — brainstorm a raw idea / Linear ticket into a converged direction (no task breakdown).
- **plan** — descend to a concrete, file-level task breakdown; set up the feature worktree.
  Stops for my explicit go-ahead before implement.
- **implement** — conduct the build via one subagent per task, finalize with the `reviewer`
  trio, then commit + push a reviewed green branch.
- **verify** — prove it works (user-directed), then open the PR.
- **babysit** — watch CI + PR review threads (opt-in; never auto-starts).
- **done** — gate the PR (CI green + threads resolved), then tear down the worktree.

Standalone tools: `pr-review` (review a diff or a teammate’s PR), `make-diagram` (ASCII diagram
of a design or flow), `worktree`, `db` (local/dev Postgres), `snowflake` (reporting warehouse),
`langfuse-traces` (analyze LLM traces — latency, throughput, tokens), `populate-dev-data`,
`env-manager`, `spinup-local-db`, `falkor-cleanup` (reap the local FalkorDB org graphs test runs
leave behind).

## Principles

- **Files are the contract.** Phase state lives in `spec/<name>-scope.md` / `<name>-plan.md` —
  no hidden session state. Skills read the previous file and write their own.
- **I drive, skills assist.** Do the obvious next step in a workflow rather than asking; but never
  merge, request reviews, or message people — that's mine.
- **Self-contained — no devkit.** Every capability lives in this repo. Never invoke or depend on a
  `devkit`-provided skill/hook/rule; Claude Code built-ins are fine.
- **Work in worktrees.** Code changes go in a git worktree, never the primary checkout.

## Layout

- `.claude/` — the harness: `skills/`, `rules/`, `hooks/`.
- `spec/` — design docs + per-idea scope/plan files.
- `tasks/` — deferred tooling chores (the `claude-task` system).
- Product sub-repos (`salestech-be`, `frontend-monorepo`, …) are gitignored siblings.

## Status — migration in progress

Graduating out of `devkit`. Plan: `spec/mt-devkit-migration.md`. Design: `spec/my-devkit-design.md`.
Devkit parity ledger: `spec/devkit-parity.md`. Skills use bare names (the `mt-` prefix was dropped
in migration Phase 2).
