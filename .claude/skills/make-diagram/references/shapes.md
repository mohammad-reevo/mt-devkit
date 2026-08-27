# Reference — the shapes

The worked examples the two `make-diagram` grammars were derived from. Match these.

Both are real cases, and both were drawn because prose had already failed at the same job.

---

# 1. Pipeline with a fork

Source: the CRMF-2202 formula-token-rendering design. Two consumers (execution and display)
share one resolution path and diverge at exactly one point. Prose about it was unreadable; the
drawing made it obvious at a glance. That gap is why the skill exists.

Use it when the question is **"where do the consumers diverge"**.

```mermaid
flowchart TD

  subgraph M1["config_string_walk.py — mechanics, no evaluation"]
    F1["find_formula_token_sites(*, model, skipped_fields)<br/>in : BaseModel, Container[str]<br/>out: list[Site] · Site = (path, text, formula_keys)<br/>one Site per STRING holding tokens · walks once"]
    F2["substitute_formula_tokens(*, model, sites, results)<br/>in : BaseModel, list[Site], Mapping[key, str]<br/>out: SubstitutionResult(config, changed)<br/>writes each site AT its path · no re-search"]
  end

  subgraph M2["flow_formula_resolution_service.py — evaluation + wrapper 1"]
    F3["evaluate_config_formulas(*, config, context_dict, formula_keys)<br/>in : BaseNodeConfig, JSONObject, Collection[str]<br/>out: FlowFormulaResults(values, errors)<br/>each distinct key evaluated once · NEVER raises"]
    F4["get_resolved_formulas(*, config, context_dict)<br/>in : BaseNodeConfig, JSONObject<br/>out: ResolvedFormulas(sites, values, errors)<br/>= find_formula_token_sites → flatten keys → evaluate"]
  end

  IN["config + context_dict"]
  RES["ResolvedFormulas(sites, values, errors)"]
  FORK{"the ONLY fork<br/>execution raises on error · display renders it"}

  A1["WRAPPER 2a · execution<br/>resolve_config_formula_tokens<br/>if errors: raise the first"]
  B1["WRAPPER 2b · display<br/>_resolve_config_formulas<br/>text = values, blank_or_ERROR per failed key"]
  A2["substitute_formula_tokens(model, sites, values)"]
  B2["substitute_formula_tokens(model, sites, text)"]
  A3["node executor"]
  B3["_render_config<br/>then overlay field: value"]

  IN --> F4
  F4 --> RES --> FORK
  FORK -->|execution| A1 --> A2 --> A3
  FORK -->|display| B1 --> B2 --> B3

  classDef shared fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
  classDef fork fill:#fef3c7,stroke:#d97706,color:#78350f
  class F4,RES shared
  class FORK fork
```

## What each element buys

Every one of these is load-bearing, not decoration.

| Element | What it buys |
|---|---|
| `subgraph "file.py — role"` | Names the module **and its boundary**. "mechanics, no evaluation" tells you what the file refuses to do — usually the more useful half. |
| `in :` / `out:` inside the node | The reader never scrolls to a signature list. The single biggest win over a bulleted function list. |
| A type alias inline (`Site = (path, text, formula_keys)`) | Expands the shape at the point of use instead of in a separate legend. |
| One logic line per function | Forces the essential clause out. Two lines means you haven't decided what matters. |
| The value on the wire as its own node (`ResolvedFormulas(...)`) | Makes the flow readable without re-reading the modules above. |
| `{"the ONLY fork"}` as a diamond, styled | **The point of the whole drawing.** A falsifiable claim: exactly one divergence. If a reviewer knows of a second, the diagram is wrong and they'll say so — which is the diagram earning its keep. |
| Edge labels `execution` / `display` | Names *what* forks, not merely that something does. |
| Identical `substitute_formula_tokens(...)` on both branches | Duplication drawn honestly. Both branches call the same function with a different mapping — visible instantly, invisible in prose. |
| Branch B continuing past its terminal | Branches don't have to be symmetric. Draw the real lengths. |

**The one thing to copy above all:** the fork node. A two-consumer pipeline has exactly one
interesting fact — *where* the consumers diverge — and every other format buries it. Give it its
own node, colour it, and say the count in the walkthrough.

---

# 2. Call-chain spine

Source: explaining CRMF-2317 / PR #32637 to its own author. The ask was *"one viz for all the
files in their calling order"* — the diff was unreadable because 40 of its "deleted" lines were
the old code re-indented into an `else:`.

Use it when the question is **"what calls what, across these files, in order"** — a PR
walkthrough, or tracing an entry point to its leaf.

```mermaid
flowchart TD

  subgraph S1["ENTRY — only one caller resolves the flag"]
    GT["graph_topology.py :1165<br/>_perform_node_validation"]
    FF["_is_inline_formula_typing_enabled :1447<br/>ONE PostHog call per run<br/>org_id is None → False<br/>+25"]
    MW["manual_workflow_detection_service.py<br/>_evaluate_promote_ready<br/>NO flag arg → default False<br/>mining stays on the old path · +5, comment only"]
    SVC["NodeValidationService(...)<br/>out: inline_formula_typing_enabled: bool"]
    GT --> FF --> SVC
    MW --> SVC
  end

  subgraph S2["PER NODE — node_validator.py :413"]
    NV["validate_node_promote_eligibility(node, service)"]
    IFH["_validate_inline_formulas :942<br/>5-line wrapper · +27"]
    MATCH["match node: → the node-type validator"]
    NV --> IFH
    NV --> MATCH
  end

  subgraph S3["THE TWO SURFACES"]
    B["SURFACE B · node_validation_service.py :310<br/>validate_inline_formulas(node)<br/>out: list[NodeValidationError]<br/>deduped: ONCE per definition, not per use site"]
    A["SURFACE A · compute/single/validator.py :68<br/>ComputeValidator.validate_promote_eligibility<br/>READS the bool · never re-resolves the flag"]
    AOFF["_substitute_templates_with_dummies<br/>every reference becomes the literal 0<br/>UNCHANGED — the 40 deleted lines in the diff<br/>are these same lines re-indented into the else"]
    A -->|flag OFF| AOFF
  end

  subgraph S4["SHARED — the one method both surfaces call"]
    VFT["node_validation_service.py :270<br/>validate_formula_typed(formula, node_id)<br/>out: list[FormulaError] · NEW"]
    BRT["formula_reference_types.py — NEW FILE +98<br/>build_reference_types(...)<br/>out: dict[str, FormulaFieldType]<br/>unresolvable → ANY, never UNKNOWN"]
    VFWT["formula_text_validation.py — +108/-14<br/>validate_formula_with_types(...)<br/>syntax → parse → functions → types"]
    VFT --> BRT --> VFWT
  end

  SVC --> NV
  IFH --> B
  MATCH --> A
  B --> VFT
  A -->|flag ON| VFT

  classDef newcode fill:#dcfce7,stroke:#16a34a,color:#14532d
  classDef untouched fill:#f1f5f9,stroke:#94a3b8,color:#334155
  classDef flagnode fill:#fef3c7,stroke:#d97706,color:#78350f
  classDef shared fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
  class FF,SVC flagnode
  class IFH,B,VFT,BRT newcode
  class AOFF,MW untouched
  class VFWT shared
```

## What each element buys

| Element | What it buys |
|---|---|
| `subgraph "PHASE — file.py :LINE"` | The phase is the reader's spine; the `file:line` is what makes every claim checkable. Neither works alone — a phase with no location is a vibe, a location with no phase is a stack trace. |
| Diff stat on every file (`+27`, `+108/-14`, `NEW FILE +98`) | Turns a call chain into a *PR* explanation. Shows at a glance which files are wiring and which hold the change. |
| Naming re-indentation explicitly | The single most useful line in the source case — it dissolved the author's impression that logic had been migrated out of a file when nothing had moved. |
| `untouched` class on the flag-off branch | A flag-gated PR has a whole column that is today's behaviour. Saying so is what makes the other column readable as *the change*. |
| Two entry points drawn side by side | The asymmetry — one caller resolves the flag, one leaves it at its default — was the most load-bearing fact in the PR, and it appeared nowhere in the diff *as* a diff. |
| Edge labels `flag OFF` / `flag ON` | The fork, in a shape that has no single fork node. |

## What this shape loses to auto-layout — say it in the walkthrough

In the source case Surface B's call travels *past* the Surface A block to reach the shared
section: they are at different depths of one traversal, not siblings. Mermaid draws them as
siblings and there is no idiom that fixes it. **That is not a reason to avoid the shape** — it's
a reason the walkthrough must carry the sentence the picture can't.

Same for anything living in a margin rather than a node: cross-references, "this is the only
non-additive change", counts. Put them in the walkthrough.

## Traps

- **Don't invent the phases.** They must be real boundaries in the call chain, not a narrative
  imposed on it. If a section title doesn't correspond to a function actually being entered,
  it's decoration.
- **A long node label is fine; a long node label doing two jobs is not.** Contract, then one
  logic line, then the diff stat. If you need a fourth line, you're explaining rather than
  drawing — move it to the walkthrough.
