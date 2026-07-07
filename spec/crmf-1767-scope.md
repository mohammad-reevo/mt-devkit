# Add non-CRM field types to eval examples — Scope

> Name: crmf-1767   (the slug — names the scope/plan files, the worktree, and branch mohammad/crmf-1767)

## Idea
The Clean & Transform node's **runtime value-production eval** (`eval_dataset.py`, graded by
`clean_and_transform_eval_metric`) exercises the node's actual LLM call — given per-field
constraints, does the node produce values that satisfy them. Today every *typed* field in that
gold dataset is CRM-bound (carries a real `crm_field_context`); the only context-less (non-CRM)
fields are free-text. So the eval has **zero coverage of a non-CRM typed field** — an output typed
purely by `field_type` (via `resolve_field_type_constraint`) with no CRM context. Kai's PR #28591
(CRMF-1763, now merged to main) made the node *produce* such fields; this ticket makes the eval
*exercise* them.

Scope is the eval dataset only — add non-CRM typed examples so the value eval covers the supported
non-CRM types. Not the node **agent** / config-generation eval, not the field_type unification
(CRMF-1768).

## Approaches considered

### A — Add non-CRM typed rows to the value eval dataset (chosen)
Add `CleanAndTransformExample` rows to `_EXAMPLES` whose `RequestedField`s are non-CRM typed
(`crm_field_context=None`, constraint from `resolve_field_type_constraint(NormalizedFieldType.X)`),
covering the supported typed types, with gold values that satisfy each constraint. The existing
metric already validates produced values against constraints and hard-fails violations, so no
metric change is needed — the path just needs to be exercised.

### B — Also add a scoring/metric change (rejected)
Considered extending the grading, but the value eval's metric already validates every produced
value against its field's constraint (hard-fail on violation) independent of `crm_field_context`.
Non-CRM typed rows are graded correctly as-is. A metric change would be redundant.

### C — (earlier mis-aim) Node-agent config-generation eval (rejected — wrong target)
An earlier reading aimed this at the node **agent** (`node_agents/clean_and_transform_data.py`,
`node_config_metric`) — teaching the agent to emit `field_type` in generated configs. That is a
different eval (config generation, not value production) and not what this ticket is about. Dropped.

## Chosen direction
Approach **A**. Add non-CRM typed examples to the value-eval gold dataset
(`core/flow/nodes/integration/clean_and_transform_data/eval_dataset.py`), covering the supported
typed types, each field context-less (`crm_field_context=None`) with its constraint built from
`resolve_field_type_constraint(...)` so the eval constraint is byte-identical to what the node
receives at runtime for a non-CRM `field_type` output. Existing free-text rows already faithfully
represent non-CRM TEXT (the resolver maps TEXT → the empty free-text constraint), so they are left
as-is — this is add-only. Update the dataset-integrity test's count and add a coverage invariant.
No metric change, no node-agent change, no binding/unification change.

## Testing
The dataset-integrity test (`test_eval_metric.py::TestGoldDatasetIntegrity`) is the gate: its
parametrized check already asserts every gold value satisfies its constraint, so it auto-validates
the new typed rows; its example-count constant must be bumped, and a small invariant added asserting
non-CRM typed coverage now exists. Actually scoring the LLM against the new rows runs through the
GEPA optimizer (expensive, API keys) — a later measurement, not a landing gate.

## Open questions
_All resolved during planning:_
1. Supported types — **10**: TEXT, NUMERIC, CURRENCY, PERCENT, BOOLEAN_CHECKBOX, TIMESTAMP,
   LOCAL_DATE, EMAIL, URL, PHONE_NUMBER (user-confirmed). TEXT already covered by existing free-text
   rows → **9 new typed types** to add.
2. Dependency on #28591 — **resolved**: merged to main; branch updated; `resolve_field_type_constraint`
   present.
3. Which eval — **resolved**: the value eval (`eval_dataset.py`), not the node-agent eval.
4. Retrofit existing free-text rows with `field_type` — **resolved: no.** Runtime maps non-CRM
   TEXT/free-form to the empty free-text constraint, so the existing rows are already faithful;
   typing them would diverge from runtime. Audited the 13 context-less rows — all genuinely TEXT
   (incl. `domain_name`, confirmed TEXT per `account/types_v2.py:189`).

## Out of scope
- The **node-agent / config-generation eval** and `node_config_metric` — different eval, not this ticket.
- The field_type **unification** (dropping `CrmFieldBinding.field_type`, moving type-stamping onto
  the field for CRM picks) — that's CRMF-1768.
- **Select-family types** (single/multi-select, enum, stage, pipeline) on non-CRM outputs — no
  allowed-values source from a bare type; excluded from the supported set.
- Retrofitting/re-typing existing free-text rows (resolved: none needed).
- Any metric/scoring change and any runtime/executor code.
