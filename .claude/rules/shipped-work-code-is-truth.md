# Shipped work: the code is source of truth over the ticket or design doc

## When to Apply
When a ticket, eng design, or PRD describes work that has **already shipped** (PR merged, status
Done) and you are about to build on it, plan against it, or write about it. Sharpest in `scope`
and `plan`, but it holds for `create-implementation-plan`, `create-eng-doc`,
`create-testing-party-doc`, and any turn that reads a ticket.

Three concrete triggers:

- the ticket is `blockedBy` / depends on another ticket whose status is Done or Merged;
- its technical notes name a symbol, field, module path, or `file:line` your change will touch;
- an eng design is cited as the spec for work already partly built.

## The Rule

**A ticket or design describing merged work is a historical proposal, not a record.** Names and
scope routinely change during implementation and review, and nobody goes back to update the doc.
So verify before building on it — two checks, both cheap enough to be mandatory rather than
advisory:

1. **Symbols.** Grep every named symbol, field, and module path before using it. If it isn't
   there, find what actually merged (the linked PR, `git log`) and use that.
2. **Scope.** Confirm the *capability* the doc says shipped actually exists. This is the half no
   compiler catches, and the expensive one — a scoped-in capability that was quietly deferred
   reshapes the plan, not just a line of code.

**Then say the drift out loud.** Name what the doc said, what actually merged, and which kind it
is — a rename, or a dropped scope item. Silently substituting the correct name is the failure
mode: it fixes your line of code and leaves everyone else reading a doc that is still wrong.

## Worked example — three drifts in one ticket

CRMF-2034 → CRMF-2039. Both the Linear ticket and the eng design (§4 / §6) specified
`computed_fields: dict[str, ComputedFieldDef]` on `BaseNodeConfig` **and**
`BaseEventConfiguration`, with `ComputedFieldDef` in `core/flow/nodes/computed_field.py`.

What merged (salestech-be PR #30903) was `compute_formulas: dict[str, ComputeFormulaDef]` on
`BaseNodeConfig` **only**, with the model in `salestech_be/core/flow/nodes/field_types.py`.

Three independent drifts in one ticket: the field name, the model name + module, and a
**silently dropped scope item** — `BaseEventConfiguration` never got the field (deferred to
CRMF-2097, and still absent a month later). Grepping `computed_fields` returns nothing. Code
built from the ticket text alone would not compile; a *plan* built from it would assume a
trigger-side capability that does not exist.

## Why

The failure is silent and confident. A ticket reads as authoritative and precise — it often
cites `file:line` — so nothing prompts a check. The cost lands late: at build time as a compile
error (cheap), or at design time as a scoped-in capability that was never built (expensive,
because it reshapes the plan). The check costs one grep.

## Record it once

Drift found this way is exactly what a `projects/` knowledge-base entry is for — the
concept-to-code name mapping, and what a ticket's scope *actually* covers. Note it as a KB
candidate; the write itself happens at `/done` or on an explicit ask, per the `kb` skill. This
rule catches the drift the first time; the KB stops the next session paying for it again.

## Not the same as `no-invented-requirements.md`

That rule says don't *add* behavior nobody asked for. This one says don't *trust* a stale spec.
Adjacent, distinct.

This applies across all repositories and projects.
