# `spec/` design + migration docs are a historical record — never swept

## When to Apply
When a harness change removes or renames something and you sweep the repo for references to it.

## The Rule

The sweep stops at `spec/`'s design and migration docs — `my-devkit-design.md`,
`devkit-parity.md`, `mt-devkit-migration.md`, `knowledge-base-design.md`. A line naming something
now gone records what was built and when. Leave it.

Not a blanket "never touch `spec/`": the per-idea `<name>-scope.md` / `<name>-plan.md` files are
live working state, written and deleted by the funnel. Edit those freely.

A doc that *misstates what was built* is a defect, not a record — say so rather than editing a
decision record unasked.

## Why

A design doc rewritten to match today's state still reads perfectly, so nothing signals that the
record was overwritten. Removing `populate-dev-data` (#122) surfaced six such references; all six
were correctly left alone, and nothing broke.

This applies across all sessions working in this workspace.
