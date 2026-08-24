---
name: make-diagram
description: Draw a design, a plan, or a change as an ASCII diagram that shows the real mechanism — module boxes carrying each function's in/out contract, the data flowing top-to-bottom, and an explicit marked line wherever a shared path forks per consumer. ASCII by default, because the output has to survive a plan file, a PR description, and a terminal with no rendering step; mermaid only when I ask for it by name. Ships one shape today (pipeline-with-a-fork) and is built to grow more. Also owns the call on when NOT to draw one. Standalone, and reached for by `plan`. Triggers on "draw this", "diagram this", "visualize the design", "show me the structure", "/make-diagram".
argument-hint: '[what to draw]'
---

> Personal rebuild — self-contained, no devkit dependency.
> Standalone tool, also reached for by **plan** when a design's shape warrants one
> (see `~/.claude/spec/my-devkit-design.md`).

# make-diagram — draw the mechanism, not the vibe

You turn a design, a plan, or a change into an **ASCII diagram of how the thing actually
works**: module boxes carrying each function's input/output contract, the data flowing
top-to-bottom, and an explicit marked line wherever a shared path forks per consumer.

Where make-diagram ends: **a diagram, in the conversation.** You don't write it to a file, you
don't edit code, and you don't decide where it goes — the caller does.

## Why ASCII

Default to ASCII, always. The output has to survive a plan file, a PR description, a terminal,
and a markdown code fence with no rendering step in between. Mermaid is live in an Artifact and
dead text everywhere this skill's output actually lands. Emit mermaid **only when I ask for it
by name** — and then give me the ASCII too, unless I say not to.

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

One shape ships today. **Read `references/pipeline-fork.md` before drawing your first one** — it
carries the full worked example this grammar was derived from. The rules below are the summary.

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

## Growing the skill

One shape ships today. When a design needs a shape this grammar can't hold — a state machine, a
layered architecture, a sequence across services — **add it here as its own section with its own
worked example**. Don't stretch the pipeline grammar over a shape it doesn't fit; a bent grammar
reads worse than no diagram at all.

## Guardrails

- **Render, don't route.** Output the diagram in the conversation. Writing it into a plan file, a
  PR description, or an eng doc is the caller's call, never a side effect of drawing.
- **Never edit code**, and never fix something you noticed while tracing the flow. Surface it in
  a line under the diagram instead.
- **Refusing to draw is a real answer.** See the "Don't draw when" list — use it.
- **Check every contract line against the actual signature.** An unverified `out:` is a lie the
  reader will act on.
