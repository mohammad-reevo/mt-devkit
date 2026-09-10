---
name: pr-explanation
description: Explain a PR, branch, or diff so I can navigate it — two to four sentences on what it does and why, then the files that carry it in reading order with each one's role, then a 3–6 node arrow diagram of how they chain. Orientation only: it never reviews, never finds, never posts. Derived cheaply from `git diff --stat` and the PR title/body — no wholesale file reads, no subagents. Runs standalone on my ask, and auto-runs as workflow's verify → babysit handoff. Triggers on "explain the PR", "explain this branch", "what's in this diff", "walk me through the change", "/pr-explanation".
argument-hint: '[PR number, branch, or nothing for the current one]'
---

> Personal rebuild — self-contained, no devkit dependency.
> Standalone tool, and the automatic handoff step in **workflow** between verify and babysit.
> `pr-review` § Report → § 1 opens its report with **§ The shape** below rather than its own copy.

# pr-explanation — orient me to the diff

Not a review. `pr-review` decides what's *wrong*; this decides where to *start reading*. If a
finding surfaces while you're building the explanation, say it in a sentence at the end — don't
grow it into a tiered report, and don't post anything.

## Resolve the target

In order, first that applies:

- **An argument given** — a PR number (`gh pr view <n>`), a branch, or a ref range.
- **A PR open for the current branch** — `gh pr view --json number,title,body,url`. This is the
  workflow case, and the common one.
- **A branch with no PR** — diff it against `origin/main`.
- **Nothing committed** — explain the uncommitted working tree.

If the worktree spans several sub-repos with their own PRs, explain each one, most substantial
first. Say which repo each is.

## Gather — cheaply, and stop

```bash
git diff --stat origin/main...HEAD        # or `gh pr diff <n> --name-only`
```

That plus the PR title/body is nearly always enough. Open a file only when `--stat` and the
title genuinely don't say what a file contributes — and then read that one file, not its
neighbours. **Never spawn an agent for this**: the whole point is that orientation is cheap. If
you find yourself doing real investigation, you've drifted into `pr-review`'s job.

## The shape

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

The diagram is the ASCII sketch above, not the `make-diagram` skill — that renders SVG and is a
heavier tool than a three-line orientation sketch warrants.

**Why parts 2 and 3:** they're the two an improvised explanation drops, and the two that do the
work. A description of the design in the abstract reads fine and helps less when the reader is
about to open the Files tab — reading order says where to start, the diagram says how the pieces
chain. Both are nearly free: they fall out of `--stat` and the title.

## Report

The three parts above, in order, and nothing else: no findings section, no test summary, no
next-steps list. `response-altitude.md` governs how much of it to show.

Then **stop**. Whatever invoked this decides what happens next.
