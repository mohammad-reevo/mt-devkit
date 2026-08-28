# Reference — mermaid mechanics

How to write, lint, render, and hand over a diagram. The shapes themselves are in
`shapes.md`.

## The loop

```
write  ~/.claude/tmp/<slug>/<name>.md      one ```mermaid fence
lint   phantom nodes, subgraph/end balance
render npx -y -p @mermaid-js/mermaid-cli mmdc -i <file>.md -o <out>.md
hand   print the SVG path — never open it
```

`mmdc` prints `Found N mermaid charts` and writes one SVG per chart, named `<out>-N.svg`.
Rename it to match the diagram before handing it over.

**Exit 0 with an SVG means the syntax is proven good.** That matters more than it sounds: without
it, "it isn't rendering" is unfalsifiable from your side and the instinct is to start editing
valid mermaid. Render first, then blame the viewer.

`timeout` does not exist on macOS — don't wrap the command in it, or you get a silent exit 0 and
no render. First run downloads Chromium (~1 min); subsequent runs are fast.

## Where it renders, if I ask

| Target | Needs |
|---|---|
| `.svg` in VS Code | nothing — built-in image preview |
| GitHub PR description / issue | nothing — renders the fence natively |
| VS Code markdown preview | `bierner.markdown-mermaid` |

If the markdown preview doesn't work but `mmdc` rendered fine, it's the editor: Restricted Mode
disables extensions, and a preview opened before an extension was installed needs a window
reload. The `.svg` sidesteps both.

## Syntax traps

None of these error loudly. All are verified against `mmdc`.

- **`{{` opens a hexagon node.** A literal `{{template}}` in a label kills the diagram. Same
  family: `((` circle, `[[` subroutine, `>` asymmetric. Describe the braces in words. A *single*
  `{curly}` inside a quoted label is fine.
- **`->` and `=>` are eaten** in label text — they vanish from the rendered output. Use `→`.
- **Quote every label** — `A["text"]`. Unquoted labels break on `(`, `:`, `,`.
- **`<br/>` is the only HTML to rely on.** `<b>` / `<i>` depend on `htmlLabels` and can render as
  literal tags.
- **A typo'd node id creates a blank phantom node**, silently. It never errors.
- **`classDef` must set `fill` AND `color`.** Fill-only is unreadable in the opposite editor
  theme, and the theme belongs to the viewer.

**Verified safe inside a quoted label** — these all render intact, so contracts can be written
naturally: `list[str]`, `dict[str, int]`, `str | None`, `tuple[A, B]`, `Result(config, changed)`,
`{curly}`, `"quoted"`, `50%`, `#`, `:`, `;`, `,`.

## Palette that survives both themes

```
classDef newfile   fill:#dcfce7,stroke:#16a34a,color:#14532d
classDef changed   fill:#fef3c7,stroke:#d97706,color:#78350f
classDef unchanged fill:#f1f5f9,stroke:#94a3b8,color:#334155
classDef forknode  fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
classDef caution   fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
```

Explicit `color:` on every class is what makes these theme-independent.

## Change-status diagrams

Whenever the diagram explains a **change** — a plan, a PR, a refactor — colour answers one
question only: *what is this change touching?* The first four classes above are that key.
`caution` is for the one genuinely risky node and is used sparingly or not at all.

**Do not mix axes.** A key of *new / untouched / shared / risky* is three questions wearing one
coat: "shared" is about topology, "risky" is about judgement, and only "new"/"untouched" answer
the change question. The reader cannot tell which question a given colour is answering, so the
whole palette stops carrying information. Topology and risk belong in the **label**.

Four labelling rules do the work colour can't. Each exists because leaving it out produced a
diagram that had to be redrawn:

- **Name the file and what it gains.** `FieldDescriptorFormRenderer.tsx · CHANGED` is half an
  answer; `· CHANGED — PURE WIRING, forwards 2 props to 6 call sites` is the whole one.
- **Mark pure wiring as pure wiring.** The file with the largest diff is often the one with no
  logic in it. Unmarked, it's where a reviewer starts reading.
- **Draw the node where the new thing actually appears**, even when it is an unremarkable
  existing component. Omitting it hides the answer to "so where does the user see this?" — the
  question the diagram was drawn to answer.
- **Annotate reachability on the new arm.** `only reachable once a token exists` states the
  safety property in three words: existing inputs still take the old path, so nothing can regress.
  That claim is usually the reason the change is safe, and it is invisible in topology alone.

The key still goes in the walkthrough — the SVG has no legend.

## Lint

Catches phantom nodes and unbalanced subgraphs before you spend a render on them.

```python
import re

m = re.search(r"```mermaid\n(.*?)\n```", open(PATH).read(), re.S).group(1)
defined = set(re.findall(r"^\s*([A-Za-z][A-Za-z0-9]*)\[", m, re.M))
sources = set(re.findall(r"^\s*([A-Za-z][A-Za-z0-9]*)\s*--", m, re.M))
targets = set(re.findall(r"-->(?:\|[^|]*\|)?\s*([A-Za-z][A-Za-z0-9]*)", m))
classed = {n for g in re.findall(r"^\s*class\s+(\S+)\s+\w+", m, re.M) for n in g.split(",")}

print("edge endpoints missing:", sorted((sources | targets) - defined))
print("classed missing:", sorted(classed - defined))
print("subgraph:", len(re.findall(r"^\s*subgraph\b", m, re.M)),
      "end:", len(re.findall(r"^\s*end\s*$", m, re.M)))
print("stray braces:", [i + 1 for i, l in enumerate(m.split("\n")) if "{{" in l])
```

The lint proves the ids line up. It does not prove mermaid accepts the file — only `mmdc` does
that, so always do both.

## What auto-layout costs you

Mermaid places nodes; you don't. Two consequences, both permanent:

- **No notion of depth.** Two calls at different depths of one traversal render as siblings.
- **No margins.** Anything that isn't a node — a cross-reference, a count, "these deleted lines
  are re-indentation" — has nowhere to live.

Neither is a reason to avoid a shape. Both are reasons the walkthrough carries the sentences the
picture can't. See SKILL.md → *The reply contract*.
