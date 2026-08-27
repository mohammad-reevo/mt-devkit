# Reference — mermaid, when I ask for it

ASCII is still the default (SKILL.md → "Why ASCII"). This file is the how, for when I've asked
for a rendered version by name.

## Where it renders

| Target | Needs | Notes |
|---|---|---|
| GitHub PR description / issue | nothing | renders natively — the highest-value target |
| VS Code markdown preview | `bierner.markdown-mermaid` | ⌘⇧V preview, ⌘K V side-by-side |
| VS Code, `.svg` file | nothing | built-in image preview; the fallback that always works |
| Artifact | — | a browser-hosted claude.ai page, **not** an in-editor render |

Confirm the extension before promising the preview:

```
code --list-extensions | grep -i mermaid
```

Write the `.md` under `~/.claude/tmp/<slug>/` (per `scratch-files.md`), put the ASCII in the
same file underneath, then `code <path>` to open it.

## Syntax traps

Each of these breaks the parse or the reading, and none of them errors loudly.

- **`{{` opens a hexagon node.** A literal `{{template}}` inside a label kills the diagram.
  Same family: `((` (circle), `[[` (subroutine), `>` (asymmetric). Describe the braces in
  words — "every reference becomes the literal 0" — rather than showing them.
- **Quote every label.** `A["text"]`. Unquoted labels break on `(`, `:`, `,`.
- **`<br/>` is the only HTML to rely on.** `<b>` / `<i>` depend on `htmlLabels` and can render
  as literal tags.
- **`classDef` must set `fill` AND `color`.** Fill-only is unreadable in the opposite VS Code
  theme, and the theme belongs to the viewer.
- **A typo'd node id creates a blank phantom node**, silently. It never errors.

## Palette that survives both themes

```
classDef newcode   fill:#dcfce7,stroke:#16a34a,color:#14532d
classDef untouched fill:#f1f5f9,stroke:#94a3b8,color:#334155
classDef flagnode  fill:#fef3c7,stroke:#d97706,color:#78350f
classDef shared    fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
classDef caution   fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
```

Explicit `color:` on every class is what makes these theme-independent. Give the colours a
*meaning* and state it in a key under the diagram — on a PR walkthrough, "new / untouched /
shared / the one risky bit" is most of the argument.

## Lint, then render

**Lint** — catches phantom nodes and unbalanced subgraphs:

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

**Render** — the lint proves the ids line up, not that mermaid accepts the file:

```
npx -y -p @mermaid-js/mermaid-cli mmdc -i <file>.md -o <out>.md
```

Prints `Found N mermaid charts` and writes one SVG per chart. **Exit 0 with an SVG means the
syntax is proven good** — so if it still isn't rendering in the editor, stop editing the diagram
and look at VS Code: Restricted Mode disables extensions, and a preview opened before the
extension activated needs a window reload. Hand over the SVG in the meantime; it needs nothing.

`timeout` does not exist on macOS — don't wrap the command in it, or you get a silent exit 0
and no render.

## Say what mermaid lost

Auto-layout has no notion of depth. Two calls at different depths of one traversal come out as
siblings, and any annotation that isn't a node (diff stats, "these deleted lines are
re-indentation", a rail travelling past a block) has nowhere to live. When that relationship is
the payload, ship the ASCII alongside and name what the rendered version flattened.
