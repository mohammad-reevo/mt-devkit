---
name: mt-implement-review-ast-checks
title: Fold devkit code-reviewer's structural AST check-intents into mt-implement's review
target: personal-claude
created: 2026-07-07
source: Wave 5 holistic devkit review (my-devkit-design.md)
---

## Problem
Devkit's `code-reviewer` plugin ships a custom AST lint engine with structural rules R001–R006:
paired-mapping-dicts, paired-model-columns, stringly-typed-enums, repeated-literal-sets,
near-duplicate-functions, silent-substitute-except. `mt-implement`'s final code-review subagent is
a general-purpose reviewer against repo conventions + quality — it does NOT specifically hunt for
these structural patterns.

## Why it matters
These are non-obvious, high-value structural checks (single-source-of-truth violations,
stringly-typed enums, silent fallbacks). Folding the *intent* of them into mt-implement's review
prompt raises review quality without any plugin/engine dependency.

## Fix ideas
- **Don't rebuild the AST engine** (`lint/run.py` + rules). Instead, enrich `mt-implement`'s
  code-review subagent prompt with the check *intents* — e.g. "flag paired dicts / model columns
  that must stay in sync, stringly-typed enums, repeated literal sets, near-duplicate functions,
  and silent try/except substitutions."
- **silent-substitute-except is already covered** by the copied `defensive-defaults.md` rule — the
  reviewer will catch it via that rule; no need to duplicate.
- Keep it a prompt enrichment, not a new gate (guidance over gates).

## Links
- [[my-devkit-design]] Wave 5 — code-reviewer AST rules (MAYBE → deferred here).
- Skill: `~/.claude/skills/mt-implement/` (the review subagent to enrich).
