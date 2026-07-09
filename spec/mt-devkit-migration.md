# mt-devkit Migration Plan (Wave 6)

> Graduate the personal harness out of staging into its own repo, `mt-devkit` — a private repo
> parallel to `devkit`. **devkit is just a directory we worked in** — there's nothing to "turn
> off" and no `.env` to retire; we simply stop using it. Detailed phase checklist below; this
> supersedes the design doc's Wave-6 sketch.
>
> **Status: DRAFT for review — nothing executed yet.**

## Phase 0 — Repo + top-level docs
- [ ] Create the private git repo `mt-devkit`, connect to
      `https://github.com/mohammad-reevo/mt-devkit`.
- [ ] Top-level `README.md`.
- [ ] Top-level `CLAUDE.md` — personal workspace/orchestrator instructions (my funnel role; NOT a
      copy of devkit's PEV-workflow + agent-roster prose).

## Phase 1 — `.claude/` dir + move the personal harness in
Split principle: **shareable dev-harness → `mt-devkit`; personal-to-me preferences → global
`~/.claude`.** (I always work rooted in `mt-devkit`.) Finalized split:

**MOVE → `mt-devkit`:**
- [x] **Skills → `.claude/skills/`** — the 10 `mt-*` (scope, plan, implement, verify, babysit, done,
      workflow, worktree, db, populate-dev-data) + env-manager, spinup-local-db, plan-split,
      create-testing-party-doc. *(`claude-task` initially moved too, then pulled back to global —
      see KEEP.)*
- [x] **Hooks → `.claude/hooks/`** — `worktree_gate_hook.py` (the branch-guard hook joins later,
      see `branch-from-main-guard-hook` task).
- [x] **Rules → `.claude/rules/`** — worktrees, frontend-no-hardcoded-colors, test-economy,
      no-invented-requirements, defensive-defaults, response-altitude, python-service-style,
      typescript-style, openapi-regen, **local-logs**.
- [x] **`spec/`** (design doc, ledger, this plan) → repo root. *(`tasks/` does NOT move — stays
      global; see KEEP.)*

**KEEP global (`~/.claude`):**
- Rules: `explanation-modes`, `job-list-closing-sentinel`, `github`, `git-merge` (personal
  preferences / conventions that apply to *all* my work, not just this harness).
- **`claude-task` skill + `tasks/`** — personal chore-tracking (revised 2026-07-08, PR #7): moving
  `tasks/` into the repo would hit the worktree gate on every edit, and a task list isn't shareable.
  The global `claude-task` skill loads in every session (incl. mt-devkit), so nothing's lost.
- `patch_acl_default.sh` — **not moved**; retired in Phase 4 with the acl drop (it only patches
  devkit's acl-hook).
- `settings.json` (global), memory, Slack MCP, acl configs.

- [ ] Keep the `mt-` prefix as-is for now; **no cross-reference / prefix cleanup here** (Phase 2).

### Phase-1 execution considerations (mechanics, not decisions)
- **Hook registration.** Moving `worktree_gate_hook.py` needs a **hooks block in
  `mt-devkit/.claude/settings.json`** to fire — a moved `.py` alone does nothing. This is a
  minimal hooks-only settings file (permissions come in Phase 3; the broader plugins discussion is
  Phase 5). **De-registration** from global `~/.claude/settings.json` waits until **Phase 4** (with
  the legacy deletion) — during migration the global gate stays registered so it keeps protecting
  every repo; the mt-devkit registration is redundant-but-harmless until then.
- **Memory is keyed to project path.** Memories under `~/.claude/projects/-…-devkit/memory/` won't
  auto-load in `mt-devkit` sessions (different project path). Migrating memory = **copying** the
  relevant files to the `mt-devkit` project-memory dir, not a file move. (Handled in Phase 2's
  memory pass; noting the mechanism here.)
- **Trim global `~/.claude/CLAUDE.md`** to the 4 rules that stay — with the Phase-4 deletion.
- **Reversible:** copy into `mt-devkit` and verify it loads *before* deleting from `~/.claude`
  (the delete is Phase 4, the absolute end).

## Phase 2 — De-prefix + fix references (wide scan) — mostly DONE (PR #3)
- [x] Drop the `mt-` prefix on the 10 skill directories (+ renamed `mt_worktree_*.sh` scripts).
- [x] Fix **all** skill→skill references and skill **script** paths (`~/.claude/skills/mt-X/…` →
      `$CLAUDE_PROJECT_DIR/.claude/skills/X/…`). Verified 0 residual refs.
- [x] Hardcoded backend paths `~/Desktop/code/devkit/…` → `~/Desktop/code/mt-devkit/…`. (env-manager
      sibling-resolution is logic, not a path — unaffected.)
- [~] `spec/` + `tasks/` **data** references — intentionally **left global** (the effort stays in
      `~/.claude` until Phase 4; they repoint at cutover).
- [x] **Memory:** rewrote the obsolete `project_moving_off_devkit` guidance (harness now lives in
      mt-devkit, not global). Full memory *migration* to the mt-devkit project-path is Phase 4.
- [~] Design doc + parity ledger + tasks index full name-sync → folded into the **Phase 4** cutover
      (they're the global working copies that move then; historical `mt-*` names left as-is for now).

## Phase 3 — Confirmed devkit items + permissions + finalize — config DONE (PR #4)
- [x] **Copy `.mcp.json`** — 5 servers (playwright-isolated + linear/sentry/datadog/notion; dropped
      playwright-interactive) + `enableAllProjectMcpServers`.
- [x] **Permissions / allowlist** — broad fail-safe whitelist in mt-devkit's `.claude/settings.json`
      (dev toolbelt + Read/Edit/Write on `~/.claude`/`mt-devkit`/`devkit` + Web/Skill + playwright);
      `rm`/arbitrary-curl left to prompt; small deny for `rm -rf ~//` + force-push. Folds in the
      former `auto-allow-claude-dir-crud` idea and covers `claude-task`'s file ops.
      - common **Bash** (git, gh, cp, mkdir, mv, sed, python3, etc.),
      - **CRUD on the harness dirs** — mt-devkit `.claude/**`, `~/.claude/**`, and (while both
        coexist during the migration) the devkit paths that still get edited.
      - Folds in the former `auto-allow-claude-dir-crud` idea.
      - **Part of this touches `claude-task`** (its target dir + any task-related allows) — handle
        it here in Phase 3.
- [x] Finalize — **✅ verified in a real mt-devkit session** (2026-07-08): `db` returns a row; all
      5 MCP servers connected (playwright-isolated too, after clearing a corrupted npx cache); bare
      names load; no permission prompts. **Fix applied:** `$CLAUDE_PROJECT_DIR` is unset for
      skill-invoked bash → switched skill script paths to `$HOME/Desktop/code/mt-devkit/…` (PR #5).
      langfuse promoted to user scope + slack env fixed (both personal MCPs, outside the repo).
      **Nothing deleted from `~/.claude` yet** — that's Phase 4.
- [ ] Still **not** here: policies + the broader plugins discussion — Phase 5.

## Phase 4 — Delete the legacy copies + drop @devkit plugins + cut over (the absolute end)
Only after Phases 0–3 are done and verified (they are). The harness runs entirely from `mt-devkit`;
now remove the now-duplicate legacy copies AND the last live devkit dependencies (the 3 @devkit
plugins). **Ordered, verify between parts** — Parts B & C edit global config + need session restarts
(a you-restart / me-edit relay). Point of no return, but everything's verified.

**Part A — sync docs into mt-devkit (a PR):**
- [ ] Copy `~/.claude/spec/{my-devkit-design, devkit-parity, mt-devkit-migration}.md` → `mt-devkit/spec/`
      (overwrite the frozen Phase-1 snapshots) → PR → merge. So mt-devkit has the live docs before the
      `~/.claude` source is deleted.

**Part B — drop the @devkit plugins (global `~/.claude/settings.json`):**
- [ ] Remove the 3 `enabledPlugins` (babysit-pr, acl-hook, code-reviewer) + `extraKnownMarketplaces.devkit`
      (if present) + `env.ACL_HOOK_CONFIG` + the `SessionStart` `patch_acl_default.sh` hook. Delete
      `~/.claude/hooks/patch_acl_default.sh` + the acl config files. (Replacements confirmed:
      babysit→mt-babysit, acl→our branch guard PR #10 + permissions, code-reviewer→in-skill review.)
- [ ] **Restart → verify** a mt-devkit session: skills load, permissions work with no acl-hook, the
      branch guard (Hook 2) fires, no missing-plugin errors.

**Part C — de-register + delete the legacy harness (global `~/.claude`):**
- [ ] Remove the `Edit|Write` worktree-gate registration from global settings (runs from mt-devkit now).
- [ ] **Delete from `~/.claude`:** `hooks/worktree_gate_hook.py`, the 14 moved skills, the 10 moved
      rules, `spec/`. **KEEP:** the 4 preference rules (explanation-modes, job-list-sentinel, github,
      git-merge), the `claude-task` skill + `tasks/`, `settings.json`, memory, Slack MCP.
- [ ] Trim `~/.claude/CLAUDE.md` to the 4 remaining rules.
- [ ] **Restart → verify:** gate fires from mt-devkit, all skills/rules load from mt-devkit, no dangling
      `~/.claude/skills/...` refs.

**Part D — final:**
- [ ] Update the `project_moving_off_devkit` memory to "migration complete"; stop using the devkit dir.
- [ ] Final sanity sweep. *(`.vscode/settings.json`: no action — identical to devkit's, `${workspaceFolder}`-
      relative, gitignored local editor config; works as-is.)*

## Phase 5 — Optional ideation (backlog, non-blocking)
Everything cut-over-critical moved into Phase 4. Remaining is pure optional polish:
- [ ] **`policy/skill_or_rule.md`** — copy as personal harness meta-guidance.
- [ ] **`mt-implement-review-ast-checks`** — fold devkit code-reviewer's AST check-intents into the
      review prompt (quality enhancement, not a cutover requirement).
- [ ] The remaining deferred `tasks/` chores (revisit as wanted).

## Open questions (flagged for review)
1. **Phase placement of the earlier "finalized keeps."** `.mcp.json` → Phase 3; **`permissions.allow`
   → Phase 3** (moved up 2026-07-07 because the approve-this prompts got noisy); `skill_or_rule.md`
   (policy) stays a **Phase 5** ideation item. Deleting the legacy `~/.claude` copies is its own
   **Phase 4** (the absolute end — nothing global deleted before then). Resolved.
2. **Typo check:** you wrote "we'll discuss them in phase 3" for policies/settings, but Phase 4 is
   the discussion phase — reading it as **Phase 4**.
3. **Phase 1 split:** which personal-global items stay in `~/.claude` vs move to `mt-devkit`?
   (Decided together during Phase 1 — listed above as candidates.)
4. **Worktree-gate logistics:** `mt-devkit` will be a git primary checkout, so my always-worktree
   Edit/Write gate will **block** edits into it. Migration setup is deliberate config work on the
   harness itself — we run it with `CLAUDE_WORKTREE_GATE=0` (or an explicit bypass), not in a
   worktree. Flagging so it's a conscious choice.
