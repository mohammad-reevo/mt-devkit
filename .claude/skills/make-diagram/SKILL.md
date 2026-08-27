---
name: make-diagram
description: Draw a design, a plan, or a change as an ASCII diagram that shows the real mechanism — module boxes carrying each function's in/out contract, the data flowing top-to-bottom, and an explicit marked line wherever a shared path forks per consumer. ASCII by default, because it needs no renderer and holds detail auto-layout drops; mermaid when I ask for it by name, which renders in VS Code's markdown preview and natively in GitHub PR bodies. Ships two shapes (pipeline-with-a-fork, call-chain-spine) and is built to grow more. Also owns the call on when NOT to draw one. Standalone, and reached for by `plan`. Triggers on "draw this", "diagram this", "visualize the design", "show me the structure", "/make-diagram".
argument-hint: '[what to draw]'
---

> Personal rebuild — self-contained, no devkit dependency.
> Standalone tool, also reached for by **plan** when a design's shape warrants one
> (see `~/.claude/spec/my-devkit-design.md`).

# make-diagram — draw the mechanism, not the vibe

You turn a design, a plan, or a change into an **ASCII diagram of how the thing actually
works**: module boxes carrying each function's input/output contract, the data flowing
top-to-bottom, and an explicit marked line wherever a shared path forks per consumer.

Where make-diagram ends: **a diagram, in the conversation.** You don't edit code, and you don't
decide where it goes — the caller does. The one file you may write is a scratch file under
`~/.claude/tmp/<slug>/`: to measure the geometry, and to carry a mermaid version somewhere VS
Code can render it. That is a workbench, not a destination.

## Why ASCII

Default to ASCII, always. The output has to survive a plan file, a PR description, a terminal,
and a markdown code fence with no rendering step in between — and the terminal is where I read
it first. Emit mermaid **only when I ask for it by name** — and then give me the ASCII too,
unless I say not to.

**Don't defend that default by claiming mermaid renders nowhere.** It renders in two of the
places this skill's output actually lands: **GitHub natively** (PR descriptions, issues) and
**VS Code's markdown preview** via `bierner.markdown-mermaid`. ASCII leads because it needs no
renderer at all and because auto-layout throws away detail a hand-drawn spine keeps — not
because mermaid is dead text. See "Mermaid, when I ask for it" below.

Render inside a bare code fence with **no language tag**. A language tag invites syntax
highlighting, and highlighting mangles box-drawing characters.

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

## The grammar — pipeline with a fork

Two shapes ship today; this is the one for **"where do the consumers diverge"**. **Read
`references/pipeline-fork.md` before drawing your first one** — it carries the full worked
example this grammar was derived from. The rules below are the summary.

### Module boxes — when the design spans files

```
┌─ file.py ─ one-line role, no evaluation ─────────────────────────────────────┐
│                                                                              │
│  function_name(*, arg, other_arg)                                            │
│      in :  ArgType, OtherType                                                │
│      out:  ReturnType      TypeAlias = (field, field, field)                 │
│      one line of what it does · a second clause after a middot               │
│                                                                              │
│  other_function(*, model, sites)                         ◄── CALLOUT         │
│      in :  BaseModel, list[Site]                                             │
│      out:  Result(config, changed)                                           │
│      what it does AT its path · no re-search                                 │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

- The title bar names the **file** and its **one-line role**. The role is often what the file
  does *not* do ("mechanics, no evaluation") — that's the boundary being drawn.
- Per function: signature, then `in :` / `out:`, then **one** line of logic. Not two.
- `◄── CALLOUT` marks the functions that matter structurally (a shared wrapper, the entry point).
- One box per file. Every box the same width.

### The flow — always

```
                          config + context_dict
                                    │
                     ┌──────────────▼──────────────┐
                     │      shared_entry_point     │   WRAPPER 1 (shared)
                     └──────────────┬──────────────┘
                                    │
                        ResolvedThing(a, b, c)
                                    │
                    ════════════════╪════════════════  ← the ONLY fork
                                    │
        ┌───────────────────────────┴───────────────────────────┐
        │                                                       │
   BRANCH A · execution                                BRANCH B · display
   consumer_side_a                                     consumer_side_b
        │                                                       │
        ▼                                                       ▼
   terminal_a                                          terminal_b
```

- **Start with the inputs**, unboxed and centered, above the first step.
- **Write the type on the wire.** The value carried between two steps goes on the `│` between
  them. This is what makes the flow readable without scrolling back up to the boxes.
- **The fork line is the payload.** `════╪════  ← the ONLY fork` asserts something falsifiable.
  If there are two forks, mark both and say two — don't quietly draw one.
- **Below the fork, aligned columns**, each headed by its consumer's name and role
  (`BRANCH A · execution`).
- ` · ` is the inline separator within a logic line.

### Rules that keep it honest

- **The contract lines are not optional.** `in :` / `out:` is the whole reason this beats a
  bulleted function list. A box with only a name is a flowchart, and flowcharts are decoration.
- **Draw what's real, not what's tidy.** If two branches duplicate a step, draw the duplication —
  that's the diagram doing its job. Don't smooth it into a shared box that isn't in the code.
- **Label the fork with what forks**, not merely that it forks.
- **No invented steps.** Diagram only what the source states. A gap in the design shows up as a
  gap in the diagram — say so in a line underneath rather than filling it in.

### Width

Cap the flow at **80 columns**; module boxes may run to **100**. Every box in one diagram is the
same width — ragged widths read as sloppy and break the column alignment below the fork. Nothing
may wrap: a wrapped line inside a code fence destroys the drawing, so measure before committing.

**Measure characters, not bytes.** `awk '{ print length($0) }'` counts BYTES, and every
box-drawing character (`│ ┌ ─ ▼ ►`) is three bytes in UTF-8 — a clean 78-column line reports as
143, and you will "fix" a drawing that was never broken. Write the diagram to a file under
`~/.claude/tmp/<slug>/` and measure it there:

```python
p = "<path>"
for i, l in enumerate(open(p), 1):
    n = len(l.rstrip("\n"))
    if n > 78:
        print(i, n)
```

**Verify any vertical rail lands in ONE column.** Hand-counting a rail that runs past a block
drifts by one and the drawing looks broken. Print the column index of every `│ ┐ ┤ ▼` on the
rail lines and confirm they're all equal *before* showing it — off-by-ones are invisible while
you're writing and glaring once rendered.

## The grammar — call-chain spine

The second shape, for **"what calls what, across all these files, in order"** — a PR
walkthrough, or tracing an entry point down to its leaf. Pipeline-with-a-fork answers *where do
consumers diverge*; this answers *what is the sequence, and which file owns each step*. **Read
`references/call-chain-spine.md` before drawing your first one.**

```
SECTION ── file.py :LINE ─────────────────────────────────────────────────────

  function(args) -> ReturnType                                    NEW  [+27]
        │
        │  one line of what happens here
        │  a second line only when it changes a decision
        ▼
  next_file.py                                              NEW FILE  [+98]
  next_function(args)
```

- **Section headers name the phase AND the file:line** — `SURFACE B ── node_service.py :310`.
  The phase is the reader's spine; the `file:line` is what makes it checkable.
- **Annotate every file with its diff stat** — `[+27]`, `[+108/-14]`, `NEW FILE`. This is what
  turns a call chain into a PR explanation: it says where the change actually *is*, and it
  exposes the files that are pure wiring.
- **Call out lines that are re-indentation, not change.** A `-40` that is really the old code
  moved into an `else:` will otherwise dominate the reader's sense of the diff — say so on the
  branch it belongs to.
- **An unchanged branch says it is unchanged**, in the drawing: `^ untouched, today's behaviour`.
- **When one call travels past a later section**, carry it on a rail in a fixed right-hand
  column and merge with `┤`. Break the intervening section headers around the rail rather than
  overwriting it. Verify the column per **Width** above.
- **Entry points are plural more often than you expect.** If two callers reach the same spine
  and only one of them sets some state, draw both and label the difference — that asymmetry is
  usually the most load-bearing thing on the page.

## Growing the skill

Two shapes ship today. When a design needs a shape neither grammar can hold — a state machine, a
layered architecture, a sequence across services — **add it here as its own section with its own
worked example**. Don't stretch an existing grammar over a shape it doesn't fit; a bent grammar
reads worse than no diagram at all.

## Mermaid, when I ask for it

**Where it renders** — the whole reason it's worth emitting:

- **GitHub, natively.** A mermaid fence in a PR description renders for reviewers.
- **VS Code**, via `bierner.markdown-mermaid`. Write the `.md`, then `code <path>` to open it;
  ⌘⇧V previews, ⌘K V side-by-side. Confirm the extension is installed
  (`code --list-extensions`) rather than assuming — if it isn't, say so instead of shipping a
  file that renders as raw text.
- **Not an Artifact.** An artifact is a browser-hosted claude.ai page, not an in-editor render.
  Don't reach for one just to make a diagram pretty.

Write it to `~/.claude/tmp/<slug>/<name>.md` (per `scratch-files.md`) with the ASCII in the same
file underneath, so one path carries both.

**Syntax traps that break the parse silently** — full list, worked example, and a lint script in
`references/mermaid.md`:

- **`{{` is hexagon-node syntax.** A literal `{{template}}` in a label breaks the whole diagram.
  Same family: `((`, `[[`, `>`. Describe the braces in words instead of showing them.
- **Quote every label** — `A["text"]`, always. Unquoted labels break on `(`, `:`, `,`.
- **`<br/>` for line breaks, and no other HTML.** `<b>`/`<i>` depend on `htmlLabels` and can
  render as literal tags.
- **`classDef` must set `fill` AND `color`.** Fill-only is unreadable in the opposite VS Code
  theme, and the theme belongs to the viewer, not to you.

**Lint before you show it.** A typo'd node id doesn't error — mermaid silently creates a blank
phantom node. Check that every edge endpoint and every `class` target is a defined node, and
that `subgraph` and `end` counts match.

**Then actually render it, don't just lint it.** A structural lint proves the ids line up, not
that mermaid accepts the file — and "it doesn't render" is otherwise unfalsifiable from your
side, so you end up guessing at syntax while the real fault is in the editor:

```
npx -y -p @mermaid-js/mermaid-cli mmdc -i <file>.md -o <out>.md
```

It prints `Found N mermaid charts` and writes one SVG per chart. Exit 0 with an SVG means the
syntax is **proven** good — so if it still isn't rendering for me, stop editing the diagram and
look at VS Code (Restricted Mode disables the extension; a preview opened before the extension
activated needs a window reload).

**The SVG it produces is the zero-dependency fallback.** VS Code previews `.svg` natively — no
extension, no workspace trust. When the markdown preview is being difficult, hand me the SVG and
move on. (`timeout` doesn't exist on macOS — don't wrap the command in it.)

**Say what mermaid lost.** Auto-layout has no notion of depth: two calls at different depths of
one traversal come out as siblings. When that relationship IS the payload, ship the ASCII
alongside and name what the rendered version flattened.

## Guardrails

- **Render, don't route.** Output the diagram in the conversation. Writing it into a plan file, a
  PR description, or an eng doc is the caller's call, never a side effect of drawing. A scratch
  file under `~/.claude/tmp/<slug>/` is not routing — it's the workbench for measuring geometry
  and for the mermaid version. Anywhere someone else would read it needs my say-so.
- **Never edit code**, and never fix something you noticed while tracing the flow. Surface it in
  a line under the diagram instead.
- **Refusing to draw is a real answer.** See the "Don't draw when" list — use it.
- **Check every contract line against the actual signature.** An unverified `out:` is a lie the
  reader will act on.
