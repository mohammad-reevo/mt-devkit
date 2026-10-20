---
name: local-stack
description: Run several port-isolated local stacks at once — one per worktree, so more than one in-flight PR can be exercised in the app simultaneously. Each stack gets its own backend/frontend/realtime ports, its own Temporal namespace and Kafka consumer groups, and an org from a fixed pool of pre-seeded orgs. Modes — up / down / list / down-all / seed-pool. Distinct from `env-manager`, which owns the single default stack on 8000/3000/8787. Triggers on "run a second stack", "run two backends", "spin up a stack for this worktree", "start a parallel stack", "local-stack up/down/list", "/local-stack".
---

> Personal rebuild — mt-devkit owns the front door; salestech-be still owns the isolation.

# local-stack — one stack per worktree

Bring up a **port-isolated** backend + frontend + realtime for a worktree, so several PRs can be
running locally at the same time. Ports derive from a slot index — the lowest free one in the
pool (1–5):

```
backend 8000+index    frontend 3000+index    realtime 8787+index
```

```bash
bash .claude/skills/local-stack/stack.sh up
bash .claude/skills/local-stack/stack.sh up --name planner-inline-first -- --askreevo --skip-org-setup
bash .claude/skills/local-stack/stack.sh down --name planner-inline-first
bash .claude/skills/local-stack/stack.sh list         # every stack that exists, and whether it is running
bash .claude/skills/local-stack/stack.sh down-all     # every stack (env-manager's `kill stacks`)
bash .claude/skills/local-stack/stack.sh seed-pool    # once, from main: seed the pool orgs
```

`--name` is the **worktree** name (under `<main>/worktrees/`); omit it and the worktree
containing the cwd is used. Everything after `--` passes through to the underlying script:
`--workers <flows,graph,bulk,crm-sync>`, `--askreevo`, `--no-fe`, `--skip-org-setup` on `up`;
`--restore-env` on `down`.

## Framework — who owns what

- **Each worktree session owns its own stack**: `up` when it needs the app, `down` when it's
  finished. `/done` runs `down` for every worktree it tears down. The default stack
  (:8000/:3000/:8787, `env-manager`) is reserved for the orchestrator session on `main`.
- **The orchestrator owns the shared layer**: Docker, migrations, and resets (`env-manager`'s
  `reset envs` runs `down-all` first). Migrations happen once, from `main`; a stack that needs an
  unmerged migration is answered by merging it first.
- **Slots and orgs come from a pool of 5.** `up` takes the lowest free slot, and the org is derived
  from the slot, so the first concurrent stack runs on pool org 1, the second on org 2. `seed-pool`
  seeds all five once; integrations a fresh org lacks (Outreach OAuth) are added to each by hand,
  once. Nothing creates or removes a pool org, so `down` has nothing to clean up there.
- **Every `up` re-writes only the frontend's session token** for its slot's org (`--org-token-only`)
  — seconds, not the minutes a full org setup takes. After a reset a session may come back on a
  different slot; that's fine, the pool orgs are seeded alike. An `up` on an unseeded pool org
  fails and names `seed-pool`. A `seed-pool` slot failing on `user_email_idx` means stale seed users
  from an older run of that slot's org: `uv run python -m scripts.seed_dev_data --org-id <org>
  --reset` in salestech-be, then re-run `seed-pool`.
- **A salestech-be branch that predates the pool** runs as before: a hashed slot (1–15) and its
  own per-slot org, seeded on first `up`. `stack.sh` prints a note when that happens.

Which slots are claimed lives in one host-global registry (`~/.config/reevo/instances.json`,
`fcntl`-locked), so two sessions never take the same slot. `list` reads it and probes each port,
and also shows a stack that was never torn down after the registry dropped its record (its stack
dir under `~/.config/reevo/stacks/` still names it), and any worktree process holding a stack port
that nothing tracks at all (`untracked` — `kill` its process group by hand).

## What this owns, and what it delegates

The isolation machinery is **salestech-be source**, not skill code: `scripts/local_dev/cli.py`
(`reevo-local`) plus `instance_isolation.py` own the slot registry
(`~/.config/reevo/instances.json`, guarded by an `fcntl` lock), the Kafka topic + consumer-group
prefixing, the `TEMPORAL_NAMESPACE`, the CDC org skip-list, and the per-slot dev org. The running
backend reads exactly what `derive()` produces, so that stays where the backend can change it in
lockstep. **Never reimplement it here** — a fork of that contract breaks silently at runtime.

This skill owns the four things the backend-side skill cannot do from an mt-devkit session:

1. **All three repo paths from the worktree name.** The BE skill takes `--fe-repo` /
   `--realtime-repo`, both defaulting to `~/frontend-monorepo` / `~/reevo-realtime`. Omit them on
   your second stack and it points at the *first* stack's checkout and rewrites its `.env` — it
   only warns. The `worktree` skill already gives every idea its own three checkouts, so the flags
   are derived and the failure mode stops existing.
2. **An instance id that differs per worktree.** This is what makes a second stack possible at
   all — see below.
3. **A free-port preflight**, which is what fixes slot 10.
4. **Reachability.** The BE skill lives behind a door the funnel won't open: entering the
   `salestech-be` sub-repo as a worktree loads its `PreToolUse:Bash` hook and blocks all Bash.
   This runs from the mt-devkit session root.

### Why `--name` is always passed

The BE scripts default the instance id to `default_instance_id()`, which normalizes the basename
of `git rev-parse --show-toplevel` **run inside the backend checkout**. In the BE skill's own
layout that top level is a salestech-be worktree named for the feature, so the default is
meaningful. In *this* layout the backend is a sub-repo inside the parent worktree, so the top
level is always `…/worktrees/<name>/salestech-be` — basename `salestech-be`, normalized
`salestech_be`, **identical for every worktree**. The second stack would raise
`InstanceIdConflict` (same id, different `workspace_path`).

So `stack.sh` derives the id from the parent worktree dir name and always passes it explicitly.
Worktree names use dashes; instance ids must match `^[a-z][a-z0-9_]{0,29}$` (a dash raises a bare
`ValueError`), so it normalizes dashes to underscores.

## Relationship to `env-manager` — sibling, not extension

`env-manager` owns **the single default stack** on 8000/3000/8787 and the shared Docker dep stack.
This skill owns **numbered stacks**. Both resolve a worktree the same way (walk up to the dir
holding `salestech-be/` and `frontend-monorepo/` as siblings), so they agree on what a worktree is.

**Never tear a numbered stack down with `env-manager`.** Its kills are process-name-based and
port-agnostic — `kill-be` is `pkill -f salestech_be`, `kill-rt` is `pkill -f "pnpm.*dev"` — so
either one kills **every** stack on the machine, which is precisely what this skill exists to
prevent. `stack.sh down` is scoped: a PID file plus a process-tree walk, then `reevo-local down`
frees the slot and deletes that instance's Kafka topics. `env-manager`'s `kill stacks` row is the
exception that proves it: it delegates to `down-all` here rather than killing anything itself.

Conversely, `env-manager`'s `run backend` starts an un-namespaced backend on :8000. That is fine
alongside numbered stacks (different port, different Temporal namespace) — just don't kill it with
this skill or vice versa.

## What is isolated, and what is not

| Isolated per stack | Shared by every stack |
|---|---|
| Ports (backend / frontend / realtime) | **Postgres** — one database, one set of migrations |
| Temporal namespace | **Redis**, **FalkorDB** |
| Kafka topics + consumer groups | **Kafka broker**, **Temporal server** |
| Pool org (slot N ⇒ org N) | The Docker dep stack itself |

So a migration you run in one stack is live in all of them, and FalkorDB writes are not org-filtered
per instance. Isolation is about *processes and message routing*, not data.

Docker stays where `env-manager` puts it: **one dep stack, started from the primary checkout**.
This skill never starts, stops or rebuilds it — it only checks the dependency containers are up
(the BE script's own preflight).

## Logs

`<worktree>/salestech-be/logs/stack/<instance>/` — one `<label>.log` per process, plus a `pids`
file. Deliberately **not** `env-manager`'s flat `logs/backend_logs.txt`: two stacks writing there
would overwrite each other. See `.claude/rules/local-logs.md`.

## Guardrails

- **Never reimplement `reevo-local`.** Slot allocation, Kafka/Temporal namespacing and the dev-org
  seed are backend contract. Wrap them; don't fork them.
- **Never tear down with `env-manager`** (and never tell me to) — its kills hit every stack.
- **Never start or stop Docker from here.** One shared dep stack, owned by `env-manager`.
- **Slots are allocated lazily at `up`**, never at `worktree create` — there are only 5 in the
  pool, and most worktrees never run a stack.
- **A preflight failure keeps its slot claimed.** Free the port, or `down` to release the slot.
- **Every stack needs its own three checkouts.** That is what the `worktree` skill produces; don't
  point two stacks at one frontend checkout, whatever the flags allow.
