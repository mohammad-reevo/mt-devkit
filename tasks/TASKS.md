# Deferred Claude Tasks

Personal tooling chores against my own harness — `~/.claude/` (personal-claude)
or the devkit repo (devkit). Not Linear (product work), not memory (facts).

Managed by the `claude-task` skill (`defer` captures, `list` shows, `execute`
drains). Finishing a task = delete its file and its line below. This index is
loaded on demand (when working on a task), not every session.

- [protect-worktree-env-secrets](protect-worktree-env-secrets.md) — personal-claude — harden .env secret handling so worktree/env ops never leak keys
- [mt-backend-request](mt-backend-request.md) — personal-claude — rebuild devkit's backend-request (auth'd local-backend HTTP) when first needed
- [drop-devkit-acl-hook](drop-devkit-acl-hook.md) — personal-claude — drop the devkit acl-hook dependency for native permissions (rebuild later only if wanted)
- [standalone-implement-subagent](standalone-implement-subagent.md) — personal-claude — lightweight implement path for post-PR tweaks / mini-PRs outside the full funnel
- [mt-implement-review-ast-checks](mt-implement-review-ast-checks.md) — personal-claude — fold devkit code-reviewer's structural AST check-intents (R001–R006) into mt-implement's review
- [branch-from-main-guard-hook](branch-from-main-guard-hook.md) — personal-claude — rebuild devkit acl-hook's "new branches only from an up-to-date main" guard as a personal hook
