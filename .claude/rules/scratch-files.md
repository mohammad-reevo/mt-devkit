# Scratch / temp files go under ~/.claude/tmp/

## When to Apply
When writing any throwaway file — a one-off script (codemod, query, helper),
an intermediate output, or a large supplementary doc that doesn't belong in the
reply. Applies to the orchestrator **and every subagent** it dispatches.

## Rule
Write scratch to **`~/.claude/tmp/`** — never `/tmp`, never `$CLAUDE_JOB_DIR/tmp`.

- When the work is tied to a funnel idea/worktree, namespace it:
  **`~/.claude/tmp/<slug>/`** — so `/done` removes it on teardown.
- Ad-hoc scratch not tied to an idea can go directly under `~/.claude/tmp/`;
  it isn't auto-cleaned, so prefer a slug subdir whenever there is one.

## Why
`~/.claude/tmp/` is **one fixed path that exists in every session** — interactive
or background — and is identical for every subagent, so a convention pointing
there actually holds. The alternatives don't:

- **`$CLAUDE_JOB_DIR/tmp`** — set only for background jobs, launch-mode-dependent
  (absent interactively, unreliable under Agent View), and invisible to
  subagents. Its cleanup is Claude Code's job-deletion, not `/done`.
- **`/tmp`** — OS-shared (parallel jobs clobber each other), not on the
  auto-allow list (so every write **prompts**), and never cleaned by the funnel.

`~/.claude/tmp/` sits under `.claude/`, so writes there are already auto-allowed
by the permission guard (no prompt), and the `<slug>` subdir is cleaned by
`/done` when the idea is closed.

This applies across all sessions working in this workspace.
