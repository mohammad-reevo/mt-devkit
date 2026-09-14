# `spec/` design + migration docs are a historical record — never swept

## When to Apply
When a harness change **removes or renames** something and you sweep the repo for references to
it — or any moment you're about to edit `spec/my-devkit-design.md`, `spec/devkit-parity.md`,
`spec/mt-devkit-migration.md`, or `spec/knowledge-base-design.md` to "match" the current state.

## The Rule

**The reference sweep stops at `spec/` design and migration docs.** A line in one of them that
names something now gone is a **record of what was designed and built, and when** — not a stale
reference to fix. Leave it byte-for-byte.

`spec/` holds two different kinds of file, and the distinction is the whole rule:

| Kind | Files | Treatment |
|---|---|---|
| **Historical** | `my-devkit-design.md`, `devkit-parity.md`, `mt-devkit-migration.md`, `knowledge-base-design.md` | Never swept, never "updated to match". A stale-looking line is the point. |
| **Live working state** | per-idea `<name>-scope.md` / `<name>-plan.md` | Written by `scope`, descended by `plan`, updated during `implement`, deleted by `/done`. Edit freely — that's the funnel. |

This is **not** a blanket "never touch `spec/`". The funnel's own writes are the exception named
above, and they are normal.

## When a design doc is genuinely wrong

Distinct from merely historical: a doc that **misstates what was actually built** (wrong
mechanism, a claim that was never true) is a defect, not a record. Don't fix it silently — say so
in conversation and let Mohammad decide. Editing a decision record without being asked is the
failure this rule exists to prevent, and it doesn't stop being one because the edit is correct.

## Why

The damage is silent and plausible. A design doc rewritten to match today's state still reads
perfectly — nothing signals that a build log was overwritten to pretend the old state never
existed. And the sweep recurs on **every** rename or removal, which is most harness changes, so
without a rule each session re-decides it and the default instinct ("keep the docs current") is
the wrong one here.

**Worked instance.** Removing the `populate-dev-data` skill (PR #122) surfaced six references —
`spec/devkit-parity.md:28`, `spec/my-devkit-design.md:15,159,193,218`,
`spec/mt-devkit-migration.md:25`. Every one historical; all six were correctly left alone and
still stand on `main` with the skill gone. Nothing was broken by not fixing them.

This applies across all sessions working in this workspace.
