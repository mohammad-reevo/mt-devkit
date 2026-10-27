#!/usr/bin/env python3
"""Prove an update-branch merge changed nothing of the PR's own but mechanical lines.

    pr_diff_guard.py snapshot <base-ref> <out.json>   # before the merge
    pr_diff_guard.py check    <base-ref> <snap.json>  # after the merge, before the push

Run inside the PR's repo checkout. Both commands read the PR's own change, `git diff
$(git merge-base <base-ref> HEAD) HEAD`, as each file's added and removed lines without
context or line numbers, so main moving underneath leaves it unchanged. `check` exits 0
when the file set and every file's lines match the snapshot, and 1 listing each
difference otherwise -- the push is refused on 1.

Regenerated files (GENERATED) are allowed through: only their presence in the file set is
compared.

Stdlib only; keep it 3.9-compatible.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

GENERATED = ("schema.sql", "openapi.json")


def _git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def _own_change(base):
    merge_base = _git("merge-base", base, "HEAD").strip()
    files = {}
    current = None
    for line in _git("diff", "-U0", "--no-color", merge_base, "HEAD").splitlines():
        if line.startswith("diff --git "):
            current = line.split(" b/", 1)[1]
            files[current] = []
        elif current is None or line.startswith(("+++", "---", "@@", "index ", "new file",
                                                 "deleted file", "similarity", "rename ",
                                                 "old mode", "new mode", "\\ No newline")):
            continue
        elif line.startswith(("+", "-")):
            if os.path.basename(current) in GENERATED:
                continue
            files[current].append(line)
    return files


def main():
    if len(sys.argv) != 4 or sys.argv[1] not in ("snapshot", "check"):
        sys.exit(__doc__)
    mode, base, path = sys.argv[1:]
    now = _own_change(base)
    if mode == "snapshot":
        with open(path, "w") as f:
            json.dump(now, f, indent=1)
        print("snapshot: {} files".format(len(now)))
        return
    with open(path) as f:
        before = json.load(f)
    problems = []
    for name in sorted(set(before) | set(now)):
        if name not in now:
            problems.append("dropped from the PR: " + name)
        elif name not in before:
            problems.append("new in the PR: " + name)
        elif before[name] != now[name]:
            gone = [l for l in before[name] if l not in now[name]]
            added = [l for l in now[name] if l not in before[name]]
            problems.append("changed: {}\n{}".format(
                name, "\n".join("    was " + l for l in gone) + "\n" +
                "\n".join("    now " + l for l in added)))
    if problems:
        print("PR diff changed beyond mechanical conflict fixes -- do not push:")
        print("\n".join(problems))
        sys.exit(1)
    print("ok: the PR's own change is identical ({} files)".format(len(now)))


if __name__ == "__main__":
    main()
