# The shape of a PR explanation — files in reading order, then a diagram

Shared prose, read by the `pr-explanation` skill (which produces one on its own) and by
`pr-review` § Report → § 1 (which opens its review report with the same thing). One home, so a
review's orientation and an ad-hoc explanation can't drift apart.

An explanation orients the reader to **navigate the diff**, not to admire the design. Three
parts, in order:

1. **Two to four sentences** — what the change does and why it exists.
2. **The files that carry it, in reading order**, each with the role it plays. Not the
   changed-file list — the ones the reader would actually open, in the order they'd open them.
3. **A simple arrow diagram** of how they build on each other — call or data flow, **3–6 nodes**,
   one clause each:

```
edit_planner.py (planner input + serialized conditions)
   → orchestrator.py (wiring, plan build)
   → switch_case_ordering.py (subsumption prover)
```

Only files in the diff. **Skip the diagram entirely for a one- or two-file diff** — a diagram of
two boxes is noise, and a manufactured one is worse.

**Keep it inline and cheap.** Derive it from `git diff --stat`, the PR title/body, and what you
already know. Don't read files wholesale to build it, and **don't spawn an agent for it**. The
diagram is the ASCII sketch above, not the `make-diagram` skill — that renders SVG and is a
heavier tool than a three-line orientation sketch warrants.

## Why parts 2 and 3

They're the two an improvised explanation drops, and the two that do the work. A description of
the design in the abstract reads fine and helps less when the reader is about to open the Files
tab: reading order says where to start, and the diagram says how the pieces chain. Both are
nearly free — they fall out of `--stat` and the title.
