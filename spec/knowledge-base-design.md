# Knowledge Base — Design

> A local, gitignored `knowledge-base/` in this repo that carries context across sessions.
> Status: designed, not built. Four PRs below, each independently shippable.
> Drains `~/.claude/tasks/cross-session-knowledge-base.md`.

## The problem

Two distinct pains, one store.

1. **Project context dies at the session boundary.** On a long-running project (the forcing
   case: inline computed fields) every new session needs to be re-told what the project is,
   where it stands, and what a given ticket actually covers. The work is redundant and it is
   constant.
2. **Concepts get re-explained.** Flow definition structures, how to query a thing, why the
   system errors exist — knowledge that is settled, that Mohammad already holds, and that gets
   typed out again every session.

Prior attempts and why they don't cover it:

- `~/.claude/projects/.../memory/` — right shape (one file per entry, index loaded every
  session), wrong scale. It is deliberately small and curated; growing it into a KB would bloat
  the always-loaded `MEMORY.md`. **The KB is a separate store for this reason.**
- `spec/inline-computed-fields/CONTEXT.md` — **53 KB, loaded by nothing.** This is the failure
  mode the design exists to avoid: a big honest document that no session ever reads. The KB's
  project doc is its short, loaded successor.

## Decisions

These were argued out. Recorded with reasoning so they aren't re-litigated.

**Store what the code can't tell you — but Mohammad decides what's safe.** The general guard is
staleness: don't build a second source of truth that has to be edited every time code moves. The
counter-argument, and the ruling: some structures genuinely never change (`flow_run`,
`flow_definition`, `user_flow`), and documenting them is safe. **Judgment on what's stable is
Mohammad's, not a rule enforced by the skill.**

**Project progress IS stored, even though it's technically derivable.** Deriving it means
reviewing every ticket and every PR, Linear is not organized for intuiting where a project
stands, and it never captures the changes made *while* implementing a ticket. A ten-line
hand-written doc beats a five-minute derivation. Store it.

**Not in `memory/`.** See above — bloating the always-loaded index is the one thing that would
make this worse than nothing.

**Gitignored, inside this repo.** In-repo because it revolves around mt-devkit's skills.
Gitignored so a KB edit never needs a PR. Accepted consequences: **no git history and no
backup** — a machine loss takes the KB with it.

**Out of scope: operational runbooks.** An earlier framing proposed a third category
(rarely-needed procedures, surfaced from symptoms via a hook). That is a different problem with
a different mechanism, and its forcing case has since been solved by the `falkor-cleanup` skill.
Not part of this design.

## Design

```
knowledge-base/              (gitignored)
├── INDEX.md                 ← imported by CLAUDE.md, so it's in every session
├── projects/
│   └── <project>.md         ← short; scope, decisions, where it stands
└── concepts/
    └── <area>/<topic>.md    ← durable; the things worth not re-explaining
```

**`projects/` and `concepts/` split because their lifecycles differ.** A project doc churns
weekly and is throwaway once the project ships. A concept entry barely changes and is maintained
indefinitely. Mixed together, neither one's freshness can be trusted; split, staleness is
legible at a glance.

**When a project ends, graduate its durable residue into `concepts/` before deleting the project
doc.** Otherwise closing a project deletes exactly the knowledge that was worth keeping. This
should be an explicit prompt, not a hope.

**One page per entry, hard cap.** Past a page, split it. This is what stops the KB drifting into
codebase documentation — the `CONTEXT.md` failure above started as a good document.

### Retrieval — recognition, not search

The core insight: **Claude cannot search for something it doesn't know exists, but it will open
an entry whose title it is already looking at.** So the always-loaded index does the work, and
search is only the fallback. This is exactly how `MEMORY.md` already behaves.

- **`INDEX.md` is loaded via an `@knowledge-base/INDEX.md` import in `CLAUDE.md`** — nothing
  auto-loads a file for being named `INDEX.md`; the import is the mechanism. One line, no code.
  *Verify at build time that the import resolves a gitignored path.* Fallback if it doesn't: a
  `SessionStart` hook that injects the file.
- **Index lines are triggers, not summaries.** A line must name what will be *on screen* when
  the entry becomes relevant — table names, error strings, the terms actually in play.
  - ❌ `flow-definition-structure — how a FlowDefinition is shaped`
  - ✅ `flow_definition / user_flow / flow_run — which table holds what, and why node configs
    look duplicated`
- **Grep over entry bodies is the backstop** (via the `kb` skill) for when no index line fired.
  The index handles recognition; search catches the miss.
- **The feedback loop:** re-explaining something that *is* in the KB means the index line is
  wrong, not that the entry is missing. Fix the line.

### Writes are gated

A PreToolUse hook denies `Edit`/`Write` under `knowledge-base/**`, making the `kb` skill the only
path in — and the skill shows a diff and waits for approval before applying. Silent modification
becomes structurally impossible rather than discouraged.

This is the same mechanism as the deferred `doc-diff-before-apply-rule` task. **Build it general
enough to drain that task too** rather than solving diff-before-apply twice.

## The four PRs

Ordered by what unblocks what.

**PR 1 — store and retrieval.** `knowledge-base/` + the `.gitignore` line, `INDEX.md`, and the
`CLAUDE.md` import. Ships useful alone: the index is in context every session and entries can be
hand-written. This is the PR that solves the re-explaining problem.

**PR 2 — the `kb` skill.** `search` / `add` / `update`, plus the index-line discipline (when
adding an entry it must ask "what am I looking at when this becomes relevant?") and the
one-page cap.

**PR 3 — the write gate.** The PreToolUse hook + diff-and-approve flow. **Must land after PR 2** —
gating before the sanctioned write path exists blocks the only way to add anything.

**PR 4 — consumers.** `/done` updates the project doc on close-out; `scope` and `pr-review`
consult the index before dispatching wide reads (that's where redundant re-investigation
actually burns).

On write triggers: `/done` fires per-worktree, not per-project, so it *updates* a project doc
rather than ending it. `concepts/` stays on explicit invoke to start — auto-writing concepts is
where knowledge bases fill with junk.

## Open items

- **Verify the `@` import resolves a gitignored path** (PR 1). Fallback is a `SessionStart` hook.
- **Backup.** Gitignored means a machine loss loses the KB. If that matters later, the fix is
  small: its own private repo inside the ignored directory.
- **Seeding is local, non-PR work.** The KB content is gitignored, so these four PRs ship only
  machinery — no entry ever appears in a diff. First entries to write by hand: the
  inline-computed-fields project doc, and the flow concepts (`flow_definition` / `user_flow` /
  `flow_run` structure, system errors, common queries).
