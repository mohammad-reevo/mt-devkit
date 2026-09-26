# Assimilation Harness (AH) — salestech-be's team overlay

## When to Apply
Any salestech-be work. AH is the team's agent overlay, applied into each worktree's
`salestech-be/` on `worktree create`: `CLAUDE.md`, `.claude/rules/general/`, `.claude/skills/`,
`.claude/lib/`. Never frontend or other repos.

## Rule
AH's rules load on their own once you read salestech-be files; follow them, except where
mt-devkit disagrees — mt-devkit wins. Overridden:
- Agent modes (`partnered` / `agentic` / `investigate`, "per the active mode"): none is
  active; the funnel skills decide how a session behaves.
- Independent review via `agentic-code-review`: use the `reviewer` agent / `pr-review`.
- Tier 3 (e2e skill or builder-agent UI check): only when I ask.
- `pr-slicing.md`, `context-docs.md`, `progress-log.md`: don't apply — no `<project>/base`,
  `.context/`, or `progress.md`.

Everything else stands, notably Tier 1 + Tier 2 of `definition-of-done.md`, `prohibitions.md`
(incl. no Claude co-author line on salestech-be commits), and the pytest cap (≤5 files,
≤2 workers).

## AH skills (catalog as of 2026-09-25)
Unused: `check-spec`, `merge-slice`, `finalize-stack`, `land-owner` — don't invoke.
Used: `.claude/lib/code_owners.py` (`owners` = which team owns each path; `approvals <pr>`),
run from `salestech-be/`. Missing ⇒ AH isn't applied; re-run its `bootstrap.sh`.
Per-file decisions + how to check AH for changes: `knowledge-base/concepts/harness/assimilation-harness.md`.

This applies across all sessions working in this workspace.
