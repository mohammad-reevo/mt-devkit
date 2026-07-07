---
name: protect-worktree-env-secrets
title: Harden .env secret handling so worktree/env ops never leak API keys
target: personal-claude
created: 2026-07-06
source: mt-* funnel build session (deferred workflow task #21)
---

## Problem
mt-worktree copies each sub-repo's `.env`/`.env.local`/`.env.test` (incl. the nested frontend
`apps/reevo-webapp/.env`) into every worktree, and env-manager re-applies a `REEVO_BACKEND_PATH`
sed on frontend run. The path rewrite is already line-scoped so secrets aren't read into context
— but the broader secret-handling posture isn't audited: full secret-laden `.env`s get duplicated
into every worktree, and nothing verifies they stay out of context / commits / logs / PRs.

## Why it matters
API keys and secrets live in these `.env`s. Duplicating them widely and handling them in
skills/scripts is a leakage surface — into Claude context, an accidental commit, a log, or a PR
body. A single leaked prod/dev key is costly.

## Fix ideas
- Verify `.env*` is gitignored in every worktree sub-repo (so it can't be committed).
- Confirm no skill/script ever `cat`s a full `.env` into context (only line-scoped sed) — add a
  guard/convention if needed.
- Decide whether copying the full secret-laden `.env` into every worktree is acceptable, or
  whether it should be scoped/scrubbed (copy only non-secret keys + reference a shared secrets
  source) or symlinked to a single gitignored source.
- Consider a scrub/redaction step if a `.env` ever must be surfaced.
- **A personal edit-guard hook** (from the Wave 2b sweep — devkit's `edit_guard_hook.py`): a
  PreToolUse:Edit/Write hook that blocks the agent from editing (and reading full) `.env` files —
  devkit's version denies `.env` edits + sub-repo `.claude` edits and enforces cwd=root. This is
  the enforcement layer for "no skill/script reads a full `.env` into context." Rebuild only the
  `.env`-protection slice (self-contained, py3.9-safe like `worktree_gate_hook.py`); the rest of
  devkit's edit-guard (cwd/`.runs` snapshot protection) is devkit-workflow-specific — skip.
  Decide at execute time: is a hook worth it, or does the gitignore + no-`cat` convention suffice?

## Links
- [[worktree-full-create]] — sibling worktree/.env-seeding task.
- Skills: `~/.claude/skills/mt-worktree/`, `~/.claude/skills/env-manager/`.
- Design doc: `~/.claude/spec/my-devkit-design.md` (build log; this was funnel task #21).
