# Reference — call-chain spine

The worked example the second `make-diagram` grammar was derived from. Match this shape.

Source: explaining CRMF-2317 / PR #32637 to its own author. The ask was *"one viz for all the
files in their calling order"* — the diff was unreadable because 40 of its "deleted" lines were
the old code re-indented into an `else:`. Pipeline-with-a-fork couldn't hold it: the question
wasn't *where do consumers diverge*, it was *what calls what, and which file owns each step*.

## The diagram

```
ENTRY ── two callers, only one of them resolves the flag ─────────────────────

  graph_topology.py :1165                 manual_workflow_detection_service.py
    _perform_node_validation                _evaluate_promote_ready       [+5]
        │                                         │
        │ :1188 _is_inline_formula_typing_        │  builds the service with
        │        enabled(org_id)         [+25]    │  NO flag arg -> defaults
        │        ONE PostHog call per run         │  False, so mining stays
        │        org_id None -> False             │  on the substitution path
        ▼                                         ▼  promote_readiness.py :46
  NodeValidationService(..., inline_formula_typing_enabled: bool)
        │
        └──────────────────┬──────────────────────┘
                           ▼

PER NODE ── node_validator.py :413 ──────────────────────────────────────────

  validate_node_promote_eligibility(node, validation_service)
        │
        ├─► _validate_user_references(...)                     pre-existing
        │
        ├─► _validate_inline_formulas(node, service)  :942   NEW  [+27]
        │        5-line wrapper, mirrors the line above         SURFACE B
        │        calls service.validate_inline_formulas(node)
        │
        └─► match node:  -> the node-type validator             SURFACE A
                 ComputeValidator.validate_promote_eligibility
                 EmailSendValidator -> validate_value_coded -> side path

SURFACE B ── node_validation_service.py :310 ────────────────────────────────

  validate_inline_formulas(node) -> list[NodeValidationError]
        │
        │  flag OFF -> return []          the whole hook is a no-op
        │  find_formula_token_sites(node.config)        pre-existing walker
        │  dedupe by formula id -> ONCE per DEFINITION, not per use site
        │
        └─► validate_formula_typed(definition.formula, node_id) ──────┐
                                                                      │
SURFACE A ── compute/single/validator.py :68 ───────────────────────  │  ───
                                                                      │
  ComputeValidator.validate_promote_eligibility(config, service, id)  │
        │                                                             │
        │  READS service.inline_formula_typing_enabled                │
        │  never re-resolves it -> both surfaces of a run agree       │
        │                                                             │
        ├── flag OFF ─► _substitute_templates_with_dummies            │
        │               formula_validator_service.validate_formula    │
        │               ^ untouched. this is today's behaviour, and   │
        │                 the 40 "deleted" lines in the diff are      │
        │                 these same lines re-indented into the else  │
        │                                                             │
        └── flag ON ──► validate_formula_typed(config.formula, id) ───┤
                                                                      │
SHARED ── the one method both surfaces call ────────────────────────  │  ───
                                                                      ▼
  node_validation_service.py :270
  validate_formula_typed(formula, node_id) -> list[FormulaError]     NEW
        │
        │  _resolve_schema_builder() :371  injected -> singleton -> local
        ▼
  formula_reference_types.py                             NEW FILE  [+98]
  build_reference_types(formula, node_id, flow_def, schema_builder, ...)
        │
        │  schema_builder.validate_template_at_node_with_context(...)
        │      ^ ALREADY RAN before this PR; only .valid was kept
        │  unresolvable / union / container -> ANY    NEVER UNKNOWN
        ▼
  dict[str, FormulaFieldType]
        │
        ▼
  formula_text_validation.py                                    [+108/-14]
  validate_formula_with_types(formula, parser_service, reference_types)
        │
        │  try #1  _run_stages    syntax -> parse -> functions
        │  try #2  the type stage
        ▼
  type_inference.py                                               [+10/-1]
  TypeInferenceEngine(reference_types=...)
        │
        │  _infer_reference_type: THE MAP first, scope registry second
        ▼
  list[FormulaError]
        │
        ▼
  node_validation_service.py :65
  format_invalid_formula_message(formula, error)                     NEW
      one wording, so the sync and typed paths cannot drift


SIDE PATH ── the sync per-field check, reached inside `match node:` ─────────

  node_validation_service.py :136  validate_value_coded(value, field_name)
        └─► :403 _validate_formula_tokens_in_value
                 token exists? definition exists?     always runs
                 validate_formula_text(...)           SKIPPED when flag ON
                 ^ the ONLY non-additive change in the PR
```

## What each convention buys

**Section header = phase + `file.py :LINE`.** The phase word is the reader's spine (`ENTRY`,
`PER NODE`, `SHARED`); the `file:line` is what makes every claim checkable. Neither works alone
— a phase with no location is a vibe, a location with no phase is a stack trace.

**Diff stats per file** (`[+27]`, `[+108/-14]`, `NEW FILE [+98]`). This is what turns a call
chain into a *PR* explanation. It also does the reviewer a favour the diff can't: it shows at a
glance which files are wiring (`[+5]`, `[+25]`) and which hold the change.

**Naming re-indentation explicitly.** `^ the 40 "deleted" lines in the diff are these same lines
re-indented into the else` was the single most useful line on the page — it dissolved the
author's impression that logic had been migrated out of a file when nothing had moved.

**Marking unchanged branches as unchanged.** A flag-gated PR has a whole column that is
"today's behaviour". Saying so in the drawing is what makes the flag-on column readable as *the
change*, rather than the reader re-deriving the delta.

**Two entry points, drawn side by side.** The asymmetry — one caller resolves the flag, one
leaves it at its default — was the most load-bearing fact in the whole PR and appeared nowhere
in the diff as a diff. When two callers reach one spine, draw both.

**The rail.** Surface B's call travels *past* the Surface A block to the shared section: they
are at different depths of one traversal, not siblings. Carry it in a fixed right-hand column,
break the intervening section headers around it (`──────  │  ───`), and merge with `┤`. This is
exactly the relationship mermaid's auto-layout destroys, and the reason to keep an ASCII copy
even when a rendered version exists.

## Traps

- **Rail drift.** Hand-counting the rail column is wrong by one within about four lines. Verify
  programmatically before showing it (see SKILL.md → Width).
- **Byte-vs-character width.** `awk length()` counts bytes; box-drawing glyphs are 3 bytes each.
  Measure in Python or you will "fix" a correct drawing.
- **Don't invent the phases.** They must be real boundaries in the call chain, not a narrative
  imposed on it. If a section header doesn't correspond to a function actually being entered,
  it's decoration.
