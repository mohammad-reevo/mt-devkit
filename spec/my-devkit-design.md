# My Devkit — Design (v0)

> A fresh personal harness, built from scratch with devkit as inspiration. Staged in
> `~/.claude/` now; graduates to its own repo later. Skills are prefixed `mt-` (temporary,
> stripped at graduation) so they coexist with devkit's skills instead of overriding them —
> I choose which to invoke per use.

## Status & scope
- **Wave 1 (✅ done):** the funnel — standalone, manually-invoked phase skills conducted by
  `mt-workflow`. **No harness** — no hooks, no session-state, no auto-transitions.
- **Wave 2 (✅ done):** devkit feature sweep — inventoried everything else devkit ships and, per
  item, decided **rebuild / copy / skip**, by kind: **2a. skills, 2b. hooks, 2c. rules**. Verdicts
  in the parity ledger (`devkit-parity.md`). This wave *decided*; the builds are Waves 3–4.
- **Wave 3 (✅ done):** skills the sweep kept — `mt-db` (one query skill; local by default, `dev`
  on request) and `mt-populate-dev-data`, both built self-contained (`mt-worktree` already done).
- **Wave 4 (✅ done):** rules the sweep kept — copied 6 rules into `~/.claude/rules/` + authored the
  openapi-regen rule (all de-coupled from devkit machinery).
- **Wave 5 (✅ done):** final holistic devkit review — swept the whole repo beyond skills/hooks/
  rules (MCPs, sub-agents, plugins, `settings.json`, commands, policy docs). Mostly SKIP-by-design;
  verdicts in the ledger. Finalized Wave-6 keeps: **copy `.mcp.json`**, **copy `skill_or_rule.md`**,
  **a narrow `~/.claude` + migrated-repo `.claude` CRUD allow-rule**.
- **Wave 6 (implement + graduate):** (1) at migration, **copy-paste devkit's `.mcp.json`** into the
  standalone repo; **copy `policy/skill_or_rule.md`**; add a **narrow `permissions.allow`** for CRUD
  on `~/.claude/**` + the migrated repo's `.claude/**` (folds in the old `auto-allow-claude-dir-crud`
  chore — no broader allowlist). (2) graduate — move the harness to a standalone repo, **drop the
  `mt-` prefix**, and drop the `@devkit` plugin enablements + marketplace (replaced by `mt-babysit` /
  native perms / in-skill review). *Deferred, not Wave 6:* folding code-reviewer AST check-intents
  into `mt-implement` (→ `mt-implement-review-ast-checks` task). (Orchestration → `mt-workflow`,
  subagent delegation → `mt-implement`, workspace isolation → `worktree_gate_hook.py` already landed;
  state files unnecessary under files-are-the-contract; auto-driving already done by `mt-workflow`.)
- Deferred one-off chores live in `~/.claude/tasks/` (the `claude-task` system), independent of
  these waves.
- **Parity ledger:** `~/.claude/spec/devkit-parity.md` is the durable at-a-glance record of every
  devkit skill/hook/rule and its verdict (rebuilt/covered/deferred/ignored/skip). Keep it updated
  as sweeps and builds land — it's the completeness check for the migration.
- Inconsistencies with devkit during staging are expected and accepted until full migration.

## Philosophy
- **I drive, skills assist.** Each phase is a skill I invoke manually. Nothing auto-runs the
  pipeline (that's Wave 2).
- **Files are the contract.** Each phase reads the previous phase's file and writes its own —
  plain markdown in `~/.claude/spec/`.
- **Coexist, don't override.** The `mt-` prefix keeps these distinct from devkit's skills so I
  can pick per-invocation rather than hard-overriding.
- **Compose, don't contain.** Skills re-use sibling skills instead of duplicating their logic
  (e.g. `mt-implement` calls `mt-verify` rather than containing verification). Abstractions
  emerge iteratively — build a skill simple first, extract pieces into their own skills as the
  system grows. *This applies among `mt-*` skills only* — see the next point for devkit.
- **Replace devkit, don't build around it.** The end goal is to move off devkit entirely, so
  no `mt-*` skill may invoke or depend on a devkit-provided skill (`verify`, `frontend-pr`/
  `backend-pr`, `babysit-pr`, `done`, `worktree`, …). When we need a capability devkit already
  has, we **duplicate it into a local `mt-` skill** and depend on that. (Claude Code *built-ins*
  are fair game — the ban is on devkit, not the core harness.) See
  [[project_moving_off_devkit]].
- **Guidance over gates** (a Wave-2 note): when the harness arrives, prefer soft rules over
  hard hooks — devkit over-enforces; this shouldn't fight me.

## The funnel (six phases)

A development idea flows through five skills, conducted by `mt-workflow`. Re-entrant — a later
phase can send me back to an earlier one. My touchpoints are deliberately few: **after scope**
(approve the direction), **at verify** (I direct the manual testing), plus anywhere mid-stream
if something comes up.

1. **`mt-scope`** — *brainstorm / discuss.* High-level direction + light research. 2–3
   approaches and tradeoffs, picks a direction, open questions. **No task breakdown, no file
   paths** — stays divergent. → scope file. *(I approve the direction before planning.)*
2. **`mt-plan`** — *strategy / detail.* Consumes the scope. Concrete goals, task breakdown,
   file-level detail, how-to-verify. → plan file.
3. **`mt-implement`** — *build (all coding).* Conducts the plan via per-task subagents (edits
   + checks), then the **`reviewer` trio finalizes all coding**, then commit + push. →
   a pushed, reviewed, green branch. **No PR.** (Code review is one-shot after full-plan
   implementation; later fixes don't re-run it.)
4. **`mt-verify`** — *prove it, then open the PR.* Manual testing / verification of the branch,
   **user-directed** (done with me, not autonomously). Once testing passes, **creates the PR**
   (description + screenshot). The PR is made only when the work is 100% complete.
5. **`mt-babysit`** — *land it.* Personal copy of the babysit skill — monitors CI + PR review
   comments, paced to a ~25-minute CI run (≈10-minute polls, which is the review-comment
   latency I'll accept). Runs automatically as the funnel tail once verify opens the PR;
   outside a drive, on explicit invoke. Never attaches itself to a bare push.
6. **`mt-done`** — *close out.* Manual (`/mt-done`): resolve the worktree's checked-out
   branches → gate their PR(s) on CI green + resolved threads → **delete** the idea's spec
   files (the PR is the source of truth) → tear down the worktree + local branches.

Seams: **implement** owns all *coding* (correctness + review) and ends at a pushed branch;
**verify** owns *proving it works* and is the gate that finally opens the PR; **babysit** owns
the PR's CI / comment lifecycle; **done** gates then tears the worktree down.

## Standalone tools (outside the funnel)
- **`pr-review`** — the `reviewer` trio on demand: my diff, my branch, or a teammate's PR.
  Report-only. Shares its agent with implement's finalization gate.
- **`mt-worktree`** — copy of devkit's worktree skill, rebuilt with my own instructions/spin.
- **`mt-db`** — one Postgres query skill; **local Docker** target by default, **dev** (Aurora
  writer; Tailscale + chamber) when specified.

## Artifacts & homes
- **Docs + per-idea phase files** live flat in **`~/.claude/spec/`** — no subdirectories, no
  namespace. This design doc lives here too. (Per-idea file naming convention is loose for now;
  refine when the first `mt-scope` runs.) Working artifacts — prune when the work ships.
- **Skills** install flat in **`~/.claude/skills/<mt-name>/`** (where the loader expects them).
  Each rebuilt skill carries a header note: "personal rebuild — `mt-` prefix temporary."

## Build order — ground-up: build simple, then expand
**Wave 1 funnel — ✅ all built** (see the Build log for per-skill detail):
1. ✅ **`mt-scope`** — funnel head (+ test-building call).
2. ✅ **`mt-plan`** — creates/enters the worktree up front.
3. ✅ **`mt-implement`** — v2 build-conductor (per-task subagents) + one-shot code-review
   finalization before push.
4. ✅ **`mt-verify`** — user-directed manual testing, then opens the PR.
5. ✅ **`mt-babysit`** — script-free personal copy of babysit-pr; auto-started funnel tail.
6. ✅ **`mt-done`** — simplified close-out; resolves by checked-out branches, tears down worktree.
7. ✅ **`mt-workflow`** — v2 conductor over the full 6-phase funnel.
8. ✅ **`mt-worktree`** — standalone; self-contained rebuild with the per-worktree frontend
   `.env` fix (see `feedback_worktree_reevo_backend_path`) + hook deny-message update.

Remaining tools (**Wave 3**): `mt-db`. Per-skill detail (exact instructions,
prompts, behaviors) is designed when each skill is built — not here.

## Build session protocol
For a session prompted "read this doc and build `mt-<skill>`", follow this:
1. Check the **Build log** below for what's done so far.
2. Brainstorm the skill's design with me first — high-level only, don't write
   anything until I approve.
3. Then write it to `~/.claude/skills/mt-<skill>/SKILL.md` (+ any helper files in
   that same dir).
4. devkit's version at `~/Desktop/code/devkit/.claude/skills/` is inspiration
   only — rebuild with my spin, don't copy.
5. When done, append one line to the **Build log** (date — skill — what was
   built/changed), and update other doc sections only if the design actually
   changed.

## Build log
<!-- Each build session appends one line when done: date — skill — what was built/changed -->
- 2026-07-06 — `mt-scope` — built v1: four-beat flow (frame → light research → diverge/converge → write file at convergence), research is a default beat with skill-judged depth, scope file convention fixed as `~/.claude/spec/<slug>-scope.md`, re-entrant revision on existing file, no-descending guardrail.
- 2026-07-06 — `mt-plan` — built v1: three beats (deep research → resolve open questions + task breakdown → converge and write `<slug>-plan.md`), scope-less quick-plan path with inline mini-scope, kickback rule to mt-scope, every task names files + done-signal.
- 2026-07-06 — `mt-implement` — built v1: direct in-session coding (no subagent dispatch yet — TODO 7), task loop ticks checkboxes in the plan file, small-drift amends plan inline / structural-drift kicks back to mt-plan, close-out (manual test, PR, screenshot) inlined and fenced for later mt-verify extraction.
- 2026-07-06 — all three — fresh-eyes review pass (2 reviewers), seam fixes: scope filename is slug authority + downstream skills glob instead of re-deriving; mt-plan revision re-reads scope and resets `[x]` ticks on rewritten tasks; plan template gains `> Repo:` header line; branch convention `mohammad/<slug>` off main; mt-verify extraction seam clarified (PR mechanics stay in implement).
- 2026-07-06 — `mt-workflow` — built v1 (pulled orchestration forward from Wave 2 as a *skill*, not a rule): conductor over the funnel, invokes each phase skill via the Skill tool, phase detected from spec files on disk (no state file). Asymmetric gating — hard stop at scope→plan (commit-to-research checkpoint), no gate plan→implement (plan approval is the checkpoint). Routes kickbacks. Status-view mode scans all spec files for a cross-idea overview.
- 2026-07-06 — `mt-scope` — reviewed for context delegation; **no change** — its one heavy beat (codebase research) already delegates to an Explore subagent that returns distilled findings; ticket read stays inline; conversation can't be delegated. Parallel exploration + distillation-reword declined as not worth it.
- 2026-07-06 — `mt-implement` — reshaped v2 into a **build conductor** (pulls Wave-2 TODO 7 forward): no longer codes in-session — dispatches one `general-purpose` subagent per task to edit + run that task's checks and return a lean report, main ticks checkboxes / owns drift + kickback decisions, then a subagent commits + pushes `mohammad/<slug>`. Close-out (manual test, review, babysit, PR, screenshot) removed — now ends at a pushed green branch and hands off to mt-verify.
- 2026-07-06 — **architecture** — funnel restructured 3→5 phases (scope → plan → implement → verify → babysit). Coding/proving/landing split cleanly: **code review moves INTO mt-implement** (finalizes all coding, one-shot post-implementation gate — later fixes don't re-run it); **PR creation moves OUT of implement INTO mt-verify** (opened only after manual testing passes 100%); **mt-verify is user-directed** (I drive the testing); **babysitting extracted to its own `mt-babysit` skill** (personal copy, opt-in) orchestrated by mt-workflow. Follow-ups queued: #5 implement code-review, #6 mt-babysit, #7 mt-workflow rework for 5 phases (incl. post-implement phase-detection, since verify/babysit state isn't in the spec files). Skill header notes still say "three-phase funnel" — fix when each skill is next edited.
- 2026-07-06 — `mt-workflow` — **reworked v1 → v2 for the full 6-phase funnel** (task #19): auto-drives scope → plan → implement → verify to an **open PR**, then STOPS. Post-scope **hard gate now requires a quick summary** (direction + approach + testing call + open questions) before I approve planning — scope is framed as the deep-context research phase. Phase detection extended: spec files for scope/plan/implement, **git/PR state for the tail** (plan all `[x]` + no PR → verify; PR open → in review). **babysit + done are never auto-run** (opt-in / explicit — surfaced only). Naming/convo (scope) + worktree (plan) ownership noted as out-of-workflow. Status view gains in-review/ready-for-done rows. Kickbacks unchanged (plan→scope, implement→plan). **This completes the funnel** — only #21 (protect .env) remains.
- 2026-07-06 — `mt-scope` — added the **test-building call** (task #20): scope now settles, at altitude, what testing the chosen direction warrants (unit / integration / none + why) as part of converging — recorded in a new `## Testing` scope section. mt-plan concretizes it into test tasks (its Verification note says "from the scope's Testing call — don't invent test scope"); mt-verify does post-build verification only, never decides tests. Keeps the kinds-of-tests decision high-level (no files/cases — that's mt-plan).
- 2026-07-06 — `env-manager` — added the worktree `.env` fix to the **run frontend** row (task #22, belt-and-suspenders on top of mt-worktree's create-time fix): before `run-fe-2`, a line-scoped in-place `sed` re-points `REEVO_BACKEND_PATH` in `apps/reevo-webapp/.env` at `<worktree_root>/salestech-be` (no-op in primary, fix in a worktree; secrets never read into context). Covers every frontend-start path since `run backend`/`run all-envs` compose this row.
- 2026-07-06 — **naming/worktree flow refined** (revises #18): the idea's **name is decided in mt-scope** now (mine if given, else self-generated; ticket → id lowercased), recorded in the scope file as a `> Name:` header, and the **convo rename (`/rename <name>`) is suggested at the very start of mt-scope**. mt-plan moved worktree+branch creation to the **beginning** (before deep research, not after the plan) — invokes `mt-worktree create <name>`, reads the name from the scope's `> Name:` header, no longer touches the convo. Both skills' header notes bumped to the 6-phase funnel.
- 2026-07-06 — `mt-verify` PR step + **PR-skills decision** (task #17) — DON'T duplicate devkit's frontend-pr/backend-pr. Discovered both repos own their PR tooling (`.claude/skills/pr-description` 266/411 lines, MANDATORY, impact-first + `pull_request_template.md`). mt-verify now uses the **relevant repo's own pr-description skill + template** (invoke if loaded, else read-and-follow — sub-repo skills aren't auto-loaded in the funnel session). No duplication → no drift, no devkit dep, no `mt-*-pr` skills. Using a repo's native tooling is NOT a devkit dependency (the replace-devkit ban is on devkit skills, not the repos').
- 2026-07-06 — `mt-babysit` — built v1 (personal copy of devkit's babysit-pr, **script-free** + self-contained — no Python helpers, no devkit plugin/hooks): poll loop over the worktree's PR(s) — CI via `gh pr checks`/`gh run view`, threads via the github.md all-threads GraphQL (fixes devkit's isOutdated-dropping bug), failing logs via `gh run view --log-failed`. **Opt-in — never auto-starts/nudges** (the key divergence from devkit). Flaky rerun capped at **once per headSha** and only when the failure doesn't overlap `git diff main...HEAD`. Reports, never fixes; reaching green does NOT auto-trigger mt-done. Dropped both devkit scripts (fetch_pr_comments.py, extract_job_failure.py) — inline gh suffices.
- 2026-07-06 — `mt-done` — built v1 (simplified personal close-out, none of devkit's session/projects/.runs machinery): manual only (/mt-done, + /mt-done cancel to abandon). RESOLVES BY the worktree's currently-checked-out branches (git branch --show-current per sub-repo) — not plan-tags, not branch enumeration (git branches are repo-global). Gate on each branch's PR: CI green + ALL review threads resolved (github.md all-threads GraphQL, isOutdated still counts as open); all-or-nothing, no merge required. Plan-optional cleanup: delete <slug>-plan/scope spec files if present. Teardown via mt-worktree remove (local branches only; remote untouched). Dropped the earlier `> Worktree:` plan-tag idea (so #13 no longer gates #7).
- 2026-07-06 — `mt-worktree` — built v1 (self-contained rebuild of devkit's worktree skill, no devkit scripts/hooks): `create`/`list`/`remove` modes + `mt_worktree_setup.sh` / `mt_worktree_teardown.sh`. Given a name → worktree of the parent + sub-repos each on `mohammad/<name>` (no ephemeral `wt-`), copies env/settings, `uv sync`. **Frontend `.env` fix baked in**: line-scoped in-place `sed` rewrites `REEVO_BACKEND_PATH` → the worktree's own `salestech-be` (secrets never read into context). Teardown deletes local branches only (remote untouched). Plus **hook update** (#12): `~/.claude/hooks/worktree_gate_hook.py` deny message now points to the mt-worktree skill instead of bare EnterWorktree/`git worktree add`. Deferred: #14 protect-.env, #15 env-manager re-apply fix.
- 2026-07-06 — `mt-implement` — added **code-review finalization** (task #5), inspired by devkit's code-reviewer (rebuilt self-contained, no plugin dependency): after full check suite green + before commit, one `general-purpose` review subagent reviews the branch diff against the repo's own `CLAUDE.md`/rules + general quality, returns verdict + findings; issues → bounded ~2 fix→re-review cycles (auto-fix) → escalate if stuck. One-shot gate — post-implementation (mt-verify) fixes don't re-run it. Header note updated to the 6-phase funnel; handoff text corrected (verify no longer "does review").
- 2026-07-06 — `mt-verify` — built v1: picks a verification strategy **implicitly** (scripts-only → run it / N/A → skip / in-app → user-directed live browser-MCP driving), no-workarounds rule, fixes surfaced bugs (which don't re-run implement's code review), then opens the PR **only after 100% pass**. PR step composes local `mt-<repo>-pr` (falls back to simple what/why/how-verified until those exist) — never devkit's PR skills. Also added Philosophy principle **"Replace devkit, don't build around it"** (duplicate devkit skills into `mt-`, never depend on them; core-harness built-ins are fine) + updated the `project_moving_off_devkit` memory. New tasks queued: #10 mt-scope test-building, #11 duplicate PR skills as `mt-*`.
- 2026-07-07 — **convo-rename dropped + human-readable slug** — the phase-prefix convo-rename idea is gone (a skill can't rename the convo — only I can via `/rename`), so mt-scope no longer suggests renaming the convo. The funnel slug is now a short human-readable name generated from the idea (e.g. `expand-eval-dataset`), not the Linear ticket id.
- 2026-07-07 — **Wave 5 holistic check** — swept the whole devkit repo beyond skills/hooks/rules (MCPs, sub-agents, plugins+marketplace, settings.json, commands, policy docs, misc). Mostly SKIP-by-design (funnel uses general-purpose subagents, guidance over gates, terse rules). Verdicts recorded in the ledger's "Other surfaces" section. Finalized Wave-6 keeps: **copy-paste `.mcp.json`** at migration (harness has no personal MCP config — inherits devkit's), **copy `policy/skill_or_rule.md`**, and **a narrow `permissions.allow` for CRUD on `~/.claude/**` + the migrated repo's `.claude/**`** (folds in the former auto-allow chore; no broader allowlist). Code-reviewer AST check-intents → deferred (`mt-implement-review-ast-checks` task). Graduation-cleanup: drop the `@devkit` plugin enablements (babysit-pr/acl-hook/code-reviewer) + marketplace, already replaced by mt-babysit / native perms / in-skill review.
- 2026-07-07 — **Wave 4 rules** — copied 6 devkit rules into `~/.claude/rules/` (test-economy, no-invented-requirements, defensive-defaults, response-altitude, python-service-style, typescript-style), substance intact but de-coupled from devkit machinery (dropped dangling `## Related`/`[[links]]` to non-copied rules, rephrased `.runs/`/`@policy`/code-reviewer-plugin references to self-contained equivalents; kept the valid defensive-defaults↔python-service-style cross-ref and real `salestech-be/`/`frontend-monorepo/` scoping). Authored `openapi-regen.md` (merges devkit's `update-openapi` + `fe-openapi-push`): regen backend spec then FE client via env-manager `gen-be`/`gen-fe`, and never hand-push the generated `packages/openapi-client/generated/` files.
- 2026-07-07 — `mt-db` + `mt-populate-dev-data` (**Wave 3**) — built both self-contained, no devkit deps. **`mt-db`** consolidates devkit's `local-db` + `dev-db` into one `dbquery.sh`: local Docker target by default, `--dev` → Aurora writer (password via `DB_PASSWORD`/chamber), `pg_isready` preflight with target-specific hints, `--csv/--expanded/--tuples-only`. Smoke-tested local (returned rows). **`mt-populate-dev-data`**: `populate.sh` runs only the destructive Docker-wipe + ~30-min DEV→local copy (make targets `docker-cleanup-dep`/`docker-start-dep`/`refresh-docker-db-from-cloud-dev-db` verified present); backend lifecycle delegated to **env-manager** (`run be`/`kill be`) and FalkorDB indexing + reconcile + verify driven from SKILL.md via **mt-db** — dropping devkit's `start-backend`/`local-db`/`backend-request` deps. Also **repointed `spinup-local-db`'s verify step** off devkit's `local-db/dbquery.sh` onto `mt-db` (killed a live devkit dependency).
- 2026-07-24 — `workflow` + `babysit` — **babysit is now the automatic funnel tail, and it polls on CI's real timescale.** `workflow`'s `verify → STOP` became `verify → babysit → STOP`: a freshly-opened PR always wants watching, so the opt-in pause bought nothing but delay. `done` remains the one explicit transition. babysit's entry contract narrowed rather than opened — auto-start comes *from the conductor*, and it still never attaches to a bare `git push` (the devkit divergence survives). Cadence reworked off the flat 90s poll (~16 wasted checks per run) onto a **CI-age-driven table**: 120s waiting for a run to register, **600s while a run is under 20 min old**, 300s inside the ~25-min finish window, 600s when only threads remain — floor 120s, ceiling 600s, shortest-across-PRs for cross-repo ideas. **The 10-minute base interval is a review-comment SLA, not a CI one** — CI alone would justify sleeping the full 25 min. Added: elapsed read from `gh run view --json startedAt`, a "25 min is expected, not a deadline — don't call it stuck before ~40 min" note, and a quiet-iteration rule (one line when nothing changed, not a repeat status table). Stale `opt-in` claim in `verify`'s guardrails corrected to point at the conductor.

## Wave 2 — devkit feature sweep (✅ DONE 2026-07-07)
Inventory everything else devkit ships that we haven't considered and, for each item, decide
**rebuild with my spin / straight copy / skip**. Nothing carries over by default; everything
earns its place. **This wave decides — it does not build** (the keeps become Waves 4–5).
**Full per-item verdicts live in the parity ledger (`devkit-parity.md`)**; summary below.

- **2a. skills** — swept 2026-07-07 (25 devkit skills total). **DONE.** Decisions:
  - *Already covered:* plan/implement/verify/done/worktree/babysit-pr → `mt-*`; backend-pr/
    frontend-pr → skipped (use repos' own `pr-description`); start-backend/frontend/realtime/
    ask-reevo → `env-manager`; local-db/dev-db → Wave 3.
  - *Build → **Wave 3** (skill):* **populate-dev-data** (restore an empty local DB — our
    verification rule cites it).
  - *Build → **Wave 4** (rule, not a skill):* **update-openapi** → an openapi-regen rule
    (trigger + command pointing at the sub-repo's gen target).
  - *Deferred to `~/.claude/tasks/`* (worth it, but implement when first needed, outside the
    waves): **backend-request** → `mt-backend-request.md`.
  - *Ignore — reimplement from scratch myself if/when I want them, not tracked:* run-e2e,
    notion-fetch, eng-design; and the maybes pr-screenshot / pull-ci-image / claude-config.
  - *Skip:* onboard (devkit first-run bootstrap — irrelevant to a personal harness).
  - *To 2b/2c:* concept-duplication (a code-reviewer plugin sub-skill — rides the hooks/agents pass).
- **2b. hooks** — swept 2026-07-07 (22 devkit hooks). **DONE.** *Guidance over gates* + no
  session/progress state machine → most SKIP. My `worktree_gate_hook.py` already covers the
  workspace-isolation want. **No hooks kept — no build wave.** Two live devkit deps surfaced and
  deferred to `tasks/`: edit-guard's `.env` slice (→ `protect-worktree-env-secrets`) and the
  acl-hook (→ `drop-devkit-acl-hook`, decided: drop for native permissions). See ledger for all 22.
- **2c. rules** — swept 2026-07-07 (27 devkit rules). **DONE.** **Keep → Wave 4** (copy to
  `~/.claude/rules/`): test-economy, no-invented-requirements, defensive-defaults,
  response-altitude, python-service-style, typescript-style; plus fe-openapi-push **merged** into
  the Wave-4 openapi rule. Seven others are COVERED by mt-* skills; the rest SKIP/ignored. See
  ledger for all 27.

## Wave 3 — skills the sweep kept (next)
Build each as a self-contained `mt-*` skill (my spin, no devkit dependency):
- **`mt-db`** — one Postgres query skill: **local** Docker target by default, **dev** (Aurora
  writer, Tailscale + chamber) when specified. Consolidates devkit's separate `local-db` + `dev-db`.
- **`mt-populate-dev-data`** — restore an empty local DB from real cloud dev data (~30 min; distinct
  from `spinup-local-db`'s synthetic fast seed). Kept separate from `mt-db`.

(`mt-worktree` is already built — Wave 1.)

## Wave 4 — rules the sweep kept (deferred)
Copy into `~/.claude/rules/` (they're devkit *project* rules today; this makes them personal +
durable): **test-economy**, **no-invented-requirements**, **defensive-defaults**,
**response-altitude**, **python-service-style**, **typescript-style**. Plus author an
**openapi-regen rule** (from `update-openapi`, with `fe-openapi-push` folded in).

## Wave 5 — final holistic devkit review (check only, deferred)
Before leaving devkit, sweep the **entire** repo once more — not just the skills/hooks/rules
already covered in Wave 2 — to catch anything the personal system is still missing. Candidate
surfaces to inventory: **MCP servers** (`.mcp.json`), **sub-agents** (`.claude/agents/`),
**plugins** + marketplace, **`settings.json`** (permissions, env, config), **slash commands**,
`CLAUDE.md`/policy docs, and any misc tooling. Same verdict discipline as Wave 2 (rebuild with my
spin / copy / skip), recorded in `devkit-parity.md`. **This wave only decides — it does not build**
(the keeps are built in Wave 6). Goal: a complete map so nothing's missed before graduation.

## Wave 6 — implement the Wave-5 keeps, then graduate (deferred)
Two parts:
1. **Build the Wave-5 keeps** (small, mostly config, done at migration time):
   - **Copy-paste devkit's `.mcp.json`** into the standalone repo (the personal harness has no MCP
     servers of its own today — it inherits devkit's; the file copies verbatim).
   - **Copy `policy/skill_or_rule.md`** into the personal harness (the one policy doc worth keeping
     — skill-vs-rule meta-guidance).
   - Add a **narrow `permissions.allow`** for CRUD on `~/.claude/**` + the migrated repo's
     `.claude/**` so harness edits don't prompt. No broader allowlist — `permissions.allow` stays
     otherwise empty. (Folds in the former `auto-allow-claude-dir-crud` chore.)
2. **Graduate** the harness out of staging: move `~/.claude`'s `mt-*` skills into their own
   standalone repo and **drop the `mt-` prefix** (they no longer need to coexist with devkit's
   skills once devkit is gone). Drop the `@devkit` plugin enablements (`babysit-pr`, `acl-hook`,
   `code-reviewer`) + `extraKnownMarketplaces.devkit` — already replaced by `mt-babysit` / native
   permissions / in-skill review.

*Deferred (not Wave 6):* folding devkit code-reviewer's AST check-intents (R001–R006) into
`mt-implement`'s review prompt → `~/.claude/tasks/mt-implement-review-ast-checks.md`.

Everything else the old "harness" wave listed already landed in Wave 1 — orchestration
(`mt-workflow`), subagent delegation (`mt-implement`), workspace isolation (`worktree_gate_hook.py`);
**state files** are unnecessary under files-are-the-contract (the scope/plan files + git/PR state
*are* the state), and **auto phase transitions** are already handled by `mt-workflow`'s auto-drive.

Skip / deferred decisions from Wave 2 need no wave — recorded in the ledger (`devkit-parity.md`);
deferred rebuilds live in `~/.claude/tasks/`.
