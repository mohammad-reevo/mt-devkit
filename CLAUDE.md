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
- **babysit** — watch CI + PR review threads; unresolved threads hand off to `address-comments`.
- **done** — gate the PR (CI green + threads resolved), then tear down the worktree.

Standalone tools: `pr-review` (review a diff or a teammate’s PR), `pr-explanation` (orient me to
a PR/branch/diff — files in reading order, no findings), `address-comments` (triage the
review comments on my PR, then act on the agreed ones), `pr-description` (write a PR body —
routes to the target repo’s convention and preflights it), `make-diagram` (ASCII diagram
of a design or flow), `kb` (the cross-session knowledge base), `worktree`, `db` (local/dev
Postgres), `snowflake` (reporting warehouse),
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

- `.claude/` — the harness: `skills/`, `rules/`, `hooks/`, `references/`, `agents/`.
- `spec/` — design docs + per-idea scope/plan files.
- `tasks/` — deferred tooling chores (the `claude-task` system).
- `knowledge-base/` — context that outlives a session (gitignored; see below).
- Product sub-repos (`salestech-be`, `frontend-monorepo`, …) are gitignored siblings.

### Where a piece of prose goes

- **Skill** — a produced artifact and the procedure for it; something I'd ask for by name. It's
  advertised in the session's skill listing, so a bare ask fires it at a fraction of the context
  an always-loaded rule costs.
- **Rule** — a norm or constraint on how work is done, not a thing you ask for.
- **`references/`** — prose **no single skill can own**: shared metadata that several skills each
  apply in their own context. `testing-call.md` is the model — `scope`, `implement`,
  `implementer`, `reviewer`, and `address-comments` all read it, and there is no "testing-call
  skill" it could belong to. `agents/` is the same idea, for shared behavior.
- **One owner ⇒ it lives in that skill.** A second reader is a citation — name the skill and its
  section — not a reason to extract a file. Two consumers is not the bar; ownerless is.

## Knowledge base

`knowledge-base/` carries what would otherwise be re-derived or re-explained every session:
`projects/` for where a project stands and what its tickets actually cover, `concepts/` for
durable things worth not explaining twice. Design: `spec/knowledge-base-design.md`.

**Its index is imported below, so every session sees it.** Treat a line that matches what
you're working on as a signal to open that entry — you won't otherwise know it exists. If you
find yourself investigating something an entry already covers, the index line was written badly;
report the line as a bug — that is a fix to the line, not a cue to file anything new.

Reading an entry is free. **Writing goes through the `kb` skill**, which says what it's about to
write and waits, then shows a diff and waits again — never hand-edit the store. **Writes happen
at `/done` or when I explicitly ask, and nowhere else** — don't offer to file things mid-session,
however KB-worthy they feel at the time, and don't read "I might save this" as an instruction.

@knowledge-base/INDEX.md

## Status — migration in progress

Graduating out of `devkit`. Plan: `spec/mt-devkit-migration.md`. Design: `spec/my-devkit-design.md`.
Devkit parity ledger: `spec/devkit-parity.md`. Skills use bare names (the `mt-` prefix was dropped
in migration Phase 2).
