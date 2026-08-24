# Reference — pipeline with a fork

The worked example the `make-diagram` grammar was derived from. Match this shape.

Source: the CRMF-2202 formula-token-rendering design. Two consumers (execution and display)
share one resolution path and diverge at exactly one point. Prose about it was unreadable; this
drawing made it obvious in a glance. That gap is why the skill exists.

## The diagram

```
┌─ config_string_walk.py ─ mechanics, no evaluation ───────────────────────────┐
│                                                                              │
│  find_formula_token_sites(*, model, skipped_fields)                          │
│      in :  BaseModel, Container[str]                                         │
│      out:  list[Site]      Site = (path, text, formula_keys)                 │
│      one Site per STRING holding token(s); walks once                        │
│                                                                              │
│  substitute_formula_tokens(*, model, sites, results)                         │
│      in :  BaseModel, list[Site], Mapping[key, str]                          │
│      out:  SubstitutionResult(config, changed)                               │
│      writes each site's substituted string AT its path · no re-search        │
│      stamps ResolvedTemplateString when original text had no {{ }}           │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ flow_formula_resolution_service.py ─ evaluation + wrapper 1 ────────────────┐
│                                                                              │
│  evaluate_config_formulas(*, config, context_dict, formula_keys)             │
│      in :  BaseNodeConfig, JSONObject, Collection[str]                       │
│      out:  FlowFormulaResults(values{key:str}, errors{key:FlowFormulaError}) │
│      each distinct key evaluated once · NEVER raises                         │
│                                                                              │
│  get_resolved_formulas(*, config, context_dict)          ◄── WRAPPER 1       │
│      in :  BaseNodeConfig, JSONObject                                        │
│      out:  ResolvedFormulas(sites, values, errors)                           │
│      = find_formula_token_sites → flatten keys → evaluate_config_formulas    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘


                          config + context_dict
                                    │
                     ┌──────────────▼──────────────┐
                     │    get_resolved_formulas    │   WRAPPER 1 (shared)
                     └──────────────┬──────────────┘
                                    │
                        ResolvedFormulas(sites, values, errors)
                                    │
                    ════════════════╪════════════════  ← the ONLY fork
                                    │
        ┌───────────────────────────┴───────────────────────────┐
        │                                                       │
   WRAPPER 2a · execution                             WRAPPER 2b · display
   resolve_config_formula_tokens                      _resolve_config_formulas
        │                                                       │
   if errors: raise first                    text = values | {k: blank_or_ERROR(e)}
        │                                                       │
        ▼                                                       ▼
   substitute_formula_tokens(model, sites, values)   substitute_formula_tokens(model, sites, text)
        │                                                       │
        ▼ substituted config                                    ▼ substituted config
   node executor                                          _render_config
                                                                │
                                                        overlay {field: value}
```

## What each element is doing

Read the drawing against this list — every one of these is load-bearing, not decoration.

| Element | What it buys |
|---|---|
| `┌─ file.py ─ role ───┐` title bar | Names the module **and its boundary**. "mechanics, no evaluation" tells you what the file refuses to do — usually the more useful half. |
| `in :` / `out:` under each function | The reader never scrolls to a signature list. This is the single biggest win over a bulleted function list. |
| A type alias inline (`Site = (path, text, formula_keys)`) | Expands the shape at the point of use, instead of a separate legend. |
| One logic line per function | Forces the essential clause out. Two lines means you haven't decided what matters. |
| `◄── WRAPPER 1` | Marks the structurally important function so the eye lands on it before reading top to bottom. |
| Type written on the wire (`ResolvedFormulas(sites, values, errors)`) | Makes the flow section self-contained — you can read it without the boxes above. |
| `════╪════ ← the ONLY fork` | **The point of the whole drawing.** It is a falsifiable claim: exactly one divergence. If a reviewer knows of a second, the diagram is wrong and they'll say so — which is the diagram earning its keep. |
| `WRAPPER 2a · execution` column heads | Names each branch **and its consumer role**, so the two columns are comparable at a glance. |
| Identical `substitute_formula_tokens(...)` on both branches | Duplication drawn honestly. Both branches call the same function with a different mapping — visible instantly, invisible in prose. |
| Branch B continuing past its terminal (`overlay {field: value}`) | Branches don't have to be symmetric. Draw the real lengths. |

## The one thing to copy above all

The fork line. A two-consumer pipeline has exactly one interesting fact — *where* the consumers
diverge — and every other format buries it. `════╪════  ← the ONLY fork` states it, marks it,
and dares the reader to contradict it.
