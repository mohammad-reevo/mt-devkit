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
- [ ] **Skills → `.claude/skills/`** — all 15: the 10 `mt-*` (scope, plan, implement, verify,
      babysit, done, workflow, worktree, db, populate-dev-data) + env-manager, spinup-local-db,
      claude-task, plan-split, create-testing-party-doc.
- [ ] **Hooks → `.claude/hooks/`** — `worktree_gate_hook.py` (the branch-guard hook joins later,
      see `tasks/branch-from-main-guard-hook.md`).
- [ ] **Rules → `.claude/rules/`** — worktrees, frontend-no-hardcoded-colors, test-economy,
      no-invented-requirements, defensive-defaults, response-altitude, python-service-style,
      typescript-style, openapi-regen, **local-logs**.
- [ ] **`spec/`** (design doc, ledger, this plan) and **`tasks/`** → repo root.

**KEEP global (`~/.claude`):**
- Rules: `explanation-modes`, `job-list-closing-sentinel`, `github`, `git-merge` (personal
  preferences / conventions that apply to *all* my work, not just this harness).
- `patch_acl_default.sh` — **not moved**; retired in Phase 4 with the acl drop (it only patches
  devkit's acl-hook).
- `settings.json` (global), memory, Slack MCP, acl configs.

- [ ] Keep the `mt-` prefix as-is for now; **no cross-reference / prefix cleanup here** (Phase 2).

### Phase-1 execution considerations (mechanics, not decisions)
- **Hook registration.** Moving `worktree_gate_hook.py` needs a **hooks block in
  `mt-devkit/.claude/settings.json`** to fire — a moved `.py` alone does nothing. This is a
  minimal hooks-only settings file, separate from the broader permissions/plugins settings
  discussion (Phase 4). Also **de-register** it from global `~/.claude/settings.json` so it
  doesn't dangle.
- **Memory is keyed to project path.** Memories under `~/.claude/projects/-…-devkit/memory/` won't
  auto-load in `mt-devkit` sessions (different project path). Migrating memory = **copying** the
  relevant files to the `mt-devkit` project-memory dir, not a file move. (Handled in Phase 2's
  memory pass; noting the mechanism here.)
- **Trim global `~/.claude/CLAUDE.md`** to the 4 rules that stay, after the move (Phase 2).
- **Reversible:** copy into `mt-devkit` and verify it loads *before* deleting from `~/.claude`.

## Phase 2 — De-prefix + fix references (wide scan)
- [ ] Drop the `mt-` prefix on the skill directories (`mt-scope` → `scope`, …).
- [ ] Fix **all** skill→skill references and script paths (`~/.claude/skills/mt-X/…` → the new
      location/name): workflow→scope/plan/implement/verify, plan→worktree, implement→verify,
      populate-dev-data→db, spinup-local-db→db, etc.
- [ ] Fix directory references that break with the move — `spec/`, `tasks/`, hook paths, hardcoded
      backend paths (e.g. `populate-dev-data`'s `SALESTECH_BE_ROOT` default), env-manager
      sibling-resolution.
- [ ] Update the design doc, parity ledger, memories, and tasks index to the new names/paths.

## Phase 3 — Bring in confirmed devkit items + finalize
- [ ] **Copy `.mcp.json`** from devkit (the one explicitly-confirmed keep).
- [ ] Finalize the migration — verify skills load under bare names, `db` works, worktree
      create/remove works, `workflow` runs.
- [ ] **Do NOT** add policies or `settings.json` here — those are Phase 4.

## Phase 4 — Discuss what else to bring from devkit (backlog)
- [ ] Discuss + decide: **policies** (incl. `skill_or_rule.md`), **`settings.json`** (incl. the
      narrow `permissions.allow` for `.claude/**` CRUD), **acl** handling, plugins/marketplace, and
      anything else undiscussed.
- [ ] The existing deferred chores in `tasks/` live here too (revisit as wanted).

## Open questions (flagged for review)
1. **Phase 3 vs 4 for the earlier "finalized keeps."** We'd finalized `skill_or_rule.md` +
   the narrow `permissions.allow` as Wave-6 keeps. Your reorg sends policies + settings to Phase 4
   discussion — so those two **re-open into Phase 4** (only `.mcp.json` is Phase 3). Confirm.
2. **Typo check:** you wrote "we'll discuss them in phase 3" for policies/settings, but Phase 4 is
   the discussion phase — reading it as **Phase 4**.
3. **Phase 1 split:** which personal-global items stay in `~/.claude` vs move to `mt-devkit`?
   (Decided together during Phase 1 — listed above as candidates.)
4. **Worktree-gate logistics:** `mt-devkit` will be a git primary checkout, so my always-worktree
   Edit/Write gate will **block** edits into it. Migration setup is deliberate config work on the
   harness itself — we run it with `CLAUDE_WORKTREE_GATE=0` (or an explicit bypass), not in a
   worktree. Flagging so it's a conscious choice.
