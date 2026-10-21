---
name: investigate-memory-usage
description: Find out where this Mac's memory went. Default mode is a breakdown by consumer — local backend stacks, vite dev servers, Docker VM, VS Code, browsers, Claude sessions, MCP servers — plus per-worktree footprints, processes over 700 MB, and anomalies (processes from deleted worktrees, orphaned API workers, day-old vite servers, every live local stack). `session` mode breaks it down per Claude session instead — which session's stacks, dev servers and test runs hold how much, and why. Read-only; proposes what to stop, never stops it unasked. Triggers on "why is my memory so high", "investigate memory usage", "what's eating memory", "memory breakdown per session", "/investigate-memory-usage", "/investigate-memory-usage session".
---

# investigate-memory-usage — where the memory went

Two modes, one script — `python3 -I .claude/skills/investigate-memory-usage/memory_report.py`:

| Mode | Command | Answers |
|---|---|---|
| `total` (default) | `memory_report.py` | Which consumers hold the memory, which worktrees, which processes, and what's anomalous |
| `session` | `memory_report.py session [--hours 36]` | Which Claude session holds what — its stacks, dev servers and test runs — and its job state |

Run from the mt-devkit root. It takes a few seconds (`top` samples once) and writes nothing.

## How it measures

- **Physical footprint, not RSS.** It reads `top`'s `mem` column, which counts swapped and
  compressed pages. Under pressure RSS under-reports badly — a 2 GB vite server shows ~50 MB RSS
  once it's swapped out — so a `ps`-based tally points at the wrong culprits.
- **Worktree attribution is by command line**: any process whose args contain
  `mt-devkit/worktrees/<name>/` belongs to that worktree (backend workers, vite, mypy, pytest).
- **Session attribution** reads every background job touched in the last `--hours` from
  `~/.claude/jobs/*/state.json` and gives each worktree to the job whose transcript names it most.
  Interactive sessions have no job file; the CLI + MCP cost of all sessions is one aggregate row.

## Reporting it

Lead with the verdict — total vs the machine's RAM, swap used, and the one or two consumers that
explain it. Then the script's table (consumer or session), then each anomaly as a sentence with
what stopping it would free. The usual culprits, in the order they've mattered:

1. **Local stacks left up after testing** — ~10 GB each (backend processes + vite); the default
   stack runs more workers, ~17 GB. A session at `[TO REVIEW]` / `[CI]` / done doesn't need one.
2. **Vite servers outliving their session** — ~2 GB each; anything up more than a day is suspect.
3. **Orphaned processes** — an API worker whose parent died, or anything still running from a
   deleted worktree.
4. **VS Code after weeks of uptime** — 10–15 GB; a restart reclaims most of it.
5. **Claude sessions** — ~0.4 GB each plus their MCP servers; only closing sessions reduces it.

Only Docker is shared between stacks; every stack runs its own backend and frontend.

## Stopping things — only on my go

Ask before stopping anything, naming each target, its session, and what it frees. Then:

- **A stack → `local-stack down --name <worktree>`.** Never `env-manager`'s kill-be: its
  `pkill -f salestech_be` takes down every stack on the machine.
- **Anything else → match the worktree path, and split PIDs with `xargs`**:
  `pgrep -f "/worktrees/<name>/" | xargs kill`. In zsh, `kill $pids` passes the whole list as
  one argument and kills nothing.
- **Never kill bare `uv run python -m salestech_be…` wrappers by command line.** Live stacks run
  the same inner wrappers (without `local_dev.cli` in their args), so a filter for "leftover"
  wrappers takes down stacks in use. Kill the worktree's processes; their wrappers exit on their own.
- Re-run the report afterwards and give the before/after.

## Guardrails
- **Read-only until I say go.** The report proposes; it never stops a process.
- **Never stop a working session's stack** — check the session's state first (`session` mode).
- The numbers are a sample at one instant; swap drains slowly after processes stop, so judge a
  cleanup by free memory, not swap.
