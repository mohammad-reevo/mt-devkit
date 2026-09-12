#!/usr/bin/env python3
"""PR-description preflight: run the target sub-repo's own validator before the PR is opened.

WHAT PROBLEM THIS SOLVES
------------------------
`salestech-be` ships a deterministic PR-description validator
(`scripts/hooks/validate_pr_description.py`) and a Claude hook that runs it
(`scripts/hooks/extract_pr_description.py`), registered as PreToolUse:Bash in
`salestech-be/.claude/settings.json`. It mirrors the mechanical subset of the
`pr-description-validation` CI job, so a malformed body is caught locally instead
of burning a ~25-minute CI round-trip.

That hook never fires for us. A funnel session runs from the mt-devkit workspace
root, so `CLAUDE_PROJECT_DIR` and the loaded settings are mt-devkit's; the
sub-repo's settings are never read. (We cannot fix that by entering the sub-repo
worktree instead -- doing so loads its own PreToolUse:Bash hook and blocks Bash
for the whole session.) The result: `salestech-be` PR #33134 burned three CI
cycles on pure format, every one of them mechanically detectable locally.

So this hook is a *shim*, not a reimplementation. It recognises a PR call,
works out which sub-repo it targets, and hands the untouched payload to that
repo's own validator with `CLAUDE_PROJECT_DIR` repointed.

WHY DELEGATE RATHER THAN ENCODE THE RULES HERE
----------------------------------------------
The contract is the sub-repo's and it moves with the sub-repo -- header set,
`Verification Metrics` label grammar, which diffs may claim `N/A`. A copy here
would go stale silently and start *passing* bodies that CI rejects, which is
strictly worse than no check. Delegation means we own zero contract knowledge:
when salestech-be changes the rules, this shim needs no edit.

Same reasoning that ruled out forking the sub-repo `pr-description` skill into
the harness -- see `.claude/skills/pr-description/SKILL.md`.

FAIL-OPEN, ALWAYS
-----------------
Every failure path allows: no validator in the target repo (frontend-monorepo
and reevo-realtime ship none), an unresolvable repo, a crash, a timeout. The
upstream hook is itself fail-open by design. A preflight that wrongly blocks a
PR is worse than one that misses -- CI is still the real gate.

Runs under /usr/bin/python3 (macOS system Python 3.9): keep 3.9-compatible
(no PEP 604 unions, no match/case). The delegated script is 3.9-safe too
(verified 2026-09-08: it carries `from __future__ import annotations`, so its
`str | None` annotations never evaluate).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

# The sub-repo's hook, relative to that repo's root. Its presence is what makes a
# repo eligible -- no path list of "repos that have one" to keep in sync.
DELEGATE_REL = os.path.join("scripts", "hooks", "extract_pr_description.py")

# MCP PR tools the delegate also understands. Registering them here means they
# are covered for free; the payload is passed through untouched.
MCP_PR_TOOLS = (
    "mcp__github__create_pull_request",
    "mcp__github__update_pull_request",
)

# Cheap prefilter so an ordinary Bash command never pays for a subprocess.
_PR_COMMAND = re.compile(r"\bgh\b.*\bpr\b\s+(create|edit)\b|\bgh\b.*\bapi\b.*\bpulls\b")

_REPO_FLAG = re.compile(r"--repo[=\s]+(?:[\w.-]+/)?([\w.-]+)")
_CD_PREFIX = re.compile(r"\bcd\s+([^\s;&|]+)")
_DASH_C = re.compile(r"\s-C\s+([^\s;&|]+)")

# How long the delegate gets. It shells out to git for the changed-file list, so
# it is not instant; a hung validator must not hang the PR.
TIMEOUT_SECONDS = 30


def _allow():
    # Emit nothing, exit 0: no decision, so other hooks and normal permissions
    # still apply. This hook only ever *adds* a deny; it never forces an allow.
    sys.exit(0)


def _unquote(value):
    return value.strip().strip("'\"")


def _find_repo_root(start):
    """Walk up from ``start`` to the first directory carrying the delegate."""
    try:
        path = os.path.realpath(os.path.expanduser(start))
    except Exception:
        return None
    while True:
        if os.path.isfile(os.path.join(path, DELEGATE_REL)):
            return path
        parent = os.path.dirname(path)
        if parent == path:
            return None
        path = parent


def _checkouts_named(base, name):
    """Every directory called ``name`` at or above ``base``, nearest first.

    The cwd of a funnel session is the workspace root, a worktree of it, or a
    sub-repo *inside* that worktree -- and only the first of those has the named
    checkout as a child. Joining the name onto the cwd therefore resolves the
    sibling from exactly one of the three shapes; walking up and looking for a
    child of that name resolves it from all of them.
    """
    found = []
    try:
        path = os.path.realpath(os.path.expanduser(base))
    except Exception:
        return found
    while True:
        candidate = os.path.join(path, name)
        if os.path.isdir(candidate):
            found.append(candidate)
        parent = os.path.dirname(path)
        if parent == path:
            return found
        path = parent


def _candidate_dirs(command, cwd):
    """Directories that might be the targeted repo, best signal first.

    `gh` is run in several shapes from a funnel session: with `--repo` from the
    workspace root, behind a `cd <sub-repo> &&`, or plainly inside the sub-repo.
    Each shape leaves a different clue, so all of them are tried.

    Returns ``(candidates, repo_name)`` -- ``repo_name`` is the repo `--repo`
    named, or None. The caller needs it to reject a root that is some *other*
    repo, which the candidate walk can still reach.
    """
    candidates = []
    repo_name = None
    base = cwd if cwd else os.getcwd()

    # `--repo ReevoAI/salestech-be` -> the checkout of that name at or above the
    # cwd. Only a sub-repo *inside* this workspace is eligible; a bare name
    # never escapes it.
    match = _REPO_FLAG.search(command)
    if match:
        name = match.group(1)
        if name not in (os.curdir, os.pardir) and "/" not in name:
            repo_name = name
            candidates.extend(_checkouts_named(base, name))

    for pattern in (_CD_PREFIX, _DASH_C):
        for raw in pattern.findall(command):
            path = _unquote(raw)
            if not path:
                continue
            candidates.append(path if os.path.isabs(path) else os.path.join(base, path))

    candidates.append(base)
    return candidates, repo_name


def _resolve_repo_root(command, cwd):
    candidates, repo_name = _candidate_dirs(command, cwd)
    for candidate in candidates:
        root = _find_repo_root(candidate)
        if not root:
            continue
        # `--repo` names the target outright, so a root that is a *different*
        # repo is one we walked up into -- most often the sub-repo the session
        # happens to be sitting in. Delegating there checks the body against
        # the wrong repo's template and denies a correct one.
        if repo_name and os.path.basename(root) != repo_name:
            continue
        return root
    return None


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        _allow()  # never block on malformed input

    tool_name = data.get("tool_name", "") or ""
    command = ""
    if tool_name == "Bash":
        command = (data.get("tool_input") or {}).get("command", "") or ""
        if not _PR_COMMAND.search(command):
            _allow()
    elif tool_name not in MCP_PR_TOOLS:
        _allow()

    repo_root = _resolve_repo_root(command, data.get("cwd") or "")
    if not repo_root:
        # frontend-monorepo and reevo-realtime ship no validator; so does any repo
        # outside the workspace. Nothing to delegate to.
        _allow()

    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = repo_root
    try:
        result = subprocess.run(
            [sys.executable, os.path.join(repo_root, DELEGATE_REL)],
            input=json.dumps(data),
            capture_output=True,
            text=True,
            cwd=repo_root,
            env=env,
            timeout=TIMEOUT_SECONDS,
        )
    except Exception:
        _allow()

    decision = (result.stdout or "").strip()
    if not decision:
        _allow()

    # Pass the delegate's decision through verbatim -- it owns the wording, and
    # re-rendering it here would be one more thing to keep in sync. Validate that
    # it is a deny before echoing, so malformed output cannot leak as a decision.
    try:
        parsed = json.loads(decision)
        hook_output = parsed.get("hookSpecificOutput") or {}
        if hook_output.get("permissionDecision") != "deny":
            _allow()
    except Exception:
        _allow()

    sys.stdout.write(decision)
    sys.exit(0)


if __name__ == "__main__":
    main()
