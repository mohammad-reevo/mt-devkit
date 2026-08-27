---
name: make-diagram
description: Draw a design, a plan, or a change as a mermaid diagram that shows the real mechanism — nodes carrying each function's in/out contract, the data flowing top-to-bottom, and an explicit marked point wherever a shared path forks per consumer. Renders the diagram to SVG and hands back the path plus a short walkthrough that stands on its own; never opens a file. Ships two shapes (pipeline-with-a-fork, call-chain-spine) and is built to grow more. Also owns the call on when NOT to draw one. Standalone, and reached for by `plan`. Triggers on "draw this", "diagram this", "visualize the design", "show me the structure", "/make-diagram".
argument-hint: '[what to draw]'
---

> Personal rebuild — self-contained, no devkit dependency.
> Standalone tool, also reached for by **plan** when a design's shape warrants one
> (see `~/.claude/spec/my-devkit-design.md`).

# make-diagram — draw the mechanism, not the vibe

You turn a design, a plan, or a change into a **mermaid diagram of how the thing actually
works**: nodes carrying each function's input/output contract, the data flowing top-to-bottom,
and an explicit marked point wherever a shared path forks per consumer.

Where make-diagram ends: **a rendered SVG, its path, and a walkthrough in the conversation.**
You don't edit code, you don't open the file, and you don't decide where the diagram goes —
the caller does.

## First — decide whether to draw at all

A weak diagram is worse than the sentence it replaced. **"This doesn't need a diagram" is a
valid outcome of invoking this skill** — say it plainly and stop, rather than producing
something decorative to justify the call.

**Draw when:**
- **Two or more consumers share a path.** Where they diverge is the single most important fact
  about the design, and prose buries it. This is the case the skill was built for.
- **Three or more steps chain**, each step's output being the next one's input.
- **You suspect duplication but can't point at it.** Two branches drawn side by side either come
  out identical or they don't — the drawing settles it.
- **The open question is "which module owns what".**

**Don't draw when:**
- Fewer than ~3 steps — a sentence wins.
- One consumer, one straight line, no fork — a sentence wins.
- It's a *list*, not a flow ("these five files each get a field added") — a list wins.

The test: if the drawing would show no fork, no contract, and no shared step, it's decoration.

## Resolve what you're drawing

The input is whatever the caller has: a design we just talked through, a plan file
(`~/.claude/spec/<slug>-plan.md`), a branch or PR diff, or a code path in the repo. Work out
which from the invocation; ask only if it's genuinely ambiguous.

**Read the source before drawing — never draw from memory of the conversation.** A diagram
asserts things: *this* returns *that*, these two branches share *this* step, there is exactly
one fork. Every assertion is falsifiable, which is precisely why the diagram beats prose — so
check each one against the real signatures. A diagram with a wrong contract line is worse than
no diagram, because it will be believed.

## How to draw — mermaid, always

1. **Write** the diagram to `~/.claude/tmp/<slug>/<name>.md` (per `scratch-files.md`), as a
   single ```mermaid fence.
2. **Lint** it — a typo'd node id never errors, it silently makes a blank phantom node.
3. **Render** it, which is the only real proof the syntax is good:

   ```
   npx -y -p @mermaid-js/mermaid-cli mmdc -i <file>.md -o <out>.md
   ```

   Prints `Found N mermaid charts` and writes one SVG per chart. Rename the SVG to match the
   diagram. (`timeout` does not exist on macOS — don't wrap the command in it, or you get a
   silent exit 0 and no render.)
4. **Hand back the SVG path.** Never run `code`, `open`, or anything else that opens it — where
   the diagram gets looked at is my call, not a side effect of drawing.

If `mmdc` exits 0 with an SVG, the syntax is **proven** good. If it still won't display, stop
editing the diagram and look at the viewer — VS Code's Restricted Mode disables extensions, and
`.svg` previews natively with no extension at all.

The lint script, the full syntax-trap list, and the theme-independent palette live in
`references/mermaid.md`. **Read it before your first diagram.** The four that bite hardest:

- **`{{` opens a hexagon node** — a literal `{{template}}` in a label kills the whole diagram.
  Same family: `((`, `[[`, `>`. Describe the braces in words.
- **`->` and `=>` are eaten** in label text. Use `→`. (Type signatures are safe: `list[str]`,
  `dict[str, int]`, `str | None` and `Result(a, b)` all render intact inside a quoted label.)
- **Quote every label** — `A["text"]`, always.
- **`classDef` must set `fill` AND `color`** — fill-only is unreadable in the opposite editor
  theme, and the theme belongs to the viewer.

## The reply contract

The diagram is a file; the **reply** is what I actually read first. It must stand on its own.

- **Lead with the path** to the rendered SVG, so it's there when I want it.
- **Then three to five lines of walkthrough** — what the diagram asserts, and the one decision
  it forces. Not a caption ("this shows the validation flow"), and not a re-narration of every
  node. Each line should be checkable against the code.
- **Name what the layout flattened.** Mermaid's auto-layout has no notion of depth: two calls at
  different depths of one traversal come out as siblings, and anything that isn't a node — a
  margin note, a "these deleted lines are re-indentation" aside — has nowhere to live. When that
  relationship is load-bearing, say it in the walkthrough, because the picture can't.
- **A reader who never opens the SVG should still get the point.** If the walkthrough only makes
  sense next to the picture, it's a caption, not a walkthrough.

`response-altitude.md` governs how much detail belongs in the reply; this section only says the
reply is never *just* a link.

## The shapes

Two ship today. **Read `references/shapes.md` before drawing your first one** — it carries the
full worked example behind each, and the mermaid idiom for it.

### Pipeline with a fork

For **"where do the consumers diverge"**. One shared resolution path, then a single point where
consumers split.

```
flowchart TD
  IN["config + context_dict"]
  W["shared_entry_point(*, config, context)<br/>in : Config, dict<br/>out: ResolvedThing(a, b, c)<br/>one line of what it does"]
  FORK{"the ONE fork<br/>what forks, not that it forks"}
  A["BRANCH A · execution<br/>consumer_side_a(...)"]
  B["BRANCH B · display<br/>consumer_side_b(...)"]
  IN --> W --> FORK
  FORK -->|execution| A
  FORK -->|display| B
```

- **The contract lines are not optional.** `in :` / `out:` inside the node is the whole reason
  this beats a bulleted function list. A node with only a name is a flowchart, and flowcharts
  are decoration.
- **The fork is the payload.** Give it its own `{"..."}` node, label it with *what* forks, and
  state in the walkthrough how many forks there are. If there are two, draw two — never quietly
  draw one.
- **Name each branch with its role**, not just its function: `BRANCH A · execution`.

### Call-chain spine

For **"what calls what, across all these files, in order"** — a PR walkthrough, or tracing an
entry point to its leaf. One `subgraph` per phase, titled with the phase **and** the file:line.

```
flowchart TD
  subgraph S1["ENTRY — graph_topology.py :1165"]
    GT["_perform_node_validation"]
    SVC["NodeValidationService(...)<br/>+25"]
    GT --> SVC
  end
  subgraph S2["SHARED — node_service.py :270"]
    VFT["validate_formula_typed(formula, node_id)<br/>out: list[FormulaError]<br/>NEW"]
  end
  SVC --> VFT
```

- **Section title = phase + `file.py :LINE`.** The phase is the reader's spine; the file:line is
  what makes the claim checkable. Neither works alone.
- **Annotate every file with its diff stat** — `+27`, `+108/-14`, `NEW FILE +98`. This is what
  turns a call chain into a *PR* explanation: it says where the change actually is, and exposes
  which files are pure wiring.
- **Call out lines that are re-indentation, not change**, and **mark unchanged branches as
  unchanged** (the `untouched` class). A flag-gated PR has a whole column that is today's
  behaviour; saying so is what makes the other column readable as *the change*.
- **Entry points are plural more often than you expect.** If two callers reach one spine and
  only one of them sets some state, draw both and label the difference — that asymmetry is
  usually the most load-bearing thing on the page, and it never appears in a diff as a diff.

## Rules that keep it honest

- **Draw what's real, not what's tidy.** If two branches duplicate a step, draw the duplication —
  that's the diagram doing its job. Don't smooth it into a shared node that isn't in the code.
- **No invented steps.** Diagram only what the source states. A gap in the design shows up as a
  gap in the diagram — say so in the walkthrough rather than filling it in.
- **Colour carries the argument or it isn't used.** Give each class a meaning (new / untouched /
  shared / the one risky bit) and state the key in the walkthrough. Decorative colour is noise.

## Growing the skill

Two shapes ship today. When a design needs a shape neither grammar can hold — a state machine, a
layered architecture, a sequence across services — **add it here as its own section with its own
worked example** in `references/shapes.md`. Don't stretch an existing grammar over a shape it
doesn't fit; a bent grammar reads worse than no diagram at all.

## Guardrails

- **Render, don't route.** Hand back the SVG path. Writing the diagram into a plan file, a PR
  description, or an eng doc is the caller's call, never a side effect of drawing. The scratch
  file under `~/.claude/tmp/<slug>/` is a workbench, not a destination.
- **Never open the file.** No `code`, no `open`. Give me the path.
- **Never edit code**, and never fix something you noticed while tracing the flow. Surface it in
  the walkthrough instead.
- **Refusing to draw is a real answer.** See the "Don't draw when" list — use it.
- **Check every contract line against the actual signature.** An unverified `out:` is a lie the
  reader will act on.
