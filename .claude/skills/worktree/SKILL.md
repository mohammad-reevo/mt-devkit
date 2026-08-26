---
name: worktree
description: Manage isolated worktrees for my personal dev funnel. Given a name, creates a worktree of the parent workspace + its sub-repos (salestech-be, frontend-monorepo, reevo-realtime) each on a logical feature branch mohammad/<name>, with env/settings copied and the frontend→backend path fixed for the worktree. Four modes — create / create-review / list / remove, where create-review builds a lightweight read-only tree (one sub-repo, detached at someone else's ref, no deps) for reviewing a PR. Use to start isolated work, review a teammate's branch, see active worktrees, or tear one down. Triggers on "make/create a worktree", "list worktrees", "remove worktree <name>".
---

> Personal rebuild — self-contained, no devkit dependency.
> Standalone tool (rebuilt from devkit's worktree skill; self-contained, no devkit
> scripts/hooks). See `~/.claude/spec/my-devkit-design.md`.

# worktree — isolated worktrees for the funnel

Given a **name**, create a worktree of the parent workspace + its sub-repos, each on a logical
feature branch `mohammad/<name>`, env copied and the frontend's backend-path fixed for *this*
worktree. Four modes: **create / create-review / list / remove**. The setup/teardown scripts in this dir do
the mechanical work — `.env` secrets are handled on disk and never read into context.

## Resolve the workspace

`MAIN` = the primary checkout of the parent workspace (where the sub-repos live). Resolve it as
the first entry of `git worktree list` in the parent repo; fall back to
`~/Desktop/code/mt-devkit`. Worktrees live at `$MAIN/worktrees/<name>/`.

## `create <name>`

1. Run the setup script (it **syncs all four primary checkouts to fresh main** first, then
   creates the parent + sub-repo worktrees on `mohammad/<name>`,
   copies `.env*` + nested frontend env + `settings.local.json`, **rewrites `REEVO_BACKEND_PATH`**
   in the worktree's frontend env to `<worktree>/salestech-be` via a line-scoped in-place sed —
   secrets never read into context — and runs `uv sync`):
   ```bash
   bash $HOME/Desktop/code/mt-devkit/.claude/skills/worktree/worktree_setup.sh "<name>" "$MAIN"
   ```
2. Switch the session in: `EnterWorktree(path: "$MAIN/worktrees/<name>")`.
3. Report: "Worktree `<name>` ready — sub-repos on `mohammad/<name>`, backend path fixed for
   this worktree."

## `create-review <name> <subrepo> <ref>`

A **read-only review tree** — for reading someone else's branch, not building on it. Used by
`pr-review`; `done` tears it down like any other worktree.

1. Run the setup script in review mode:
   ```bash
   bash $HOME/Desktop/code/mt-devkit/.claude/skills/worktree/worktree_setup.sh \
     "<name>" "$MAIN" --review <subrepo> <ref>
   ```
2. Switch the session in: `EnterWorktree(path: "$MAIN/worktrees/<name>")` — the **parent**,
   never the sub-repo (entering a sub-repo loads its own `PreToolUse:Bash` hook and blocks
   Bash for the session).
3. Report the path and what's checked out.

Three differences from `create`, each load-bearing:

- **One sub-repo, not three.** A review reads one repo; the other two would be dead weight.
- **No env copy, no `uv sync`.** Nothing is executed in a review tree. This is the point: a
  review tree is **~390M** instead of the **~4-6G** a feature worktree costs.
- **Detached at `<ref>`, never a local branch.** `done` resolves each sub-repo's checked-out
  branch and gates the open PR for it. On a named branch tracking the author's ref that
  resolves *their* PR — so tearing down my own review tree would block on their CI and their
  unresolved threads. Detached leaves `git branch --show-current` empty, so no PR resolves and
  the gate is a no-op. Don't "simplify" this into a named branch.

`<ref>` must already exist locally — the script's step 0 fetches every primary, so
`origin/<their-branch>` is available for any same-repo PR.

## `list`

Show worktrees under `$MAIN/worktrees/`, most-recently-active first. For each, per sub-repo:
- branch: `git -C "$MAIN/worktrees/<name>/<subrepo>" branch --show-current`
- last commit: `git -C "$MAIN/worktrees/<name>/<subrepo>" log -1 --format='%ct|%cr'` (sort by
  `%ct`, show `%cr`)

Render a compact table (worktree | updated | salestech-be branch | frontend-monorepo branch |
reevo-realtime branch). `—` for a missing sub-repo. No `EnterWorktree`. If none: say so.

## `remove <name>`

1. If the session is **inside** that worktree, `ExitWorktree(action: "keep")` first — don't
   stand in a directory you're about to delete.
2. Run the teardown script:
   ```bash
   bash $HOME/Desktop/code/mt-devkit/.claude/skills/worktree/worktree_teardown.sh "<name>" "$MAIN"
   ```
   It removes each sub-repo worktree + the parent worktree and deletes the **local**
   feature branches — `mohammad/<name>` **and** whatever each tree actually had checked out,
   which differ once a session splits its work across two branches. Only the `mohammad/`
   namespace is eligible, so a tree left on `main` or a teammate's branch is never touched.
3. Report what was removed.

## Notes

- **`create` is what keeps the primary checkouts current.** They are never developed in, so
  nothing else advances their `main`. Step 0 of the setup script fetches and fast-forwards
  `main` in all four (`mt-devkit` + the three sub-repos) — which is why a new worktree branches
  off genuinely fresh `origin/main`, and why `branch_from_main_guard_hook`'s freshness test
  passes afterwards without a manual pull. Best-effort: offline degrades to a stale base, never
  to a failed create. A primary that is dirty or off `main` is fetched but not fast-forwarded.
- **Remote branches are never touched** — they back open PRs; GitHub deletes them on merge.
- One logical feature branch `mohammad/<name>` in every repo — no ephemeral `wt-<name>`.
- Worktrees share Docker infra (DB / Redis / Temporal) — only code differs.
- `.env` is copied + path-fixed on disk by the script, never read into the conversation.
  Deeper secret hardening is a separate task.
- **Funnel wiring (later):** `plan` will `create` a worktree (name from the idea);
  `done` calls `remove` to tear it down after close-out. `pr-review` uses `create-review`
  for a teammate's PR and never tears it down itself — `done` does, same as any worktree.
- After a standalone `create`, return to `/workflow` to drive the funnel in the new worktree
  — it owns what comes next.
