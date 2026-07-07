# AskReevo node agent — instruction verbosity & correctness — Plan

> Scope: crmf-1747-scope.md
> Repo: /Users/mohammad/Desktop/code/devkit/worktrees/crmf-1747/salestech-be (worktree off origin/main, branch mohammad/crmf-1747-askreevo-node-agent-verbosity-and-instruction-handling)
> amended: work runs in a worktree (primary checkout is gate-blocked for edits)
> Linear: CRMF-1747 — https://linear.app/reevo/issue/CRMF-1747

## Goals
The Clean & Transform **node agent** stops restating what the node's runtime model
already enforces, conditional on binding:
- **CRM-bound fields** → lean instructions: transform verb + source path + any format
  that is the actual transformation goal. No echoing of allowed-values / field-type
  shape / "output a single value" — the runtime constraint enforces those. No
  type-inappropriate directives (the "output only labels" class).
- **Unbound / free-text fields** → keep full shape/format/value detail; no runtime
  backstop exists for them.
- No model-insulting filler ("remember the countries of the world", "don't output
  invalid values") anywhere.

Behavior reaches runtime through two channels, both updated here:
1. **Docstring** → `bake` → `programs/clean_and_transform_data.json` (deterministic).
2. **Few-shot examples** → `train_agent.py` (ACE, LLM) → regenerated playbook JSON →
   `bake` → same program artifact.

## Non-goals
- The "Improve instructions" rewrite prompt (`prompt_improvement.py`).
- The node runtime model / its seed instructions / enriched metadata (`module.py`).
- Any new deterministic validation/guardrail logic.
- A scored verbosity metric (verbosity judged by eye).
- New invented example cases beyond modeling the lean form.

## Decisions
- **Runtime-awareness = paraphrase in the docstring** (scope fork 1a): the *principle*,
  not the runtime's verbatim mechanics (drift guard).
- **Verbosity judged by eye** (scope fork 2i) via `run_agent.py` baseline-then-compare.
- **Both channels + retrain** (user decision, supersedes scope's "no retrain"): examples
  are NOT baked as demos — they reach runtime only via a training run that regenerates
  the ACE playbook. So edit docstring AND examples AND run `train_agent.py`, then re-bake.
- **Train mode = incremental** (project default), but only after pruning
  restatement-reinforcing strategies from the current playbook (Task 5) so the
  continuation doesn't carry the habit forward. Provider = `vertex` (local
  `ANTHROPIC_API_KEY` unset).
- **Test-safety invariants** (hold through all example edits): keep ≥1 `{{$.…}}` per
  instruction; keep every binding + `select_list_id`; keep the bound-majority (>half of
  training examples carry a `crm_fields` seed); preserve a symptom-fix trigger keyword
  (`returned`/`echoed`/`inconsistent`/`added an explanation`) in
  `_VAL_EDIT_REVENUE_NUMBER`'s description.

## Slimming rule (every bound-field instruction in Tasks 3–4)
- **KEEP:** transform verb, source `{{$.…}}` path, and any format that is the actual
  transformation asked for (E.164, "Street, City, State ZIP" assembly, 1.2M→number).
- **DROP:** trailing meta-restatements echoing the field's contract — "output one of
  the allowed X values", "output a single value", "output a bare string/number",
  "output true or false", numeric "no words or surrounding sentence" when it only
  restates numeric-type enforcement.
- **Unbound fields:** leave untouched.

## Tasks

- [x] 1. **Capture baseline** — file: `/Users/mohammad/.claude/jobs/7053f138/tmp/crmf-1747-baseline.txt` (scratch; job tmp dir).
      > amended: baseline saved to job tmp dir, not repo tmp/. Dry-run DID yield a bound SINGLE_SELECT `industry` field, so bound-field comparison is exercisable after all.
      Run `run_agent.py` on 3 prompts, save the printed configs:
      ```
      uv run python scripts/flow_builder/run_agent.py --node "Classify the account's industry from its description and set it on the account, and summarize the description for review" --node-type clean_and_transform_data --provider vertex
      uv run python scripts/flow_builder/run_agent.py --node "Split the contact full name into first and last name" --node-type clean_and_transform_data --provider vertex
      uv run python scripts/flow_builder/run_agent.py --node "Format the contact phone number into E.164" --node-type clean_and_transform_data --provider vertex
      ```
      Done when: the 3 generated configs (with `fields[].instruction` prose) are saved for diffing.

- [ ] 2. **Docstring edits** — file: `salestech_be/core/flow/agent/node_agents/clean_and_transform_data.py` (`CleanAndTransformDataSignature`, lines ~162–303).
      (a) Insert a **"WHAT THE RUNTIME ALREADY ENFORCES"** subsection after `CRM BINDING`
      (after line 214): for a bound field the runtime enforces `allowed_values` (draws only
      from the set, never invents), `field_type` (single value vs MULTI_SELECT array), and
      `value_format`, and is given the field's display name / description / help_text — so
      the instruction MUST NOT restate any of it. Paraphrase the principle only; do not copy
      `module.py`'s seed-instruction prose.
      (b) Soften the SHAPE bullet (lines 251–252): state output shape explicitly **only for
      unbound / free-text outputs**; for a bound output the type/format is already enforced.
      (c) Add a rule: never dictate how a select / enum / boolean field formats or labels its
      output (the "output only labels" class), and never add model-insulting filler.
      Done when: docstring has the new subsection + softened bullet + new rule; file lints.
      > amended: also fixed the prompt-facing `_CONFIG_SCHEMA_HINTS` block (injected into
      > `node_schema` via `get_config_schema()`, line 436) — softened `instruction_anti_patterns_note`
      > ("always state shape" → free-text only) and slimmed `example_bound_field` ("Output one of the
      > allowed stage values" dropped). Necessary: it's live prompt content that otherwise contradicts
      > the new docstring rule.
      > done: 3 docstring edits + 2 schema-hint edits applied; ruff clean + parse OK.

- [ ] 3. **Slim bound training examples** — same `.py`, dicts lines ~537–1178. Apply the
      Slimming rule. **Strong (drop picklist restatement):** T2 `industry_vertical`,
      T3 `technology`, T4 `account_status`, T8 `sales_territory`, T9 `seniority`.
      **Mild (drop trailing "output a bare X"):** remaining bound fields in T1, T2
      `estimated_annual_revenue`, T5. **Untouched:** unbound (T2 `enrichment_note`,
      T9 `clean_title`, T11 `risk_level`), legit-transform (T6 `billing_address`,
      T7 `risk_level` TEXT). **Symptom-fix (T10 `_EXAMPLE_EDIT_SCORE_TO_NUMBER`):** keep its
      pedagogical instruction — it teaches the "don't add words" fix.
      Done when: the 5 strong instructions no longer name the allowed-value set; placeholders + bindings intact.
      > done: T1 email/phone, T2 industry/is_enterprise/revenue, T3 technology, T4 account_status,
      > T5 first/last, T8 sales_territory, T9 seniority slimmed. Untouched: T2 enrichment_note (unbound),
      > T6 billing_address + T7 custom risk (legit-transform), T9 clean_title (unbound), T10 symptom-fix,
      > T11 (unbound). grep confirms no picklist restatements remain in training.

- [ ] 4. **Slim bound validation examples** — same `.py`, lines ~1380–1560.
      **Strong:** `_VAL_SENIORITY`, `_VAL_LEAD_SOURCE`, `_VAL_INTERESTS`, `_VAL_EMAIL_STATUS`.
      **Mild:** other bound V-examples per the Slimming rule. **Preserve:**
      `_VAL_EDIT_REVENUE_NUMBER`'s symptom-fix keyword in its description; unbound V18–V21 untouched.
      Done when: strong validation instructions slimmed; Task 7 structural tests pass.
      > done: strong V5–V8 (seniority/lead_source/interests/email_status) slimmed. Mild bound
      > restatements also dropped where pure type-restatement + safely targetable: V1 URL, V3 percent,
      > V4/V12 numeric, V11 headquarters, V13 revenue, V16 email, V17 phone, V14 phone. KEPT transform
      > detail (ISO date, 'City, Country', 'no percent sign', mapping polarity on V9 bool). KEPT unbound
      > free-text (V18–V21) and symptom-fix (V15, T10) untouched. Symptom-fix keyword ("returned")
      > confirmed present.
      > amended: also slimmed T6 billing_address trailing "Output a bare string" (plan said untouched)
      > — same bound-TEXT pattern as V11, kept for corpus consistency; format transform preserved.

- [ ] 5. **Prune restatement strategies from the playbook** — file:
      `data/flow_builder/playbooks/clean_and_transform_data_playbook.json`. Remove ACE
      strategies that reinforce restating output shape / picklists for bound fields (they'd
      survive an incremental retrain). If none exist, note it and change nothing.
      Done when: no playbook strategy contradicts the Task 2 rule.
      > done: removed 11 pro-restatement bullets (incl. helpful=29 str-438cc "list representative example
      > values" and helpful=32 str-bf2ef "output a bare integer/number" — the strongest carriers of the
      > habit under the old examples), 101→90. Edited 2 mixed bullets (currency, E.164) to strip the
      > bare-type tail while keeping transform guidance. Kept casing bullets (legit for unbound example
      > labels). JSON valid.

- [ ] 6. **Retrain over the edited examples** — regenerates the playbook.
      ```
      uv run python scripts/flow_builder/train_agent.py --train --agents clean_and_transform_data --epochs 2 --provider vertex
      ```
      Incremental (continues from the pruned playbook). Confirm it consumes the edited
      examples and rewrites `clean_and_transform_data_playbook.json`.
      Done when: training completes, playbook regenerated, no restatement strategy reintroduced (spot-check).
      > done: 2 epochs completed via vertex (~9 min), playbook 90→107 bullets. Spot-check: ZERO
      > picklist/allowed-values restatement bullets reintroduced. ACE learned the bound/unbound split —
      > remaining "Output a bare string" bullets are scoped to enrichment-note/free-text (unbound, legit)
      > or the symptom-fix example; one generic "avoid 'Score: 75' → bare value" numeric anti-pattern kept
      > (guards a real formatting mistake, not the targeted restatement).

- [ ] 7. **Coding checks** (before bake).
      ```
      make pytest tests/unit/core/flow/agent/node_agents/test_clean_and_transform_data.py
      make pytest tests/unit/core/flow/agent/test_training_schema_parity.py
      make pytest tests/unit/scripts/flow_builder/test_check_playbook_hygiene.py
      uv run ruff check salestech_be/core/flow/agent/node_agents/clean_and_transform_data.py
      uv run mypy salestech_be/core/flow/agent/node_agents/clean_and_transform_data.py
      ```
      Done when: green (example integrity, parity/ratio, symptom-fix, bound-majority, playbook hygiene).
      > done: 473 passed / 0 failed / 524 skipped (VCR/integration-gated). All 11 training + 21 validation
      > Pydantic checks, train/val ratio, symptom-fix ran + passed. ruff clean, mypy clean on the file.

- [ ] 8. **Re-bake + verify + pair** — file: `salestech_be/core/flow/agent/programs/clean_and_transform_data.json`.
      ```
      uv run python scripts/flow_builder/bake_playbooks.py --agents clean_and_transform_data
      ```
      Verify the baked `predictor.signature.instructions` contains the new
      "WHAT THE RUNTIME ALREADY ENFORCES" text + softened SHAPE bullet and reflects the
      retrained playbook. Commit program JSON + playbook JSON alongside the `.py`.
      Done when: baked artifact reflects docstring + retrained playbook; paired files committed together.
      > done: baked 107 bullets → programs/clean_and_transform_data.json. Verified instructions contain
      > the new "WHAT THE RUNTIME ALREADY ENFORCES" section, softened SHAPE bullet, "output only the
      > labels" anti-rule, "countries of the world" anti-filler; the only allowed-values phrase is the
      > rule's own negative example. Commit of paired files folded into close-out.

- [ ] 9. **After-change eyeball** — re-run the 3 Task-1 prompts, diff prose against
      `tmp/crmf-1747-baseline.txt`. Confirm leaner instructions, no filler, unbound fields
      still detailed.
      Done when: verbosity reduction confirmed by eye with correctness intact; noted in close-out.
      > done: bound `industry` instruction went from "...Output one short industry label such as
      > Technology, Healthcare... Output a bare string." → "Classify the industry ... {{...}}." (label-list
      > + shape restatement gone; binding + classify verb intact). Unbound fields correctly kept "Output a
      > bare string". Binding-conditional behavior confirmed at runtime. Baseline/after saved in job tmp.

## Verification
- **Coding checks** — the Task 7 suite, then the after-stop
  `cd salestech-be && uv run deploy/ci/run-code-checks.sh`.
- **Manual checks** — `run_agent.py` baseline (Task 1) vs after (Task 9) on the 3 prompts;
  eyeball that (i) bound-field instructions no longer restate allowed values / format,
  (ii) no filler, (iii) unbound fields still carry detail.
  **Caveat:** the `--node` dry run doesn't seed a live `crm_fields` roster, so fields often
  come back free-text (unbound) — the eyeball cleanly shows filler/verbosity reduction but
  may not exercise bound-field slimming directly. Bound-field confidence rests on the
  deterministic docstring change + slimmed examples + retrained playbook, cross-checked by
  inspecting the baked `programs/*.json` instructions.
