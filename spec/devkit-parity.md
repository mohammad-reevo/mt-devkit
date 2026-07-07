# Devkit Parity Ledger

> Durable record of the move off devkit: every devkit skill / hook / rule and what we did with it.
> The working decisions live in `my-devkit-design.md` (the waves); this is the at-a-glance
> reference + completeness check ("did we account for every devkit feature?"). Keep explanations
> **super brief** — one clause. Update as each sweep/build lands.

**Verdict tags:** `REBUILT` (personal mt-* exists) · `COVERED` (handled by another personal skill)
· `WAVE-N` (planned, not built) · `DEFERRED` (task in `~/.claude/tasks/`) · `IGNORED` (dropped;
reimplement from scratch if ever wanted) · `SKIP` (deliberately not wanted).

## Skills — swept 2026-07-07 (Wave 2a, done)

| devkit skill | verdict | note |
|---|---|---|
| plan | REBUILT → mt-plan | + worktree-up-front, consumes scope |
| implement | REBUILT → mt-implement | per-task subagents + in-skill code review |
| verify | REBUILT → mt-verify | user-directed; opens PR via repos' own pr skills |
| done | REBUILT → mt-done | simplified; resolves by checked-out branch, no session machinery |
| worktree | REBUILT → mt-worktree | self-contained; per-worktree `.env` fix |
| babysit-pr (plugin) | REBUILT → mt-babysit | script-free, opt-in, fixes isOutdated drop |
| local-db | ✅ BUILT → mt-db (local) | consolidated into `mt-db`; local is the default target |
| dev-db | ✅ BUILT → mt-db (dev) | consolidated into `mt-db`; `dev` target (Aurora writer, Tailscale + chamber) |
| start-backend | COVERED | env-manager + run commands |
| start-frontend | COVERED | env-manager + run commands |
| start-realtime | COVERED | env-manager |
| start-ask-reevo | COVERED | env-manager |
| populate-dev-data | ✅ BUILT → mt-populate-dev-data | restore an empty local DB from real dev data |
| update-openapi | ✅ BUILT (rule) | authored `~/.claude/rules/openapi-regen.md` |
| backend-request | DEFERRED | `mt-backend-request.md` — build when first needed |
| backend-pr | IGNORED | use salestech-be's own `pr-description` skill |
| frontend-pr | IGNORED | use frontend's own `pr-description` skill |
| pr-screenshot | IGNORED | repos' pr skills bring their own; only if mt-verify screenshots itself |
| run-e2e | IGNORED | reimplement myself if wanted |
| notion-fetch | IGNORED | reimplement myself if wanted |
| eng-design | IGNORED | reimplement myself if wanted |
| pull-ci-image | IGNORED | niche |
| claude-config | IGNORED | meta config-editing; native `update-config` covers most |
| onboard | SKIP | devkit first-run bootstrap — irrelevant to a personal harness |
| concept-duplication (plugin) | → 2c | code-reviewer sub-skill; rides the hooks/agents pass |

## Hooks — swept 2026-07-07 (Wave 2b, done)

Philosophy: *guidance over gates* + no session/progress state machine → most devkit hooks (which
enforce that machine) are SKIP.

| devkit hook | verdict | note |
|---|---|---|
| workspace_isolation_hook | COVERED | my `worktree_gate_hook.py`; rm-rf/subagent-git extras IGNORED |
| edit_guard_hook | DEFERRED | `.env`-protect slice folded into `protect-worktree-env-secrets.md`; rest SKIP |
| acl_hook (plugin) | DEFERRED | drop for native permissions — `drop-devkit-acl-hook.md` |
| context_saving_hook | IGNORED | file-size gate not wanted |
| worktree_hook | SKIP | superseded by mt-worktree skill |
| prompt_hook | SKIP | devkit lifecycle/Stop-enforcement glue |
| ci_watched_stamp_hook | SKIP | pairs with prompt_hook CI enforcement |
| summary_guard_hook | SKIP | devkit progress-file machine |
| progress_guard_hook | SKIP | devkit progress-file machine |
| subagent_dispatch_guard_hook | SKIP | devkit roster/session gates |
| subagent_progress_guard_hook | SKIP | devkit PROGRESS_ENTRY protocol |
| lifecycle_logger_hook | SKIP | observability only |
| pr_create_gate_hook | SKIP | mt-verify gates the PR in-skill |
| workflow_guard_hook | SKIP | plan-review/size/repo gates (repo-isolation already covered) |
| plan_authoring_hook | SKIP | devkit plan-format enforcement |
| subagent_push_guard (babysit-pr) | SKIP | would block mt-implement's subagent push |
| babysit_pr_nudge (babysit-pr) | SKIP | babysit is opt-in (`BABYSIT_PR_AUTONUDGE=0`) |
| commit_gate_hook (commit-gate) | SKIP | mt-implement runs checks in-skill |
| commit_review_nudge (code-reviewer) | SKIP | code review is in-skill |
| review_stamp_hook (code-reviewer) | SKIP | stamp-gated-push machinery |
| push_gate_hook (code-reviewer) | SKIP | stamp-gated-push machinery |
| code_quality_gate_hook (code-reviewer) | SKIP | plugin AST-linter gate |

**Personal hooks I keep:** `worktree_gate_hook.py` (workspace isolation — the one gate I want);
`patch_acl_default.sh` (only exists to patch devkit's acl-hook — retired when acl is dropped).

## Rules — swept 2026-07-07 (Wave 2c, done)

27 devkit rules. KEEP = copy into `~/.claude/rules/` so they survive devkit's removal (they're
devkit *project* rules today, not personal). COVERED = already baked into an mt-* skill.

| devkit rule | verdict | note |
|---|---|---|
| test-economy | ✅ COPIED | fewest tests, most distinct behavior |
| no-invented-requirements | ✅ COPIED | no unrequested behavior/fallbacks |
| defensive-defaults | ✅ COPIED | no silent try/except or loop skips |
| response-altitude | ✅ COPIED | calibrate reply detail; bottom line first |
| python-service-style | ✅ COPIED | backend service-layer conventions |
| typescript-style | ✅ COPIED | frontend TS conventions |
| fe-openapi-push | ✅ MERGED | folded into `openapi-regen.md` (don't hand-push generated openapi) |
| test-failures | IGNORED | dumped — reimplement if wanted |
| validate-data-freshness | IGNORED | dumped |
| validate-invariant-direction | IGNORED | dumped |
| resolve-premise-before-escalating | IGNORED | dumped |
| no-asking-just-do | IGNORED | dumped (behavior I follow anyway) |
| agent-dispatch-sizing | COVERED | mt-implement subagent discipline |
| auto-fix-audit-findings | COVERED | mt-babysit / mt-implement |
| investigation | COVERED | mt-* + file-size hook ignored |
| workflow-lifecycle | COVERED | mt-workflow |
| verification | COVERED | mt-verify / mt-implement |
| git-push | COVERED | mt-implement / mt-verify |
| plan-format | COVERED | mt-plan |
| curl | SKIP | → deferred mt-backend-request |
| local-db | SKIP | → mt-db (built) |
| start-backend-skill | SKIP | I use env-manager |
| session-data-access | SKIP | my funnel has no session files |
| api-documentation | SKIP | devkit plan-format-coupled |
| skill-activation-exemption | SKIP | devkit subagent meta |
| browser-automation | SKIP | devkit `.mcp.json` — revisit if mt-verify does MCP browser |
| ticket-creation | SKIP | Vladimir's convention, not mine |

**Wave 2 sweep complete** — 2a skills ✅, 2b hooks ✅, 2c rules ✅. Every devkit skill/hook/rule
is accounted for above.

## Other surfaces — swept 2026-07-07 (Wave 5, done)

Everything beyond skills/hooks/rules. Most is SKIP-by-design (the `mt-*` funnel uses
general-purpose subagents, guidance over gates, terse rules). Keeps → Wave 6.

| surface | verdict | note |
|---|---|---|
| **MCP servers** (`.mcp.json`: playwright-isolated/-interactive, linear, sentry, datadog, notion) | COPY → Wave 6 | just **copy-paste `.mcp.json`** verbatim into the standalone repo at migration. Simple; no per-server porting. |
| **permissions.allow** allowlist | SKIP (keep none) | not used today; keep it that way. Wave 6 adds ONLY a narrow allow-rule for CRUD on `~/.claude/**` + the migrated harness repo's `.claude/**` (the old `auto-allow-claude-dir-crud` chore, folded into Wave 6). |
| **policy/`skill_or_rule.md`** | COPY → Wave 6 | harness meta-guidance (skill vs rule) — genuinely useful for ongoing harness work. |
| **code-reviewer AST rules** (R001–R006: paired-dicts, stringly-enums, silent-substitute-except, …) | DEFERRED (task) | `mt-implement-review-ast-checks.md` — fold the check *intents* into `mt-implement`'s review prompt, not the engine. (silent-substitute-except already ↔ defensive-defaults.) |
| **sub-agents** (`.claude/agents/*`: code/test-writers, reviewers, ticket-writer, e2e-verifier, harness-code-writer) | SKIP | by design — `mt-*` skills spawn general-purpose subagents with inline prompts, no named roster. `ticket-writer` skipped with its convention (Vladimir's). |
| **plugins** context-saving / commit-gate | SKIP | file-size gate + commit gate not wanted (guidance over gates). |
| **plugins** acl-hook / babysit-pr / code-reviewer | SKIP (graduation cleanup) | replaced by: acl→native perms (`drop-devkit-acl-hook`), babysit→`mt-babysit`, code-reviewer→`mt-implement` review. Drop the `@devkit` plugin enablements + `extraKnownMarketplaces.devkit` at graduation. |
| **policy/** other 13 docs (workflow*, eng-*-process, salestech-be-patterns, local-*, testing-party-templates, api-doc-format, background-vs-foreground) | SKIP | devkit-workflow / Reevo-process specific, or covered by mt-skills. (background-vs-foreground is borderline — low value.) |
| **slash commands** | SKIP | neither side uses `commands/` files — parity, nothing to do. |
| **settings**: plansDirectory / worktree.bgIsolation / env vars / hook_utils.py / code-quality-gate.toml / output-styles / statusline / .githooks / CI | SKIP | devkit-workflow config or greenfield; set up fresh in the standalone repo at graduation. |

**Wave 5 complete.** Wave-6 keeps (finalized): **copy-paste `.mcp.json`**, **copy
`skill_or_rule.md`**, and **a narrow allow-rule for CRUD on `~/.claude/**` + the migrated repo's
`.claude/**`**. `permissions.allow` stays empty otherwise; code-review AST checks → deferred task;
plugins/marketplace → graduation-cleanup. Everything else skip.
