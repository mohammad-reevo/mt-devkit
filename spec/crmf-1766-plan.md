# Update node agent for non-CRM field types — Plan

> Scope: crmf-1766-scope.md
> Repo: salestech-be (worktree: worktrees/crmf-1766/salestech-be, branch mohammad/crmf-1766)

## Goals
Teach the **Clean & Transform flow-builder agent** (system A: `node_agents/clean_and_transform_data.py`)
to emit a **top-level `TransformOutputField.field_type`** for non-CRM output fields, drawn from:

    TEXT, NUMERIC, CURRENCY, PERCENT, BOOLEAN_CHECKBOX, TIMESTAMP, LOCAL_DATE, EMAIL, URL, PHONE_NUMBER

Today the agent types a field only when it's CRM-bound (nesting `field_type` inside `crm_binding`);
every non-CRM output falls out as untyped free text. The top-level `field_type` slot already exists
on the model and is already consumed by the runtime (#28591) — this ticket is purely getting the
agent to *produce* it, plus revamping the few-shot examples to demonstrate it. Done = the agent's
signature + examples instruct/demonstrate top-level typing, and (after the gated retrain) the
regenerated program makes the agent reliably emit `field_type` for typed non-CRM outputs while still
omitting it for genuine free-text (summaries/prose).

## Non-goals
- **Runtime system (B)** — `.../clean_and_transform_data/module.py`, `eval_dataset.py`, `judge.py`,
  `core/ai/programs/WorkflowCleanAndTransformData.json`. Owned by a separate PR (updating the runtime
  eval dataset + prompt optimization, and later removing the old field type). Do not touch.
- **Config switch-over** — making top-level `field_type` the single source / deleting
  `CrmFieldBinding.field_type` (CRMF-1768).
- **Enforcing the 10-type allowlist** in code — the config accepts any `NormalizedFieldType` and
  degrades unsupported ones to free text; the restriction stays prompt-only (deliberate, see Decisions).
- Non-CRM SELECT / ENUM / OBJECT_REFERENCE / NESTED (no descriptor to validate against).
- FE / variable-suggestion / UI work.

## Decisions
- **System (B) out of scope** — user is updating the runtime module + its evals in a separate PR;
  runtime already consumes `field_type`, so nothing here depends on it.
- **Retrain is in scope but GATED** — a retrain (`train_agent.py --provider vertex`, real LLM calls,
  flaky) is what makes the new behavior live. It runs only on the user's explicit go-ahead during
  implementation (Task 4). Because retrain regenerates the baked program, it subsumes a standalone
  rebake — there is no separate rebake deliverable.
- **No allowlist backstop** — validators don't inspect top-level `field_type`; unsupported types
  degrade to free text (config.py contract), so no code guard is added. Behavior lives in the
  signature docstring + retrained playbook bullets.
- **Keep genuine free-text examples untyped** — some outputs (summaries, prose notes, unresolved
  refs) must stay `field_type`-less so the agent learns to omit it, not over-type. T2's
  `enrichment_note` and T11's refusal stay untyped on purpose.

## Tasks
- [x] 1. **Signature docstring + `_CONFIG_SCHEMA_HINTS`** — files: `salestech_be/core/flow/agent/node_agents/clean_and_transform_data.py`.
      In `CleanAndTransformDataSignature` docstring (~162-306): extend the `OUTPUT SHAPE` skeleton
      (~174-178) with an optional top-level `field_type` key; at the "leave `crm_binding` unset" clause
      (~185-187) add guidance to set top-level `field_type` to one of the 10 types when a non-CRM output
      has a recognizable value type (and to omit it for genuine free-text/prose); carve out the
      "instruction is the only spec for free-text" statements (~225-227, ~264-268) so they apply only to
      *untyped* unbound fields. Optionally update the inline `EXAMPLE OUTPUT` (~294-305) to show a
      top-level `field_type`. In `_CONFIG_SCHEMA_HINTS` (~49-159): add an `example_typed_field` (a
      non-CRM field with top-level `field_type`, e.g. `cleaned_phone` → `PHONE_NUMBER`) and a
      `non_crm_field_type_note` listing the 10 allowed types.
      Done when: docstring + hints name top-level `field_type` and the 10 types; ruff + mypy clean on the file.

- [x] 2. **Revamp examples** — same file. Add a keyword-only helper `_typed_field(*, name, instruction, field_type)`
      near the binding helpers (~502-550). Add new non-CRM **typed** training examples (T-series list ~1197-1209)
      covering the type surface (at least NUMERIC, CURRENCY, PERCENT, EMAIL, URL, LOCAL_DATE, BOOLEAN_CHECKBOX).
      Retype the free-text **validation** examples whose output has a clear type — e.g. V19
      `_VAL_FREE_TEXT_REVENUE_PER_EMPLOYEE` (~2125) → `NUMERIC` — to assert top-level `field_type`; leave
      genuinely-untyped cases (T2 `enrichment_note`, T11 refusal, a prose summary) `field_type`-less as
      negative coverage. Keep the T/V lists wired (~1197-1209, ~2232-2253).
      Done when: all examples validate structurally via `validate_config`; suite has both typed non-CRM
      and untyped free-text examples.

- [x] 3. **Unit tests** — file: `tests/unit/core/flow/agent/node_agents/test_clean_and_transform_data.py`.
      Add a test that a non-CRM `TransformOutputField` with a top-level `field_type` (and no `crm_binding`)
      passes the agent's `validate_config`; assert a representative new typed example produces the expected
      config shape (top-level `field_type`, no nested binding). Follow existing test patterns in the file.
      Done when: `uv run pytest tests/unit/core/flow/agent/node_agents/test_clean_and_transform_data.py` passes.

> amended: Task 4 (retrain) deferred to AFTER the PR is 100% ready — user wants the PR opened on
> the code changes alone, then a single retrain once all changes are final (avoids wasting a
> training loop mid-iteration). The docstring/example changes have no runtime effect until this
> runs; the PR description must call this out as a pending step.

- [ ] 4. **Retrain + commit regenerated program — HOLD: deferred until PR finalized, then explicit user go-ahead**
      (real LLM calls via vertex; do not run until the user says so during mt-implement). Files:
      `data/flow_builder/playbooks/clean_and_transform_data_playbook.json`,
      `salestech_be/core/flow/agent/programs/clean_and_transform_data.json`.
      Run `uv run python scripts/flow_builder/train_agent.py --train --agents clean_and_transform_data --provider vertex`
      (full run, or incremental `--example-filter "<phrase>" --epochs 2` — user directs the form when
      lifting the hold). Before running, review current playbook bullets for any that contradict non-CRM
      typing. Commit the regenerated playbook + program.
      Done when: program regenerated and committed; `run_agent.py` spot-checks emit top-level `field_type`
      for typed non-CRM prompts (measured over ~10 runs — agent is non-deterministic even at temp 0).

## Verification
- **Coding checks (no LLM, run any time):**
  - `uv run pytest tests/unit/core/flow/agent/node_agents/test_clean_and_transform_data.py`
  - `uv run pytest tests/unit/core/flow/nodes/integration/clean_and_transform_data` (config + executor regression)
  - `uv run ruff check <changed files>` and `uv run mypy <changed files>` (or the repo's standard `deploy/ci/run-code-checks.sh`)
- **Manual checks (post-retrain, in mt-verify, after the Task 4 hold is lifted):**
  - `uv run python scripts/flow_builder/run_agent.py --node "<prompt calling for a typed non-CRM output>" --node-type clean_and_transform_data --provider vertex`
    over ~10 prompts spanning the 10 types; confirm the agent emits top-level `field_type` (measure
    miss-rate) and still omits it for a genuine free-text/summary prompt.
