---
name: branch-from-main-guard-hook
title: Personal branch-from-main guard hook (rebuild devkit acl-hook's "new branches only from an up-to-date main")
target: personal-claude
created: 2026-07-07
source: liked devkit acl-hook's branch guard during the mt-devkit migration
---

## Problem
Devkit's `acl-hook` plugin has a guard I like: it only allows creating a new branch when you're on
`main` and local `main == origin/main` — message *"Create branches only from main — currently on
'<branch>'"*. We're dropping the devkit acl-hook (see [[drop-devkit-acl-hook]]), so this guard goes
with it unless we rebuild it as our own.

## Why it matters
It enforces branching off a fresh `main` — prevents accidentally branching off a stale branch or a
behind `main`. (It fired during the mt-devkit Phase-0→1 transition, which is what surfaced it.)

## Fix ideas
- Build a self-contained personal `PreToolUse:Bash` hook (lands in the **mt-devkit** harness
  `.claude/hooks/`, alongside `worktree_gate_hook.py`) that blocks new-branch creation
  (`git checkout -b`, `git branch <new>`, `git worktree add -b`) unless current branch is `main`
  AND local `main` is up to date with `origin/main`.
- Source to mirror: `~/.claude/plugins/cache/devkit/acl-hook/0.8.0/hooks/acl_hook.py` (the branch
  guard, ~line 257: "Allow new branches only when on main and local main == origin/main").
- **Improve on devkit's version:** also allow an explicit up-to-date start-point
  (`git checkout -b <name> origin/main`, `git worktree add -b <name> ... origin/main`) even when
  the current branch isn't `main` — that legit case is what devkit's guard wrongly blocked in a
  worktree (main lives in the primary checkout, can't be checked out in the worktree).
- py3.9-safe, no devkit dependency; register in the mt-devkit harness settings.

## Links
- [[drop-devkit-acl-hook]] — the plugin this guard currently rides on.
- Lands with the migrated hooks in the mt-devkit harness.
