#!/usr/bin/env python3
"""Global worktree gate: deny Edit/Write that lands in a repo's primary checkout.

Personal ~/.claude enforcement (intentionally NOT devkit-coupled). Forces every
code change to happen inside a git worktree, keeping each repo's primary checkout
(its `main` working tree) pristine and free for parallel tasks.

Detection: a primary checkout has `.git` as a DIRECTORY; a linked worktree has
`.git` as a FILE pointing at the real gitdir. We deny edits whose target resolves
into a primary checkout and tell the agent to make/enter a worktree first (the
worktree skill). A hook cannot relocate the session itself -- it can only block
until the agent is in a worktree.

Allow (gate does not fire) when:
  - CLAUDE_WORKTREE_GATE=0            per-session escape hatch
  - target is not inside any git repo (worktrees require git)
  - target is inside a linked worktree (`.git` is a file -- already isolated),
    UNLESS that worktree is on `main`/`master` (on-main guard -- feature work
    belongs on a feature branch, so those are denied too)
  - target is under ~/.claude         (config must stay editable, incl. this hook)

Runs under /usr/bin/python3 (macOS system Python 3.9): keep 3.9-compatible
(no PEP 604 unions, no match/case).
"""
from __future__ import annotations

import json
import os
import sys


def _allow():
    # Emit nothing and exit 0: no decision, so other hooks / normal permissions
    # still apply. The gate only ever *adds* a deny; it never forces an allow.
    sys.exit(0)


def _deny(reason):
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
    )
    sys.exit(0)


def _nearest_existing_dir(path):
    d = path if os.path.isdir(path) else os.path.dirname(path)
    while d and not os.path.isdir(d):
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return d or os.getcwd()


def _enclosing_git_marker(start_dir):
    """Walk up from start_dir; return (repo_root, marker_path) or (None, None)."""
    d = os.path.realpath(start_dir)
    while True:
        marker = os.path.join(d, ".git")
        if os.path.exists(marker):
            return d, marker
        parent = os.path.dirname(d)
        if parent == d:
            return None, None
        d = parent


def _worktree_branch(marker):
    """Given a linked-worktree `.git` FILE, return its current branch name.

    No subprocess: read `gitdir: <path>` from the .git file, then parse
    `<path>/HEAD` for `ref: refs/heads/<branch>`. Returns the branch name, or
    None on any parse failure or detached HEAD (caller treats None as "allow").
    """
    try:
        with open(marker, "r") as f:
            content = f.read()
    except Exception:
        return None
    gitdir = None
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("gitdir:"):
            gitdir = line[len("gitdir:"):].strip()
            break
    if not gitdir:
        return None
    head_path = os.path.join(gitdir, "HEAD")
    try:
        with open(head_path, "r") as f:
            head = f.read().strip()
    except Exception:
        return None
    prefix = "ref: refs/heads/"
    if head.startswith(prefix):
        return head[len(prefix):].strip()
    return None  # detached HEAD or unrecognized -- do not block


def main():
    if os.environ.get("CLAUDE_WORKTREE_GATE", "1") == "0":
        _allow()

    try:
        data = json.load(sys.stdin)
    except Exception:
        _allow()  # never block on malformed input

    if data.get("tool_name", "") not in ("Edit", "Write"):
        _allow()

    file_path = (data.get("tool_input") or {}).get("file_path", "")
    if not file_path:
        _allow()

    abs_path = os.path.realpath(os.path.expanduser(file_path))

    # ~/.claude config must always be editable (this hook, rules, settings).
    claude_home = os.path.realpath(os.path.expanduser("~/.claude"))
    if abs_path == claude_home or abs_path.startswith(claude_home + os.sep):
        _allow()

    repo_root, marker = _enclosing_git_marker(_nearest_existing_dir(abs_path))
    if marker is None:
        _allow()  # not inside a git repo -- worktrees do not apply
    if os.path.isfile(marker):
        # Linked worktree (.git is a file) -- already isolated from the primary
        # checkout. But still block edits when the worktree itself is sitting on
        # the main/master branch: feature work belongs on a feature branch.
        branch = _worktree_branch(marker)
        if branch in ("main", "master"):
            _deny(
                "On-main guard: this worktree is on '{branch}'. Editing on the "
                "main branch is blocked -- create/switch to a feature branch "
                "first (`git checkout -b mohammad/<name> origin/main`).".format(
                    branch=branch
                )
            )
        _allow()

    # `.git` is a directory => primary checkout. Block.
    rel = os.path.relpath(abs_path, repo_root)
    _deny(
        "Worktree gate: '{rel}' is in the PRIMARY checkout of {root} (its main "
        "working tree), which must stay pristine for parallel tasks. Do not edit "
        "here.\n"
        "  Fix: make a worktree with the worktree skill (`create <name>`), which "
        "sets up the sub-repos on `mohammad/<name>` and switches you in; then make the "
        "change inside it. (Or EnterWorktree into an existing worktree.)\n"
        "  Bypass this session only: set CLAUDE_WORKTREE_GATE=0.".format(
            rel=rel, root=repo_root
        )
    )


if __name__ == "__main__":
    main()
