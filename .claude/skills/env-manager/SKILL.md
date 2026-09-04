---
name: env-manager
description: Manage local Reevo dev environment (backend, frontend, realtime, docker) via envctl.sh, the script the user's ~/.zshrc aliases also wrap. Triggers on "run backend", "kill backend", "re-run backend", "check backend", "generate backend openapi spec", "run frontend", "run frontend with dev", "kill frontend", "re-run frontend", "check frontend", "generate frontend openapi spec", "run realtime", "kill realtime", "re-run realtime", "check realtime", "run all-envs", "kill all-envs", "re-run all-envs", "check all-envs", "run docker", "kill docker", "re-run docker", "restart docker", "check docker", "reload aliases", "pull <env_name>", "checkout <branch_name> <env_name>", "merge <branch_name> <env_name>", "check branch <env_name>".
---

# env-manager

## Purpose

This skill maps verbal commands to exact bash invocations of `envctl.sh`, the script beside this file that holds the local-env command bodies. That script is the source of truth — the user's `~/.zshrc` aliases are thin wrappers around it. If a command changes, change it in `envctl.sh`; never re-implement a body in a row here.

## Code changes do NOT require a re-run

The local services auto-reload on code changes — backend, frontend, and realtime all pick up edits without a restart. Since `run <env>` now stops-and-restarts the env, **do NOT `run` an env again just to pick up code changes.** Running "to pick up the changes" or "to verify" is wrong and wastes minutes of startup time.

**The one exception: actually executing a workflow.** The flow-engine / temporal worker processes started by `run-be` do not hot-reload. If the task involves actually *running* a workflow (executing a flow, triggering the flow engine), `run` **backend** first so the workers pick up the new code. Merely editing workflow-related code does not trigger this — only the intent to execute one does.

Restarting (`run`) is otherwise only for: explicit user request, a crashed/wedged service, or switching which worktree/branch a service runs from.

## Rules of execution

When the user invokes this skill with a verbal command (e.g. `/env-manager run be`):

1. **Match exactly one row** in the command map below. The match is on the user's literal words, in order. If no row matches, tell the user and stop — do not guess.
2. **Run the row's command verbatim.** Do not paraphrase, reorder, or substitute aliases.
3. **Call `<ENVCTL>` for every stack command — never `zsh -ic '<alias>'`.** `<ENVCTL>` is the literal path `/Users/mohammad/Desktop/code/mt-devkit/.claude/skills/env-manager/envctl.sh` (always the primary checkout, never a worktree copy). It holds the command bodies; the `~/.zshrc` aliases are thin wrappers around that same script, so the shell and this skill cannot drift. **A worktree-isolated session refuses to reach an alias at all** — both `zsh -ic '<alias>'` and `zsh -c 'source ~/.zshrc; …'` are denied, because the guard cannot prove sourced shell text won't run git outside the worktree — and the `worktree` skill enters every funnel worktree via `EnterWorktree`, so that denial covers every drive. A plain script path has nothing to source, so it passes.
4. **No extra steps.** No health checks, no readiness waits, no `docker ps` confirmations, no log tails — unless the user explicitly asks.
5. **Kill chains use `;` not `&&`** so the second cleanup runs even when the first finds nothing to kill.
6. **If something fails**, stop and report exactly what failed. Do not apply silent workarounds, do not retry with different flags, do not skip steps. The user reads logs themselves.
7. **Always anchor cwd at `<worktree_root>` first** (resolved per Rule 9). Bash tool sessions persist cwd between calls, and the ACL hook rejects any call whose cwd is inside a sub-repo (e.g. `salestech-be`, `frontend-monorepo`, `reevo-realtime`). Every command must begin with `cd <worktree_root> && cd <subdir> && ...` — never just `cd <subdir>`, and never the literal hardcoded path.
8. **Rule 4 exception — dispatch-then-poll when starting envs.** Applies only to **Envs** section rows that start a service.
    - **Dispatch in the background.** Issue every service-start row as a **background** Bash call (`run_in_background: true`). Never run it in the foreground, and never pipe it through `tail`/`head` — piping suppresses streaming, so you learn nothing until the command returns. `run-fe-2` and `run-rt` self-detach (they end in `&`), but **`run-be` can block for minutes** (its `make start-flow-dep` leg), so foregrounding it strands you with zero visibility.
    - **Poll state, not output.** After dispatching, poll `lsof` for the ports this run actually started, in a **bounded** loop — cap the iterations (~36 × 5s ≈ 3 min) instead of looping forever, so a service that never comes up fails loudly rather than hanging. Do **not** use `sleep N && lsof` — the harness blocks chained sleeps.
    - **On timeout, diagnose — don't re-run.** Name each port that is not listening and `tail -n 20` that service's log: backend `salestech-be/logs/backend_logs.txt`, frontend `frontend-monorepo/logs/frontend_logs.txt`, realtime `reevo-realtime/logs/dev.log`, docker `salestech-be/logs/docker_up_logs.txt`. Every start command already redirects to its own log — read the log; never re-run a command just to see its output.
    - **A lost tool result is recoverable.** Because the poll reads state, if a call's result is lost or hangs, simply re-poll `lsof`. Never sit waiting on a dead call.
9. **Resolve `<worktree_root>` before running any row.** mt-devkit can be checked out as the canonical clone at `/Users/mohammad/Desktop/code/mt-devkit` or as one or more worktrees at `/Users/mohammad/Desktop/code/mt-devkit/worktrees/<name>/`. Each is a complete clone containing `salestech-be/`, `frontend-monorepo/`, `reevo-realtime/`. Resolve as follows:
    - Start from the **live current working directory** — run `pwd` and use its output. Do **not** read the env header's "primary working directory": that value is captured at session start and never follows the session into a worktree, so it always resolves to wherever the session began (usually `main`) even when you are working inside a worktree. `pwd` is the only signal that reflects the worktree you are actually in.
    - Walk up the parent chain until you find a directory containing both `salestech-be/` and `frontend-monorepo/` as siblings. That directory is `<worktree_root>`. (Note: a bare `git worktree add` of a single sub-repo — e.g. a `worktrees/<name>/` that contains only `salestech-be/` — is **not** a resolvable worktree here; it lacks the `frontend-monorepo/` sibling, so the walk-up skips past it. A full mt-devkit worktree, created via the `worktree` skill, contains all sub-repos as siblings.)
    - If no such directory exists in the parent chain, **stop and tell the user**: "not inside an mt-devkit worktree". Do **not** silently fall back to `/Users/mohammad/Desktop/code/mt-devkit`.
    - **Cache the resolved value for the entire command.** All-Envs compositions inherit the same `<worktree_root>` — never re-detect mid-chain. Re-detect on each new `/env-manager` invocation.
    - Rationale: kills are port/process-based and already worktree-agnostic, but `run`/`git`/`gen` rows must operate on the worktree the user is currently sitting in.
    - **Exception — the Docker section.** Docker rows ignore this resolution and always use the primary checkout; see the note above the Docker command table for why.

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

**Killing whatever was already running is the point — don't flag it, don't ask.** The kill aliases are port- and process-name-based (`kill-be-f` ends in `pkill -9 -f salestech_be`, `kill-fe` frees tcp:3000), so they are **worktree-agnostic**: `run backend` from worktree A will take down a backend serving from worktree B. That is intended and expected — a port hosts one service, and I know what I am doing when I ask for a run. Do not warn about it beforehand, do not ask for confirmation, and do not offer to restart the other worktree's env afterwards. Just run the row and report the result. (Rule 6 still applies to genuine *failures* — this is not one.)

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
| merge `<branch_name>` `<env_name>` | `cd <worktree_root> && cd <env_subdir> && git pull && git merge origin/<branch_name>` |
| pull `<env_name>` | `cd <worktree_root> && cd <env_subdir> && git pull` and report pull output. |
| checkout `<branch_name>` `<env_name>` | `cd <worktree_root> && cd <env_subdir> && git checkout <branch_name>`. Report checkout output. Then execute **pull `<env_name>`** (this section) — that handles the upstream fast-forward, so checkout doesn't have to duplicate it. |
| check branch `<env_name>` | `git -C <worktree_root>/<env_subdir> branch --show-current`. Report a single line: `<env_name>: <branch_name>`. If the sub-repo directory doesn't exist, report `<env_name>: —`. If branch lookup returns empty, use `unknown`. |

### Backend

| You say | I run |
|---|---|
| run backend | **kill backend** (this section) first — a safe no-op if nothing is running — then `cd <worktree_root> && cd salestech-be && uv sync && mkdir -p logs && <ENVCTL> run-be`. Idempotent: stops any running backend, then starts fresh. **Then always run frontend (Frontend section) too** — the frontend caches an auth token minted by the backend at its own startup, and re-running the backend invalidates that token, leaving any already-running frontend silently unauthenticated. So `run backend` is really `run-be` → `run-fe-2`; the frontend must be (re)started against the fresh backend. Poll-until-listening per Rule 8 for **both** 8000 and 3000. (This coupling is why a bare backend restart used to leave the frontend dead/stale.) **Exception:** when `run backend` is invoked as a step inside a larger composition that already (re)starts the frontend *after* the backend — i.e. `run all-envs` — skip this trailing frontend run; the composition's own frontend step covers it. Only chain the frontend when `run backend` is the standalone command. |
| kill backend | `cd <worktree_root> && cd salestech-be && <ENVCTL> kill-be-f` |
| check backend | `lsof -iTCP:8000 -sTCP:LISTEN -nP`. If LISTENING, also run the **PID → worktree+branch lookup** helper for the first listening pid. Report a single line: `backend (port 8000): LISTENING — pid <pid>, worktree: <wt_name>, branch: <branch_name>` or `backend (port 8000): NOT LISTENING`. |
| generate backend openapi spec | `cd <worktree_root> && cd salestech-be && <ENVCTL> gen-be` |

### Frontend

| You say | I run |
|---|---|
| run frontend | **kill frontend** (this section) first — a safe no-op if nothing is running — then `cd <worktree_root> && cd frontend-monorepo && { sed -i '' -E "s#^REEVO_BACKEND_PATH=.*#REEVO_BACKEND_PATH=<worktree_root>/salestech-be#" apps/reevo-webapp/.env 2>/dev/null; true; } && pnpm install && mkdir -p logs && <ENVCTL> run-fe-2`. Idempotent: stops any running frontend, then starts fresh. The `sed` re-points the frontend's `REEVO_BACKEND_PATH` at **this** worktree's own backend before startup — a no-op in the primary checkout (the value already matches), but the fix in a worktree, where the copied `.env` still points at the main checkout and would otherwise leave `run-fe-2`'s token-gen hitting the wrong backend (`:3000` never comes up). Line-scoped `sed`, so no secret in the `.env` is read into context. |
| kill frontend | `cd <worktree_root> && cd frontend-monorepo && <ENVCTL> kill-fe` |
| check frontend | `lsof -iTCP:3000 -sTCP:LISTEN -nP`. If LISTENING, also run the **PID → worktree+branch lookup** helper for the first listening pid. Report a single line: `frontend (port 3000): LISTENING — pid <pid>, worktree: <wt_name>, branch: <branch_name>` or `frontend (port 3000): NOT LISTENING`. |
| generate frontend openapi spec | `cd <worktree_root> && cd frontend-monorepo && <ENVCTL> gen-fe` |

### Realtime

| You say | I run |
|---|---|
| run realtime | **kill realtime** (this section) first — a safe no-op if nothing is running — then `cd <worktree_root> && cd reevo-realtime && pnpm install && mkdir -p logs && <ENVCTL> run-rt`. Idempotent: stops any running realtime, then starts fresh. |
| kill realtime | `cd <worktree_root> && cd reevo-realtime && <ENVCTL> kill-rt` |
| check realtime | `lsof -iTCP:8787 -sTCP:LISTEN -nP`. If LISTENING, also run the **PID → worktree+branch lookup** helper for the first listening pid. Report a single line: `realtime (port 8787): LISTENING — pid <pid>, worktree: <wt_name>, branch: <branch_name>` or `realtime (port 8787): NOT LISTENING`. |

### mt-devkit

| You say | I run |
|---|---|
| check mt-devkit | `git -C <worktree_root> branch --show-current` for the branch. Apply the **Worktree root → name** helper to `<worktree_root>`. Report a single line: `mt-devkit: worktree: <wt_name>, branch: <branch_name>`. If branch lookup returns empty, use `unknown`. |

### Docker

**Docker rows always operate on the primary checkout** (`/Users/mohammad/Desktop/code/mt-devkit`),
whatever `pwd` says — for these rows, ignore the Rule 9 `<worktree_root>` resolution and use the
primary. Every worktree shares one Docker VM, one image set, and one Postgres; only code differs.
So bringing the deps up from a worktree would apply *that branch's* compose file and *that
branch's* migrations to state every other worktree also uses — which is how the DB ends up
stamped at a revision `main` cannot resolve, and how containers for services a branch has renamed
survive as orphans squatting on the ports their replacements need. Pinning Docker to `main` keeps
the shared infra at one known baseline.

| You say | I run |
|---|---|
| run docker | Ensure `main` is current and the Docker VM is up, then bring the compose deps up fresh — because **kill docker** now stops the VM, `run docker` must boot it first (this replaces the old "kill docker first" delegation, which would now needlessly stop-then-start the VM). (0) **Refresh `main`:** execute **checkout main backend** (Git section) against the primary checkout. The compose file `d-up` reads and the migrations it applies both come from that checkout, so a stale `main` is exactly what leaves the local DB stamped at a revision it cannot locate (`Can't locate revision identified by ...`). (1) **Start the VM if the daemon is down:** `docker info >/dev/null 2>&1 \|\| docker desktop start` — `docker desktop start` is synchronous, returning when the daemon is ready (~10s), and is skipped entirely when the daemon is already up. (2) **Recycle + bring up deps:** `cd <worktree_root> && cd salestech-be && <ENVCTL> d-down` (clears any existing deps — a no-op right after a fresh VM start), then `<ENVCTL> awssso && <ENVCTL> d-up`. (3) **redis-cluster guard:** after `d-up`, check `salestech_be-redis-cluster` — if it is `Restarting`/unhealthy, its persisted cluster state has tripped `[ERR] Node ... not empty` on recreate; reset only that one ephemeral volume and recreate it (named data volumes like Postgres are untouched): `cd <worktree_root> && docker compose -f salestech-be/deploy/docker-compose.yml --project-directory salestech-be --profile local-deps rm -sfv salestech_be-redis-cluster && docker compose -f salestech-be/deploy/docker-compose.yml --project-directory salestech-be --profile local-deps up -d salestech_be-redis-cluster`. Then poll it to `healthy`. (4) **Reap the FalkorDB test-org graphs** (see the `falkor-cleanup` skill for why): `bash $HOME/Desktop/code/mt-devkit/.claude/skills/falkor-cleanup/falkor_reap.sh`. This is the intended window — `d-up` returns only once FalkorDB is healthy (`up --detach --wait`), and the CDC consumers are backend processes that **run backend** has not started yet, so nothing is mid-write. Each org graph costs ~20 MB of index scaffolding and integration tests mint one org per test, so skipping this is what eventually has the host OOM killer take out vite and the backend. The script no-ops when the container is down; report its one-line `N → M graph(s), X → Y` output. |
| kill docker | Stop the deps **and** the VM, so the ~10 GB the idle Linux VM holds is actually reclaimed — `d-down` alone only removes containers, but the Apple-Virtualization VM keeps its committed guest RAM for its whole lifetime (Activity Monitor's "Virtual Machine Service" stays multi-GB with zero containers). (1) **If the daemon is up** (`docker info >/dev/null 2>&1`): `cd <worktree_root> && cd salestech-be && <ENVCTL> d-down` to gracefully remove the compose deps so nothing lingers across the VM cycle. (2) `docker desktop stop` (plain command, no cd — synchronous, ~25s; tears down the VM and backend, leaving only the tiny `vmnetd` privileged helper). If `docker info` already fails, the VM is already stopped — nothing to do. Named data volumes persist across the stop, so **run docker** recovers losslessly (Postgres data survives). |
| restart docker | `docker desktop restart` (no cd — path-independent; plain command, not a zsh alias). Restarts the Docker Desktop app/VM itself — use when the daemon hiccups or hangs. Distinct from **run docker** (which starts the VM if the daemon is down, then recreates the compose deps) — use **restart docker** when the daemon is wedged and needs a full app-level stop/start rather than a clean start from stopped. After it returns, run **check docker** (this section) and report its line. |
| check docker | (1) `docker info >/dev/null 2>&1 && echo "Docker daemon: RUNNING" \|\| echo "Docker daemon: NOT RUNNING"`; (2) if daemon is running, `cd <worktree_root> && docker compose -f salestech-be/deploy/docker-compose.yml --project-directory salestech-be --profile local-deps ps --format '{{.Name}}\t{{.Status}}'`. Do NOT `cd` into `salestech-be` — that pollutes the Bash session cwd and trips the workspace-isolation hook on subsequent calls. Report a single line: `Docker: daemon <running\|not running>, deps <all healthy\|<comma-separated unhealthy/non-Up service names>\|none>`. Use `none` if the compose table is empty, `all healthy` if every row's status starts with `Up` and contains `(healthy)`, otherwise list only the unhealthy/non-Up service names. Do not enumerate healthy services. If the daemon is not running, omit the deps segment. |

### Other

| You say | I run |
|---|---|
| reload aliases | `source ~/.zshrc` in **your own** shell — I cannot source it for you (Rule 3). Only needed when the *wrapper set* changes; a change to a command **body** in `envctl.sh` takes effect immediately, with no reload. |

## Why a script and not the aliases

The Bash tool's shell is non-interactive (and may be `bash`, not `zsh`), so `~/.zshrc` is never sourced and aliases like `run-be` don't exist there. The old bridge was `zsh -ic '<alias>'` — spawn an interactive zsh, let it source `~/.zshrc`, resolve the alias. That is **refused outright in a worktree-isolated session**: the guard cannot prove sourced shell text won't run git outside the worktree, and it rejects `zsh -c 'source ~/.zshrc; …'` on the same grounds. Because the `worktree` skill enters every funnel worktree via `EnterWorktree`, this made every row here unusable during exactly the work the funnel exists to drive — you could not start, stop, or even check the local stack from inside a drive.

So the bodies live in `envctl.sh`, which both callers reach: this skill by path, the user's shell through one-line `~/.zshrc` wrappers (`alias run-be='"$MT_ENVCTL" run-be'`). One definition, so the two cannot drift — the snapshot table this section replaced had silently drifted in three places before anyone noticed (`run-be`'s falkor temporal workers, `awssso`'s `env -u BROWSER`, `kill-be-f`'s `-sTCP:LISTEN`).

## Shell wrappers (one-time `~/.zshrc` setup)

This skill works without this step — it calls `envctl.sh` by path. The step exists so the user's own
shell shares the same definition instead of keeping a second copy that drifts. **Apply it only once
this change is merged**, since the aliases point at the primary checkout, and pointing them at a file
that isn't there yet breaks every new terminal:

```zsh
export MT_ENVCTL="$HOME/Desktop/code/mt-devkit/.claude/skills/env-manager/envctl.sh"

alias awssso='"$MT_ENVCTL" awssso'
alias alembic-up='"$MT_ENVCTL" alembic-up'
alias d-up='"$MT_ENVCTL" d-up'
alias d-down='"$MT_ENVCTL" d-down'
alias gen-be='"$MT_ENVCTL" gen-be'
alias run-be='"$MT_ENVCTL" run-be'
alias kill-be-f='"$MT_ENVCTL" kill-be-f'
alias gen-fe='"$MT_ENVCTL" gen-fe'
alias run-fe-2='"$MT_ENVCTL" run-fe-2'
alias kill-fe='"$MT_ENVCTL" kill-fe'
alias run-rt='"$MT_ENVCTL" run-rt'
alias kill-rt='"$MT_ENVCTL" kill-rt'
```

`kill-be`, `run-fe`, `d-cleanup`, `gpu`, `sz` are untouched — this skill never calls them.

One behaviour change to expect: `run-be` now backgrounds its processes from a script rather than from
the interactive shell, so they reparent to `init` and survive closing the terminal. Output still goes
to the same `logs/*.txt` files, and `kill-be-f` still stops them.

## Command reference

`envctl.sh` **is** the reference — read it, not a copy of it; `envctl.sh --help` lists the subcommands. Every one is cwd-dependent: run it from the sub-repo it belongs to, which is what Rule 7's `cd <worktree_root> && cd <subdir>` prefix establishes.

`gpu` and `sz` are deliberately absent from the script: `gpu` is plain `git pull`, which the Git rows now call directly, and `sz` must source into the caller's own interactive shell — something no script can do.
