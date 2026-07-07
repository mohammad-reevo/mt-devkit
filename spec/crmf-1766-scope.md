# Update node agent for non-CRM field types — Scope

> Name: crmf-1766   (the slug — names the scope/plan files, the worktree, and branch mohammad/crmf-1766)

## Idea
The Clean & Transform node agent types an output field only when it's CRM-bound (it
stuffs `field_type` into `crm_binding`); every non-CRM output falls out as unvalidated
free text. PR #28591 (CRMF-1763, now merged to main) added a top-level
`TransformOutputField.field_type` so a non-CRM output *can* be typed and validated. This
ticket teaches the node agent to actually use it — pick an appropriate `NormalizedFieldType`
for non-CRM outputs instead of leaving them as text — and revamps its examples accordingly.

## Approaches considered

### A. Node-agent-only, additive on top of #28591 (chosen)
Touch only the node-agent layer: update the prompt/signature to instruct the agent to set
top-level `field_type` for non-CRM outputs, add/revamp training examples that demonstrate
non-CRM typed outputs, rebake + retrain the baked program, and extend the eval dataset +
judge. No config, executor, suggestion-service, or `CrmFieldBinding` changes. CRM-bound
fields keep nesting `field_type` in the binding exactly as today; only the non-CRM path is
new. Contained, matches the ticket title, low blast radius.
- Tradeoffs: requires a rebake + retrain (docstring/example edits are inert until rebaked)
  and an eval-dataset update — the bulk of the effort is prompt/example quality + eval, not
  code. Depends on #28591 (satisfied — merged).

### B. Bundle the full config switch-over (rejected)
Also make top-level `field_type` the single source for *all* fields and delete
`CrmFieldBinding.field_type` (the CRMF-1768 "unify" TODO). Rejected: explicitly deferred by
the user to CRMF-1768. It's a separate change (config model + suggestion service + backfill
concerns) and would make this PR a half-migration instead of a focused agent touch-up.

## Chosen direction
Additive node-agent update (Approach A). The agent learns to emit a top-level `field_type`
for non-CRM outputs, drawn from the confirmed relevant set:

    TEXT, NUMERIC, CURRENCY, PERCENT, BOOLEAN_CHECKBOX, TIMESTAMP, LOCAL_DATE, EMAIL, URL, PHONE_NUMBER

(These are the type-alone-resolvable set plus TEXT/BOOLEAN. Non-CRM SELECT/ENUM/reference are
deliberately excluded — they degrade to free text without a CRM descriptor, so the agent
should not emit them for non-CRM outputs.)

Shape of the change, at altitude:
- **Prompt/signature** — instruct the agent that a non-CRM output should carry a best-fit
  top-level `field_type` rather than defaulting to text.
- **Examples** — add/revamp training examples so the agent has non-CRM typed outputs to learn
  from (e.g. a NUMERIC total, a CURRENCY amount, an EMAIL, a LOCAL_DATE), alongside the
  existing CRM-bound examples.
- **Rebake + retrain** — regenerate the baked program(s) so the edits take runtime effect.
- **Eval + judge** — extend the eval dataset and judge to cover non-CRM typed outputs.

CRM-bound behavior is unchanged; `crm_binding.field_type` stays as-is (its removal is CRMF-1768).

## Testing
- **Unit / agent-config** — the agent, given inputs that call for typed non-CRM outputs,
  emits top-level `field_type` from the allowed set (not nested in a binding, not defaulted to
  text); CRM-bound examples still emit their binding unchanged.
- **Agent eval** — the retrained program passes the (updated) eval dataset via the judge; this
  is the primary quality gate for "revamp examples." Measure over multiple runs — the agent is
  non-deterministic even at temp 0.
- No new E2E / integration — backend agent-layer only, no user-facing surface added by this
  ticket. Executor/resolver validation of the new types is already covered by #28591's tests.

## Open questions
- **How much eval churn belongs here?** The eval dataset + judge (`eval_dataset.py`, `judge.py`)
  currently encode field-type-in-binding. Updating them to the new non-CRM-typed shape is part
  of the quality gate, but the extent (add a handful of non-CRM cases vs a broad revamp) is a
  plan-time sizing call.
- **Retrain scope** — whether a full retrain is needed or a rebake of the playbook program
  suffices; confirm against `agent/CLAUDE.md` rebake/retrain guidance at plan time.

## Out of scope
- Making top-level `field_type` the single source for all fields / deleting
  `CrmFieldBinding.field_type` (CRMF-1768).
- Any config-model, executor, or suggestion-service changes.
- Non-CRM SELECT / ENUM / OBJECT_REFERENCE / NESTED support (no descriptor to validate against).
- FE / variable-suggestion / UI work.
