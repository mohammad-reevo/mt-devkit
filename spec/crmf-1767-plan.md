# Add non-CRM field types to eval examples — Plan

> Scope: crmf-1767-scope.md
> Repo: /Users/mohammad/Desktop/code/devkit/worktrees/crmf-1767/salestech-be

## Goals
Add non-CRM **typed** examples to the Clean & Transform runtime value-production eval
(`eval_dataset.py`) so the eval exercises the non-CRM `field_type` path across the supported typed
types. Each new field is context-less (`crm_field_context=None`) with its constraint built from
`resolve_field_type_constraint(NormalizedFieldType.X)` — byte-identical to what the node receives at
runtime — and a gold value that satisfies the constraint. The dataset-integrity test is updated to
cover the new rows. Done = new rows land, `test_eval_metric.py` passes (golds validate + coverage
invariant holds), and code checks are green.

## Non-goals
- The node-agent / config-generation eval (`node_agents/clean_and_transform_data.py`,
  `node_config_metric`) — different eval, explicitly out.
- The field_type unification / `CrmFieldBinding.field_type` deprecation — CRMF-1768.
- Select-family types (single/multi-select, enum, stage, pipeline) on non-CRM outputs.
- Retrofitting/re-typing existing free-text rows — none needed (TEXT is already the empty
  free-text constraint at runtime; `domain_name` confirmed TEXT).
- Any metric/scoring change or runtime/executor code.

## Decisions
- **Which eval:** the runtime value eval `core/flow/nodes/integration/clean_and_transform_data/eval_dataset.py`,
  graded by `clean_and_transform_eval_metric` (`judge.py:212`). Not the node-agent eval.
- **Supported types (10):** TEXT, NUMERIC, CURRENCY, PERCENT, BOOLEAN_CHECKBOX, TIMESTAMP,
  LOCAL_DATE, EMAIL, URL, PHONE_NUMBER. TEXT is already covered by the existing 13 context-less
  free-text rows → **9 new typed types** to add.
- **Constraint construction:** build each new field's constraint via
  `resolve_field_type_constraint(NormalizedFieldType.X)` (runtime-faithful; auto-supplies the
  correct `value_format`; yields the `true/false` allowed-values set for BOOLEAN_CHECKBOX), not
  direct `FieldValueConstraint(...)`. Both live in `crm_field_constraint_resolver.py`, already
  imported by `eval_dataset.py`.
- **No metric change:** the metric already validates every produced value against its constraint
  (hard-fail on violation) and ignores `crm_field_context`, so non-CRM typed rows grade correctly.
- **No retrofit:** existing free-text rows stay as-is (add-only).
- **Dependency #28591:** merged to main; branch already updated (`resolve_field_type_constraint`
  present at `crm_field_constraint_resolver.py:304`).

## Tasks
- [x] 1. Add non-CRM typed examples to the gold dataset — files:
      `salestech_be/core/flow/nodes/integration/clean_and_transform_data/eval_dataset.py`.
      Add ~4–6 new `CleanAndTransformExample` entries to `_EXAMPLES`, **multi-field for economy**,
      collectively covering all 9 new typed types. Each `RequestedField`: realistic `name` +
      `instruction`, `crm_field_context=None`, `constraint=resolve_field_type_constraint(NormalizedFieldType.<T>)`,
      and a gold `ProducedValue` whose value **parses** against that constraint. Add the imports for
      `resolve_field_type_constraint` and `NormalizedFieldType`. Suggested spread (implement may
      refine wording/values):
        - NUMERIC (e.g. employee count "~500 people" → "500") + CURRENCY (e.g. "$1.2M ARR" →
          "1200000") + URL (company website → "https://acme.io")
        - EMAIL (normalize " Jane.DOE@Acme.IO " → "jane.doe@acme.io") + PHONE_NUMBER
          ("(415) 555-1234" → "+14155551234")
        - TIMESTAMP (demo datetime → ISO 8601) + LOCAL_DATE (contract start → "2026-03-14")
        - BOOLEAN_CHECKBOX (is-SQL-qualified → "true") + PERCENT (win probability "15% off" → "15")
      Note TIMESTAMP and BOOLEAN_CHECKBOX have **no prior row** in the dataset — verify their exact
      gold format against `validate_produced_value` (TIMESTAMP parses via
      `custom_field_value_from_generic_value(FieldType.TIMESTAMP, ...)`; BOOLEAN gold must be exactly
      `"true"`/`"false"`).
      Done when: rows added, file imports resolve, and Task 2's integrity test passes (every new
      gold value validates against its constraint).
- [x] 2. Update the dataset-integrity test — files:
      `tests/unit/core/flow/nodes/integration/clean_and_transform_data/test_eval_metric.py`.
      In `TestGoldDatasetIntegrity`: bump `assert len(_EXAMPLES) == 39` to the new count. Add one
      invariant test asserting non-CRM typed coverage now exists — for each of the 9 new typed types,
      at least one `_EXAMPLES` field has `crm_field_context is None` **and** a typed constraint for
      that type (parseable: `constraint.field_type == FieldType.<T>`; boolean:
      `constraint.allowed_values == ("true","false")`) — so the coverage can't silently regress.
      The existing parametrized `test_every_gold_value_satisfies_its_constraint` already covers the
      new rows automatically. Done when: `test_eval_metric.py` passes.

Ordered: Task 2's count/invariant depend on Task 1's rows.

## Verification
- **Coding checks (gate):**
  - `cd salestech-be && uv run pytest tests/unit/core/flow/nodes/integration/clean_and_transform_data/test_eval_metric.py -q`
    (integrity: count + every gold validates + non-CRM coverage invariant; plus the metric-behavior tests).
  - `cd salestech-be && uv run deploy/ci/run-code-checks.sh` (ruff + mypy).
- **Manual checks:** none required to land. Optionally, a full LLM scoring pass over the new rows via
  `uv run python scripts/optimize_clean_and_transform_node.py` (GEPA; needs `ANTHROPIC_API_KEY` +
  `WANDB_API_KEY`) is a later measurement of node quality on the new cases, not a landing gate.
