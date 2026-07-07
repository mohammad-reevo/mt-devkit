# AskReevo node agent — instruction verbosity & correctness — Scope

Linear: CRMF-1747 — https://linear.app/reevo/issue/CRMF-1747

## Idea
The AI-workflow-builder's **node agent** for the Clean & Transform node (the agent
that *authors* per-field instructions) has three quality quirks when it populates a
node config:

1. **Unneeded verbosity** — it emits filler the underlying node model doesn't need
   ("remember the countries of the world"), and rules the node model is *already*
   system-prompted for ("don't output invalid values").
2. **Type-inappropriate / wrong instructions** — e.g. "output only labels" on a
   select-list field: both nonsensical for that field type and already handled by
   the node model's system prompt.
3. **Metadata duplication on bound fields** — it restates a CRM field's allowed
   values / format inside the instruction text, even though that metadata is
   enriched onto the runtime model call for bound fields. Confusing duplicate info.

The through-line: the node agent restates things the **node's runtime model**
already knows (it's Claude, it's system-prompted, and for bound fields it receives
the field's value contract). Fix is prompt/example tuning **entirely within the
node agent** — no runtime-model, improve-instructions, or new-logic changes.

Keep two things distinct (the ticket conflates them):
- **Node agent** — DSPy agent the workflow builder uses to *write* instructions
  (`core/flow/agent/node_agents/clean_and_transform_data.py`). This is the fix surface.
- **Node runtime model** — Claude that *executes* each instruction at flow time
  (`core/flow/nodes/integration/clean_and_transform_data/module.py`). Not changed;
  it's the source of truth for "what's already covered."

## What the runtime already enforces (grounding for the fix)
The runtime seed instructions already tell the executing model, for every
**CRM-bound** field: return values drawn only from `allowed_values` verbatim, never
invent outside the set; MULTI_SELECT → JSON array; match `value_format` exactly; and
use the field's display name / description / help_text to choose the right value.
A **bound** field carries this constraint + CRM context; an **unbound** field gets an
empty constraint → the runtime falls back entirely to the instruction text. So the
redundancy the ticket describes holds **only for bound fields**; unbound/user-defined
fields have no metadata backstop and legitimately need the detail in the instruction.

## Approaches considered

### Node-agent-only, binding-conditional (CHOSEN)
Teach the authoring agent what the runtime model already enforces, and make
instruction detail conditional on whether the output field is CRM-bound. Covers all
three quirks at their single root. Matches the ticket's "improve examples and docs."

### Two-surface (node agent + Improve-instructions prompt) — rejected
Also touch the "Improve instructions" rewrite prompt so it strips redundant metadata
from already-authored instructions. Rejected: user scoped the fix to the node agent;
the Improve path is metadata-blind and only *preserves* redundancy — stopping the
source (the authoring agent) is the intended fix.

### Deterministic post-processing guardrail — rejected
Code that strips/rejects nonsensical directives on select fields after generation.
Rejected: over-engineered for a quality-tuning ticket, invents logic not asked for,
and contradicts the "examples and documentation" framing.

## Chosen direction
Inside the node agent, apply one principle: **don't restate what the runtime model
already knows.**

- **Make the authoring agent runtime-aware by paraphrase** (fork 1 → option a): add a
  concise "what the runtime already enforces" note + a "don't restate it for bound
  fields" rule to the agent's own documentation. Paraphrase the *principle*, not the
  runtime's verbatim mechanics — minimal coupling, low drift risk. Do **not** single-
  source the runtime's full prose into the authoring prompt.
- **Binding-conditional instruction detail:**
  - Bound field → lean instruction (what to derive, from which input path); omit
    allowed-values restatement, format rules, "pick a valid value," output-shape
    directives, and any type-nonsensical directive (the "output only labels" class).
  - Unbound field → keep shape/format/value detail; no runtime backstop exists.
- **Cut model-insulting filler** across both (the "countries of the world" class).
- Land the change in **both** the agent's documentation/rules **and** its few-shot
  examples — the baked examples are what actually steer behavior, and several current
  examples model the bad habit. Then re-bake the agent's program artifact.

## Open questions
- **Verbosity is judged by eye** (fork 2 → option i): run the agent eval harness
  (`scripts/flow_builder/run_agent.py`) to capture a **baseline sample now**, apply the
  change, re-run, and eyeball before/after for "leaner but still correct." Correctness
  stays the harness's job (miss-rate); temp=0 is flaky so judge over ~10 runs, not one.
  No scored conciseness metric — out of scope.
- Which specific few-shot examples currently restate allowed values / model verbose
  or type-inappropriate instructions, and how many need reworking (bound vs unbound).
  mt-plan to enumerate against the training + validation example sets.
- Confirm the paraphrased "runtime already enforces" note stays a *principle* and
  doesn't turn into a second copy of the seed-instruction mechanics (drift guard).
- Re-bake step: which program artifact(s) must be re-baked and committed alongside the
  source edits (paired-file hygiene).

## Out of scope
- The "Improve instructions" / AskReevo rewrite prompt (`prompt_improvement.py`).
- The node runtime model, its seed instructions, and its enriched metadata.
- Any new deterministic validation/guardrail logic.
- A scored verbosity/conciseness eval metric.
- Retraining the agent from scratch (example/doc tuning + re-bake only, unless mt-plan
  finds tuning insufficient).
