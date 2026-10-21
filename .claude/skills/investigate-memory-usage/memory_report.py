"""Where this Mac's memory went — by consumer (`total`) or by Claude session (`session`).

Read-only. Measures each process's physical footprint from `top` (it counts swapped and
compressed pages; RSS does not, and under memory pressure RSS under-reports badly), then groups
it. Prints markdown tables plus the anomalies worth acting on; never stops anything.

    python3 memory_report.py [total|session] [--hours N]
"""

import argparse
import collections
import glob
import json
import os
import re
import subprocess
import time

MAIN = os.path.expanduser("~/Desktop/code/mt-devkit")
WORKTREE_RE = re.compile(r"/mt-devkit/worktrees/([A-Za-z0-9._-]+)/")
UNITS_MB = {"K": 1 / 1024, "M": 1, "G": 1024, "B": 1 / 1048576}
BIG_MB = 700


def run(cmd: list[str]) -> str:
    return subprocess.run(cmd, capture_output=True, text=True).stdout


def footprints() -> dict[int, float]:
    """PID → physical footprint in MB, for every process `top` reports."""
    out, rows = run(["top", "-l", "1", "-o", "mem", "-n", "2000", "-stats", "pid,mem"]), {}
    started = False
    for line in out.splitlines():
        if line.startswith("PID"):
            started = True
            continue
        parts = line.split()
        if not started or len(parts) != 2 or not parts[0].isdigit():
            continue
        mem = parts[1].rstrip("+-")
        unit = mem[-1]
        value = float(mem[:-1]) if unit in UNITS_MB else float(mem)
        rows[int(parts[0])] = value * UNITS_MB.get(unit, 1)
    return rows


def processes() -> dict[int, tuple[int, str, str]]:
    """PID → (PPID, elapsed, full command line)."""
    rows = {}
    for line in run(["ps", "-axo", "pid=,ppid=,etime=,args="]).splitlines():
        parts = line.split(None, 3)
        if len(parts) == 4:
            rows[int(parts[0])] = (int(parts[1]), parts[2], parts[3].strip())
    return rows


def category(args: str) -> str:
    # Order matters: a worktree's vite or python must not fall through to "other".
    low = args.lower()
    if "Virtualization.VirtualMachine" in args:
        return "Docker VM"
    if "vite.js dev" in args:
        return "vite dev servers"
    if "partykit" in args:
        return "realtime (partykit)"
    if re.search(r"mypy|pytest|bake_playbooks|train_agent|compare_|generate_openapi", args):
        return "transient runs (mypy/pytest/bake/openapi)"
    if "salestech_be" in args or "multiprocessing" in args:
        return "local backend stacks"
    if "Visual Studio Code" in args or "Code Helper" in args:
        return "VS Code"
    if "mcp" in low:
        return "MCP servers"
    if "claude" in low:
        return "Claude CLI"
    if "firefox" in low or "plugin-container" in args:
        return "Firefox"
    if "Google Chrome" in args:
        return "Chrome"
    return "other"


def system_line() -> str:
    free = run(["memory_pressure"]).strip().splitlines()[-1]
    swap = run(["sysctl", "-n", "vm.swapusage"]).strip()
    return f"{free} · swap {swap}"


def worktree_usage(fp, procs) -> dict[str, dict]:
    """Worktree name → footprint of every process launched from it (stacks, vite, test runs)."""
    usage = collections.defaultdict(lambda: {"mb": 0.0, "pids": [], "oldest": ""})
    for pid, (_, elapsed, args) in procs.items():
        m = WORKTREE_RE.search(args)
        if m and pid in fp:
            u = usage[m.group(1)]
            u["mb"] += fp[pid]
            u["pids"].append(pid)
            u["oldest"] = max(u["oldest"], elapsed, key=lambda e: (len(e), e))
    return usage


def anomalies(fp, procs, usage) -> list[str]:
    found = []
    for name, u in usage.items():
        if not os.path.isdir(f"{MAIN}/worktrees/{name}"):
            found.append(f"processes from DELETED worktree `{name}` — {u['mb'] / 1024:.1f} GB, pids {u['pids']}")
    for pid, (ppid, elapsed, args) in procs.items():
        if ppid == 1 and "multiprocessing.spawn" in args and pid in fp:
            found.append(f"orphaned API worker pid {pid} (parent gone, up {elapsed}) — {fp[pid]:.0f} MB")
    vite = [(args, e) for _, (_, e, args) in procs.items() if "vite.js dev" in args]
    for args, elapsed in vite:
        if "-" in elapsed:  # etime grows a "D-" day prefix after 24h
            m = WORKTREE_RE.search(args)
            found.append(f"vite up {elapsed} for `{m.group(1) if m else '?'}` — likely stale")
    stacks = run(["bash", f"{MAIN}/.claude/skills/local-stack/stack.sh", "list"])
    found += [f"local-stack: {line.strip()}" for line in stacks.splitlines() if re.match(r"\s*\[", line)]
    return found


def total(fp, procs) -> None:
    cats = collections.defaultdict(lambda: [0.0, 0])
    for pid, (_, _, args) in procs.items():
        if pid in fp:
            c = cats[category(args)]
            c[0] += fp[pid]
            c[1] += 1
    print(system_line(), "\n")
    print("| Footprint | Processes | Consumer |\n|---|---|---|")
    for name, (mb, n) in sorted(cats.items(), key=lambda kv: -kv[1][0]):
        print(f"| {mb / 1024:.1f} GB | {n} | {name} |")
    print(f"| **{sum(c[0] for c in cats.values()) / 1024:.1f} GB** | | **total** |\n")

    usage = worktree_usage(fp, procs)
    if usage:
        print("| Footprint | Worktree | Oldest process |\n|---|---|---|")
        for name, u in sorted(usage.items(), key=lambda kv: -kv[1]["mb"]):
            print(f"| {u['mb'] / 1024:.1f} GB | {name} | up {u['oldest']} |")
    else:
        print("No processes running from any worktree.")

    print(f"\nProcesses over {BIG_MB} MB:")
    for pid in sorted((p for p in procs if fp.get(p, 0) > BIG_MB), key=lambda p: -fp[p]):
        ppid, elapsed, args = procs[pid]
        print(f"- {fp[pid]:.0f} MB pid={pid} ppid={ppid} up={elapsed} {args[:110]}")
    print("\nAnomalies:")
    for line in anomalies(fp, procs, usage) or ["none"]:
        print(f"- {line}")


def jobs(hours: float) -> list[dict]:
    """Background jobs touched in the last `hours`, each with the worktrees its transcript names."""
    rows, now = [], time.time()
    for path in glob.glob(os.path.expanduser("~/.claude/jobs/*/state.json")):
        if now - os.path.getmtime(path) > hours * 3600:
            continue
        try:
            state = json.load(open(path))
        except (OSError, json.JSONDecodeError):
            # Legit business flow: a job writes state.json non-atomically; a half-written
            # file is a job mid-update, and the next run reads it whole.
            continue
        mentions = collections.Counter()
        for sid in (state.get("resumeSessionId"), state.get("sessionId")):
            hits = glob.glob(os.path.expanduser(f"~/.claude/projects/*/{sid}.jsonl")) if sid else []
            if hits:
                with open(max(hits, key=os.path.getmtime), errors="ignore") as fh:
                    for line in fh:
                        mentions.update(re.findall(r"mt-devkit/worktrees/([A-Za-z0-9._-]+)", line))
                break
        rows.append({
            "name": state.get("name") or (state.get("intent") or "?")[:60],
            "state": state.get("state") or "",
            "mentions": mentions,
        })
    return rows


def session(fp, procs, hours: float) -> None:
    usage = worktree_usage(fp, procs)
    sessions = jobs(hours)
    # A worktree belongs to the session whose transcript names it most — one owner each.
    owner = {}
    for name in usage:
        best = max(sessions, key=lambda s: s["mentions"][name], default=None)
        if best and best["mentions"][name]:
            owner[name] = best
    per_session = collections.defaultdict(lambda: {"mb": 0.0, "why": []})
    unowned = []
    for name, u in usage.items():
        if name in owner:
            entry = per_session[id(owner[name])]
            entry["mb"] += u["mb"]
            entry["why"].append(f"`{name}` {u['mb'] / 1024:.1f} GB ({len(u['pids'])} procs, up {u['oldest']})")
        else:
            unowned.append(f"`{name}` {u['mb'] / 1024:.1f} GB")
    cli = sum(fp.get(p, 0) for p, (_, _, a) in procs.items() if category(a) in ("Claude CLI", "MCP servers"))

    print(system_line(), "\n")
    print("| Session | State | Footprint | Why |\n|---|---|---|---|")
    for s in sorted((s for s in sessions if id(s) in per_session), key=lambda s: -per_session[id(s)]["mb"]):
        e = per_session[id(s)]
        print(f"| {s['name']} | {s['state']} | {e['mb'] / 1024:.1f} GB | {'; '.join(e['why'])} |")
    if not per_session and not unowned:
        print("| *(no session holds a stack, dev server, or test run)* | — | 0 GB | |")
    if unowned:
        print(f"| *(no live session)* | — | | {'; '.join(unowned)} |")
    print(f"| All Claude sessions themselves | — | {cli / 1024:.1f} GB | CLI processes + their MCP servers |")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", nargs="?", default="total", choices=["total", "session"])
    parser.add_argument("--hours", type=float, default=36, help="session mode: jobs touched within this window")
    opts = parser.parse_args()
    fp, procs = footprints(), processes()
    total(fp, procs) if opts.mode == "total" else session(fp, procs, opts.hours)


if __name__ == "__main__":
    main()
