# Explaining a PR: files in reading order, then a diagram

## When to Apply
Any time you explain a change to me **outside a review's own report** — "explain the PR real
quick" mid-`babysit`, a walkthrough during `verify` or `workflow`, or a plain conversational ask
about a branch or a diff. `pr-review`'s § 1 is this same shape; it cites this file rather than
restating it, so the two can't drift.

## The Rule

An explanation orients me to **navigate the diff**, not to admire the design. Three parts, in
order:

1. **Two to four sentences** — what the change does and why it exists.
2. **The files that carry it, in reading order**, each with the role it plays. Not the
   changed-file list — the ones I'd actually open, in the order I'd open them.
3. **A simple arrow diagram** of how they build on each other — call or data flow, **3–6 nodes**,
   one clause each:

```
edit_planner.py (planner input + serialized conditions)
   → orchestrator.py (wiring, plan build)
   → switch_case_ordering.py (subsumption prover)
```

**Skip the diagram entirely for a one- or two-file diff** — a diagram of two boxes is noise, and
a manufactured one is worse.

**Keep it inline and cheap.** Derive it from `git diff --stat`, the PR title/body, and what you
already know. Don't read files wholesale to build it, and **don't spawn an agent for it**. The
diagram is the ASCII sketch above, not the `make-diagram` skill — that renders SVG and is a
heavier tool than a three-line orientation sketch warrants.

## Why
Parts 2 and 3 are exactly the ones an improvised explanation drops, and they're the ones that do
the work. A description of the design in the abstract reads fine and helps less when I'm about to
open the Files tab: reading order says where to start, and the diagram says how the pieces chain.
Both are nearly free — they fall out of `--stat` and the title.

This applies across all repositories and projects.
