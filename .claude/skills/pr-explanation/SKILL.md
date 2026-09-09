---
name: pr-explanation
description: Explain a PR, branch, or diff so I can navigate it — two to four sentences on what it does and why, then the files that carry it in reading order with each one's role, then a 3–6 node arrow diagram of how they chain. Orientation only: it never reviews, never finds, never posts. Derived cheaply from `git diff --stat` and the PR title/body — no wholesale file reads, no subagents. Runs standalone on my ask, and auto-runs as workflow's verify → babysit handoff. Triggers on "explain the PR", "explain this branch", "what's in this diff", "walk me through the change", "/pr-explanation".
argument-hint: '[PR number, branch, or nothing for the current one]'
---

> Personal rebuild — self-contained, no devkit dependency.
> Standalone tool, and the automatic handoff step in **workflow** between verify and babysit.

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

## Report

Follow `mt-devkit/.claude/references/pr-explanation-shape.md` exactly — the three parts in
order, the diagram skipped at one or two files. Nothing else: no findings section, no test
summary, no next-steps list. `response-altitude.md` governs how much of it to show.

Then **stop**. Whatever invoked this decides what happens next.
