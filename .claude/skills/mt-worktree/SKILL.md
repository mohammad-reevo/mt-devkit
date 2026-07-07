---
name: mt-worktree
description: Manage isolated worktrees for my personal dev funnel. Given a name, creates a worktree of the parent workspace + its sub-repos (salestech-be, frontend-monorepo) each on a logical feature branch mohammad/<name>, with env/settings copied and the frontend→backend path fixed for the worktree. Three modes — create / list / remove. Use to start isolated work, see active worktrees, or tear one down. Triggers on "make/create a worktree", "list worktrees", "remove worktree <name>".
---

> Personal rebuild — `mt-` prefix temporary (stripped at graduation to standalone repo).
> Standalone tool (rebuilt from devkit's worktree skill; self-contained, no devkit
> scripts/hooks). See `~/.claude/spec/my-devkit-design.md`.

# mt-worktree — isolated worktrees for the funnel

Given a **name**, create a worktree of the parent workspace + its sub-repos, each on a logical
feature branch `mohammad/<name>`, env copied and the frontend's backend-path fixed for *this*
worktree. Three modes: **create / list / remove**. The setup/teardown scripts in this dir do
the mechanical work — `.env` secrets are handled on disk and never read into context.

## Resolve the workspace

`MAIN` = the primary checkout of the parent workspace (where the sub-repos live). Resolve it as
the first entry of `git worktree list` in the parent repo; fall back to
`~/Desktop/code/devkit`. Worktrees live at `$MAIN/worktrees/<name>/`.

## `create <name>`

1. Run the setup script (it creates the parent + sub-repo worktrees on `mohammad/<name>`,
   copies `.env*` + nested frontend env + `settings.local.json`, **rewrites `REEVO_BACKEND_PATH`**
   in the worktree's frontend env to `<worktree>/salestech-be` via a line-scoped in-place sed —
   secrets never read into context — and runs `uv sync`):
   ```bash
   bash ~/.claude/skills/mt-worktree/mt_worktree_setup.sh "<name>" "$MAIN"
   ```
2. Switch the session in: `EnterWorktree(path: "$MAIN/worktrees/<name>")`.
3. Report: "Worktree `<name>` ready — sub-repos on `mohammad/<name>`, backend path fixed for
   this worktree."

## `list`

Show worktrees under `$MAIN/worktrees/`, most-recently-active first. For each, per sub-repo:
- branch: `git -C "$MAIN/worktrees/<name>/<subrepo>" branch --show-current`
- last commit: `git -C "$MAIN/worktrees/<name>/<subrepo>" log -1 --format='%ct|%cr'` (sort by
  `%ct`, show `%cr`)

Render a compact table (worktree | updated | salestech-be branch | frontend-monorepo branch).
`—` for a missing sub-repo. No `EnterWorktree`. If none: say so.

## `remove <name>`

1. If the session is **inside** that worktree, `ExitWorktree(action: "keep")` first — don't
   stand in a directory you're about to delete.
2. Run the teardown script:
   ```bash
   bash ~/.claude/skills/mt-worktree/mt_worktree_teardown.sh "<name>" "$MAIN"
   ```
   It removes each sub-repo worktree + the parent worktree and deletes the **local**
   `mohammad/<name>` branches.
3. Report what was removed.

## Notes

- **Remote branches are never touched** — they back open PRs; GitHub deletes them on merge.
- One logical feature branch `mohammad/<name>` in every repo — no ephemeral `wt-<name>`.
- Worktrees share Docker infra (DB / Redis / Temporal) — only code differs.
- `.env` is copied + path-fixed on disk by the script, never read into the conversation.
  Deeper secret hardening is a separate task.
- **Funnel wiring (later):** `mt-plan` will `create` a worktree (name from the idea);
  `mt-done` calls `remove` to tear it down after close-out.
- After a standalone `create`, return to `/mt-workflow` to drive the funnel in the new worktree
  — it owns what comes next.
