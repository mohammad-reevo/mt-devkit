---
name: standalone-implement-subagent
title: A generic implement subagent for changes outside the full mt-workflow funnel
target: personal-claude
created: 2026-07-07
source: mt-* harness discussion (Wave 2 sweep session)
---

## Problem
The funnel (mt-scope → … → mt-done) is the heavyweight path. Some changes don't warrant it:
a tweak **after the PR is already ready**, or a **mini-PR** too small for the full workflow. No
sanctioned lightweight path exists for those today.

## Why it matters
Reaching for the whole funnel (scope + plan + worktree + review + verify) to make a two-line
follow-up is friction. A quick standalone build path keeps small changes fast without abandoning
the subagent-delegation discipline (raw code / check output stays out of main context).

## Fix ideas
- This might just be **mt-implement's per-task subagent, re-used standalone** — dispatch one
  general-purpose subagent to make the change + run checks + report, without the plan-file /
  worktree-creation / code-review scaffolding around it.
- Decide: a thin new skill (`mt-quick`?) vs. a documented "invoke the implement subagent directly"
  convention vs. a flag on mt-implement for the no-plan case.
- Figure out how it interacts with an existing worktree/branch vs. a post-PR tweak on a branch
  that's already checked out.

## Links
- [[my-devkit-design]] — funnel; this is the lightweight escape hatch beside it.
- Skill: `~/.claude/skills/mt-implement/` (the subagent to potentially re-use).
