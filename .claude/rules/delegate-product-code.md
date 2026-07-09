# Delegate product-repo code changes to the implementer subagent

## When to Apply
When any **product-repo code** needs editing — a file under `salestech-be`,
`frontend-monorepo`, `reevo-realtime`, or `harvey-the-slack-bot` — whether inside
the funnel (an `implement` task), a plan-less follow-up, or a revision after a
plan already shipped.

## The Rule
The orchestrator does **not** hand-edit product-repo code. Dispatch an
**`implementer`** subagent (`subagent_type: implementer`) to make the change, run
the checks for what it touched, and report lean. Raw code and check output stay
inside the subagent — that is the whole point.

- **Why:** context economy. Editing product code in the main thread pulls file
  contents, diffs, and check logs into the orchestrator's context, which is the
  bloat the whole subagent-delegation discipline exists to avoid. One `implementer`
  contract, used everywhere, keeps the funnel and the one-off follow-up consistent.
- **How:** `subagent_type: implementer` — "`<the change>`. Files: `<paths>`." The
  agent reads the source itself; don't write it a detailed inline spec.

## Trivial edits may be inline
A small fix — under **30 new lines** — you may make directly; it doesn't move the
context needle. At or above 30 new lines to product code, delegate.

## Enforced, not just advised
`implementer_gate_hook.py` (PreToolUse on Edit/Write) blocks an orchestrator edit
of ≥30 new lines to a product sub-repo and points you to the `implementer`. Harness
/ `spec/` / plan / task files are unaffected — those the orchestrator edits directly.

This applies across all repositories and projects.
