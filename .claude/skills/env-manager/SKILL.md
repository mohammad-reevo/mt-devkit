---
name: env-manager
description: Manage local Reevo dev environment (backend, frontend, realtime, docker) using the user's ~/.zshrc aliases. Triggers on "run backend", "kill backend", "re-run backend", "check backend", "generate backend openapi spec", "run frontend", "run frontend with dev", "kill frontend", "re-run frontend", "check frontend", "generate frontend openapi spec", "run realtime", "kill realtime", "re-run realtime", "check realtime", "run all-envs", "kill all-envs", "re-run all-envs", "check all-envs", "run docker", "kill docker", "re-run docker", "restart docker", "check docker", "reload aliases", "pull <env_name>", "checkout <branch_name> <env_name>", "merge <branch_name> <env_name>", "check branch <env_name>".
---

# env-manager

## Purpose

This skill maps verbal commands to exact bash invocations of the user's `~/.zshrc` aliases. The aliases are the source of truth — if one changes, update only the row in the command map, never re-implement the alias body.

## Code changes do NOT require a re-run

The local services auto-reload on code changes — backend, frontend, and realtime all pick up edits without a restart. Since `run <env>` now stops-and-restarts the env, **do NOT `run` an env again just to pick up code changes.** Running "to pick up the changes" or "to verify" is wrong and wastes minutes of startup time.

**The one exception: actually executing a workflow.** The flow-engine / temporal worker processes started by `run-be` do not hot-reload. If the task involves actually *running* a workflow (executing a flow, triggering the flow engine), `run` **backend** first so the workers pick up the new code. Merely editing workflow-related code does not trigger this — only the intent to execute one does.

Restarting (`run`) is otherwise only for: explicit user request, a crashed/wedged service, or switching which worktree/branch a service runs from.

## Rules of execution

When the user invokes this skill with a verbal command (e.g. `/env-manager run be`):

1. **Match exactly one row** in the command map below. The match is on the user's literal words, in order. If no row matches, tell the user and stop — do not guess.
2. **Run the row's command verbatim.** Do not paraphrase, reorder, or substitute aliases.
3. **Use `zsh -ic '<chain>'`** for every alias call. This forces a fresh interactive shell that re-sources `~/.zshrc`, so aliases added mid-session are picked up.
4. **No extra steps.** No health checks, no readiness waits, no `docker ps` confirmations, no log tails — unless the user explicitly asks.
5. **Kill chains use `;` not `&&`** so the second cleanup runs even when the first finds nothing to kill.
6. **If something fails**, stop and report exactly what failed. Do not apply silent workarounds, do not retry with different flags, do not skip steps. The user reads logs themselves.
7. **Always anchor cwd at `<worktree_root>` first** (resolved per Rule 9). Bash tool sessions persist cwd between calls, and the ACL hook rejects any call whose cwd is inside a sub-repo (e.g. `salestech-be`, `frontend-monorepo`, `reevo-realtime`). Every command must begin with `cd <worktree_root> && cd <subdir> && ...` — never just `cd <subdir>`, and never the literal hardcoded path.
8. **Rule 4 exception — readiness poll after starting envs.** The `run-be`, `run-fe-2`, `run-rt` aliases background-detach immediately. After dispatching, poll: `until lsof -iTCP:8000 -sTCP:LISTEN -nP >/dev/null && lsof -iTCP:3000 -sTCP:LISTEN -nP >/dev/null && lsof -iTCP:8787 -sTCP:LISTEN -nP >/dev/null; do sleep 5; done` then report final lsof. Do **not** use `sleep N && lsof` — harness blocks chained sleeps. Applies only to **Envs** section rows that start a service.
9. **Resolve `<worktree_root>` before running any row.** mt-devkit can be checked out as the canonical clone at `/Users/mohammad/Desktop/code/mt-devkit` or as one or more worktrees at `/Users/mohammad/Desktop/code/mt-devkit/worktrees/<name>/`. Each is a complete clone containing `salestech-be/`, `frontend-monorepo/`, `reevo-realtime/`. Resolve as follows:
    - Start from the **live current working directory** — run `pwd` and use its output. Do **not** read the env header's "primary working directory": that value is captured at session start and never follows the session into a worktree, so it always resolves to wherever the session began (usually `main`) even when you are working inside a worktree. `pwd` is the only signal that reflects the worktree you are actually in.
    - Walk up the parent chain until you find a directory containing both `salestech-be/` and `frontend-monorepo/` as siblings. That directory is `<worktree_root>`. (Note: a bare `git worktree add` of a single sub-repo — e.g. a `worktrees/<name>/` that contains only `salestech-be/` — is **not** a resolvable worktree here; it lacks the `frontend-monorepo/` sibling, so the walk-up skips past it. A full mt-devkit worktree, created via the `worktree` skill, contains all sub-repos as siblings.)
    - If no such directory exists in the parent chain, **stop and tell the user**: "not inside an mt-devkit worktree". Do **not** silently fall back to `/Users/mohammad/Desktop/code/mt-devkit`.
    - **Cache the resolved value for the entire command.** All-Envs compositions inherit the same `<worktree_root>` — never re-detect mid-chain. Re-detect on each new `/env-manager` invocation.
    - Rationale: kills are port/process-based and already worktree-agnostic, but `run`/`git`/`gen` rows must operate on the worktree the user is currently sitting in.

## Env name → subdir mapping

When a row uses the `<env_name>` placeholder, substitute the matching `<env_subdir>` from this table.

| `<env_name>` | `<env_subdir>` |
|---|---|
| backend | `salestech-be` |
| frontend | `frontend-monorepo` |
| realtime | `reevo-realtime` |
| mt-devkit | `.` |
| all-envs | meta — implicit fan-out (see below) |

### `all-envs` fan-out

When a parameterized row receives `<env_name> = all-envs`, run the row's command **four times in parallel** — once for each of `{backend, frontend, realtime, mt-devkit}` — and report a 4-line block summarizing per-env results. This fan-out applies uniformly to every parameterized `<env_name>` row (`merge`, `pull`, `checkout`, `check branch`, etc.) so each new such row automatically supports `all-envs` without needing its own composition row.

If any individual fan-out call fails, report which env failed and stop per Rule 6 — do not silently skip.

The explicit rows in the **All-Envs** section (`run all-envs`, `kill all-envs`, `check all-envs`) take precedence over implicit fan-out because they encode specific ordering, sequencing, or extras (like Docker) that pure parallel fan-out cannot express.

## PID → worktree+branch lookup (helper)

Used by `check backend`, `check frontend`, `check realtime` to label the worktree and branch of a running env process. Given a pid, run **two separate pipelines** (do **not** chain them with `;`/`&&` or use `cwd=$(...)` — the ACL hook splits inside `$()` and prompts):

1. **cwd**: `lsof -p <pid> -a -d cwd -Fn | grep ^n | head -1 | sed 's/^n//'` — then apply the **Worktree root → name** helper to the cwd's worktree-root ancestor (the directory in its parent chain that contains both `salestech-be/` and `frontend-monorepo/` as siblings).
2. **branch**: `lsof -p <pid> -a -d cwd -Fn | grep ^n | head -1 | sed 's/^n//' | xargs -I {} git -C {} branch --show-current`

If branch lookup returns empty, use `unknown`. If multiple PIDs are listening on the same port (e.g. backend has parent + worker), inspect the first PID only — they share cwd via fork.

## Worktree root → name (helper)

Used by `check mt-devkit` and the worktree step of **PID → worktree+branch lookup**. Map a worktree root path:
- `/Users/mohammad/Desktop/code/mt-devkit` → `main`
- `/Users/mohammad/Desktop/code/mt-devkit/worktrees/<name>` → `<name>`
- Otherwise → `unknown (path: <path>)`

## Command map

The map is split into sections by domain. When a row delegates to another row, the target section is named in parentheses so it is unambiguous which sub-table to consult.

**`run` is idempotent (stop-then-start).** Every `run <env>` row first stops any running instance, then starts fresh — so there is no separate `re-run`. `re-run <env>` (and `re-run all-envs`) is an accepted synonym that does exactly what the matching `run` row does; the skill still activates on that phrasing.

### All-Envs

| You say | I run |
|---|---|
| run all-envs | **run docker** (Docker section) → **run backend** (Backend section) → **run realtime** (Realtime section) → **run frontend** (Frontend section), in that order. Each `run` is idempotent (stops any running instance first, then starts), so this also recycles whatever is already up — no separate re-run needed. Then poll-until-listening per Rule 8. |
| kill all-envs | **kill backend** (Backend section) → **kill realtime** (Realtime section) → **kill frontend** (Frontend section) → **kill docker** (Docker section), in that order. |
| check all-envs | **check mt-devkit** (mt-devkit section) → **check backend** (Backend section) → **check frontend** (Frontend section) → **check realtime** (Realtime section) → **check docker** (Docker section), in that order. Run all five and report combined results as **five separate lines** (one per sub-check, preserving each sub-row's "Report a single line" output verbatim — do not join with separators like `·` or `\|`). Do not stop on a NOT LISTENING / NOT RUNNING result (this is a status query, not a workflow step, so Rule 7 does not apply). |

### Git

`<branch_name>` is the branch the user names. `<env_name>` resolves to `<env_subdir>` per the **Env name → subdir mapping** section above.

| You say | I run |
|---|---|
| merge `<branch_name>` `<env_name>` | `cd <worktree_root> && cd <env_subdir> && zsh -ic 'gpu && git merge origin/<branch_name>'` |
| pull `<env_name>` | `cd <worktree_root> && cd <env_subdir> && zsh -ic 'gpu'` and report pull output. |
| checkout `<branch_name>` `<env_name>` | `cd <worktree_root> && cd <env_subdir> && zsh -ic 'git checkout <branch_name>'`. Report checkout output. Then execute **pull `<env_name>`** (this section) — that handles the upstream fast-forward, so checkout doesn't have to duplicate it. |
| check branch `<env_name>` | `git -C <worktree_root>/<env_subdir> branch --show-current`. Report a single line: `<env_name>: <branch_name>`. If the sub-repo directory doesn't exist, report `<env_name>: —`. If branch lookup returns empty, use `unknown`. |

### Backend

| You say | I run |
|---|---|
| run backend | **kill backend** (this section) first — a safe no-op if nothing is running — then `cd <worktree_root> && cd salestech-be && uv sync && mkdir -p logs && zsh -ic 'run-be'`. Idempotent: stops any running backend, then starts fresh. **Then always run frontend (Frontend section) too** — the frontend caches an auth token minted by the backend at its own startup, and re-running the backend invalidates that token, leaving any already-running frontend silently unauthenticated. So `run backend` is really `run-be` → `run-fe-2`; the frontend must be (re)started against the fresh backend. Poll-until-listening per Rule 8 for **both** 8000 and 3000. (This coupling is why a bare backend restart used to leave the frontend dead/stale.) **Exception:** when `run backend` is invoked as a step inside a larger composition that already (re)starts the frontend *after* the backend — i.e. `run all-envs` — skip this trailing frontend run; the composition's own frontend step covers it. Only chain the frontend when `run backend` is the standalone command. |
| kill backend | `cd <worktree_root> && cd salestech-be && zsh -ic 'kill-be-f'` |
| check backend | `lsof -iTCP:8000 -sTCP:LISTEN -nP`. If LISTENING, also run the **PID → worktree+branch lookup** helper for the first listening pid. Report a single line: `backend (port 8000): LISTENING — pid <pid>, worktree: <wt_name>, branch: <branch_name>` or `backend (port 8000): NOT LISTENING`. |
| generate backend openapi spec | `cd <worktree_root> && cd salestech-be && zsh -ic 'gen-be'` |

### Frontend

| You say | I run |
|---|---|
| run frontend | **kill frontend** (this section) first — a safe no-op if nothing is running — then `cd <worktree_root> && cd frontend-monorepo && { sed -i '' -E "s#^REEVO_BACKEND_PATH=.*#REEVO_BACKEND_PATH=<worktree_root>/salestech-be#" apps/reevo-webapp/.env 2>/dev/null; true; } && pnpm install && mkdir -p logs && zsh -ic 'run-fe-2'`. Idempotent: stops any running frontend, then starts fresh. The `sed` re-points the frontend's `REEVO_BACKEND_PATH` at **this** worktree's own backend before startup — a no-op in the primary checkout (the value already matches), but the fix in a worktree, where the copied `.env` still points at the main checkout and would otherwise leave `run-fe-2`'s token-gen hitting the wrong backend (`:3000` never comes up). Line-scoped `sed`, so no secret in the `.env` is read into context. |
| kill frontend | `cd <worktree_root> && cd frontend-monorepo && zsh -ic 'kill-fe'` |
| check frontend | `lsof -iTCP:3000 -sTCP:LISTEN -nP`. If LISTENING, also run the **PID → worktree+branch lookup** helper for the first listening pid. Report a single line: `frontend (port 3000): LISTENING — pid <pid>, worktree: <wt_name>, branch: <branch_name>` or `frontend (port 3000): NOT LISTENING`. |
| generate frontend openapi spec | `cd <worktree_root> && cd frontend-monorepo && zsh -ic 'gen-fe'` |

### Realtime

| You say | I run |
|---|---|
| run realtime | **kill realtime** (this section) first — a safe no-op if nothing is running — then `cd <worktree_root> && cd reevo-realtime && pnpm install && mkdir -p logs && zsh -ic 'run-rt'`. Idempotent: stops any running realtime, then starts fresh. |
| kill realtime | `cd <worktree_root> && cd reevo-realtime && zsh -ic 'kill-rt'` |
| check realtime | `lsof -iTCP:8787 -sTCP:LISTEN -nP`. If LISTENING, also run the **PID → worktree+branch lookup** helper for the first listening pid. Report a single line: `realtime (port 8787): LISTENING — pid <pid>, worktree: <wt_name>, branch: <branch_name>` or `realtime (port 8787): NOT LISTENING`. |

### mt-devkit

| You say | I run |
|---|---|
| check mt-devkit | `git -C <worktree_root> branch --show-current` for the branch. Apply the **Worktree root → name** helper to `<worktree_root>`. Report a single line: `mt-devkit: worktree: <wt_name>, branch: <branch_name>`. If branch lookup returns empty, use `unknown`. |

### Docker

| You say | I run |
|---|---|
| run docker | **kill docker** (this section) first — a safe no-op if nothing is running — then `cd <worktree_root> && cd salestech-be && zsh -ic 'awssso && d-up'`. Idempotent: tears down the compose deps, then brings them back up fresh. |
| kill docker | `cd <worktree_root> && cd salestech-be && zsh -ic 'd-down'` |
| restart docker | `docker desktop restart` (no cd — path-independent; plain command, not a zsh alias). Restarts the Docker Desktop app/VM itself — use when the daemon hiccups or hangs. Distinct from **run docker**, which only recreates the compose deps on an already-healthy daemon. After it returns, run **check docker** (this section) and report its line. |
| check docker | (1) `docker info >/dev/null 2>&1 && echo "Docker daemon: RUNNING" \|\| echo "Docker daemon: NOT RUNNING"`; (2) if daemon is running, `cd <worktree_root> && docker compose -f salestech-be/deploy/docker-compose.yml --project-directory salestech-be --profile local-deps ps --format '{{.Name}}\t{{.Status}}'`. Do NOT `cd` into `salestech-be` — that pollutes the Bash session cwd and trips the workspace-isolation hook on subsequent calls. Report a single line: `Docker: daemon <running\|not running>, deps <all healthy\|<comma-separated unhealthy/non-Up service names>\|none>`. Use `none` if the compose table is empty, `all healthy` if every row's status starts with `Up` and contains `(healthy)`, otherwise list only the unhealthy/non-Up service names. Do not enumerate healthy services. If the daemon is not running, omit the deps segment. |

### Other

| You say | I run |
|---|---|
| reload aliases | `zsh -ic 'sz'` (no cd — path-independent) |

## Why `zsh -ic`?

The Bash tool's shell is non-interactive (and may be `bash`, not `zsh`), so `~/.zshrc` is never sourced and aliases like `gpu` / `run-be` don't exist there. `zsh -ic '<alias>'` spawns an interactive zsh, which sources `~/.zshrc` and resolves the alias before exiting. Also covers the case where `~/.zshrc` was edited mid-session — the parent shell would still hold the old aliases.

## Alias reference (snapshot of `~/.zshrc`)

Reference only — the live `~/.zshrc` is the source of truth. If a row drifts, update this section.

| Alias | Expansion |
|---|---|
| `gpu` | `git pull` |
| `sz` | `source ~/.zshrc` |
| `alembic-up` | `uv run alembic upgrade head` |
| `awssso` | `aws sso login --profile $AWS_PROFILE` (where `AWS_PROFILE=workflow`) |
| `d-up` | `make docker-start-dep` |
| `d-down` | `make docker-suspend-dep` |
| `gen-be` | `uv run generate_openapi.py` |
| `run-be` | Backgrounds: `salestech_be` API + temporal workers (`integrity_job`, `chat`) + `make start-flow-dep LOG_DIR=logs` (which itself backgrounds `flow_engine --worker all`, `flow_change_consumer`, `debezium_consumer_v2`, `cdc-partitioner`, and the three `falkor` CDC event consumers — cdc / index / write). Each process redirected to its own `logs/*.txt` (or `logs/*.log` for the make-dispatched ones). The temporal `falkor` workers (workflow & activity) are intentionally NOT started — they only handle on-demand bulk ops (`IndexAll/SpecificOrganizationsWorkflow`, `Validate*Workflow`, `CleanupOrphanedAuthzSetsWorkflow`, `DeleteAllOrganizationsWorkflow`, etc.) triggered from `local_test_helpers/trigger_falkordb_*.py`. Start them manually only when running those helpers: `uv run python -m salestech_be.temporal.workers.falkor --worker workflow` and `--worker activity`. |
| `kill-be-f` | `lsof -ti tcp:8000 -sTCP:LISTEN \| xargs kill -9 2>/dev/null; pkill -9 -f salestech_be 2>/dev/null; true` |
| `gen-fe` | `pnpm generate-openapi-client:local` |
| `run-fe-2` | `pnpm -F ./apps/reevo-webapp dev > logs/frontend_logs.txt 2>&1 &` |
| `kill-fe` | `lsof -ti tcp:3000 -sTCP:LISTEN \| xargs kill -9 2>/dev/null; true` |
| `run-rt` | `pnpm dev > logs/dev.log 2>&1 &` |
| `kill-rt` | `pkill -f "pnpm.*dev" 2>/dev/null; true` |
