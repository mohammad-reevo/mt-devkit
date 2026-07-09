#!/usr/bin/env python3
"""Branch-from-main guard: deny branch-creation git commands that would branch
off a base which is not FRESH main.

Personal ~/.claude enforcement. The accident this catches: creating a new
feature branch off whatever HEAD happens to be (a stale main, or another feature
branch) instead of off fresh `origin/main`. This keeps every feature branch
rooted on current upstream main.

Scope (PreToolUse:Bash): only branch-CREATION git commands are inspected --
`git checkout -b/-B`, `git switch -c/-C`, `git branch <name>`, and
`git worktree add -b <name>`. Everything else (list/status/etc.) is allowed
untouched.

Rule per branch-creation segment:
  - Explicit start-point that names main  -> require FRESH (allow) else deny.
  - Explicit start-point that is anything else (feature branch / HEAD / SHA)
    -> ALLOW (deliberate off-non-main; the intended escape hatch).
  - No explicit start-point (off current HEAD) -> allow ONLY if current branch
    is main AND main is FRESH; else deny.

FRESH = local `refs/heads/main` equals `refs/remotes/origin/main`. We `git fetch
origin main` first (real guarantee); if that fails (offline) we fall back to the
same local comparison without fetching and note that freshness wasn't
network-verified.

On any parse error / uncertainty -> ALLOW. This guard targets the clear
accidental case; it must never false-block.

Bypass: MT_BRANCH_GUARD=0.

Runs under /usr/bin/python3 (macOS system Python 3.9): keep 3.9-compatible
(no PEP 604 unions, no match/case).
"""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys


def _allow():
    # Emit nothing and exit 0: no decision, so normal permissions still apply.
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


_MAIN_NAMES = ("main", "master")


def _main_kind(ref):
    """Classify a ref as main. Returns:
      "remote" -> a remote-tracking main (origin/main, refs/remotes/origin/main,
                  <remote>/main). Branching off this is always the sanctioned
                  fresh-main path -> allowed unconditionally.
      "local"  -> the local main branch (main, master, refs/heads/main). Needs a
                  freshness check (local main == origin/main).
      None     -> not a main ref.
    """
    if ref is None:
        return None
    r = ref.strip()
    if r.startswith("refs/heads/"):
        tail = r[len("refs/heads/"):]
        return "local" if tail in _MAIN_NAMES else None
    if r.startswith("refs/remotes/"):
        tail = r[len("refs/remotes/"):].split("/")[-1]
        return "remote" if tail in _MAIN_NAMES else None
    if "/" in r:
        # e.g. origin/main -- a remote-tracking ref.
        tail = r.split("/")[-1]
        return "remote" if tail in _MAIN_NAMES else None
    return "local" if r in _MAIN_NAMES else None


def _split_segments(command):
    """Split a shell command into segments on &&, ||, ;, |, and newlines."""
    # Replace the multi-char operators with a sentinel, then split.
    tmp = command.replace("\n", ";")
    for op in ("&&", "||"):
        tmp = tmp.replace(op, ";")
    # Single '|' and ';' as separators.
    tmp = tmp.replace("|", ";")
    return [s.strip() for s in tmp.split(";") if s.strip()]


def _strip_git_c(tokens):
    """Strip a leading `git [-C <path>]`; return (path_or_None, rest_tokens).

    Returns (None, None) if the segment is not a git invocation.
    """
    if not tokens or tokens[0] != "git":
        return None, None
    rest = tokens[1:]
    path = None
    # Skip global git options that precede the subcommand, capturing -C <path>.
    i = 0
    while i < len(rest):
        tok = rest[i]
        if tok == "-C" and i + 1 < len(rest):
            path = rest[i + 1]
            i += 2
            continue
        if tok.startswith("-C") and len(tok) > 2:
            path = tok[2:]
            i += 1
            continue
        if tok == "-c" and i + 1 < len(rest):
            # `git -c key=val` global config -- skip the pair.
            i += 2
            continue
        if tok.startswith("-"):
            # Other global option (e.g. --no-pager) -- skip it.
            i += 1
            continue
        break
    return path, rest[i:]


def _positionals(tokens):
    """Return non-flag positional args from a token list (drops any leading
    `-x`/`--x` flags; keeps everything after the first positional as-is except
    it also filters out flags interleaved between positionals)."""
    return [t for t in tokens if not t.startswith("-")]


def _parse_creation(tokens):
    """Given the tokens AFTER `git [-C path]` is stripped, decide whether this is
    a branch-creation command. Returns (name, start_point_or_None) if so, else
    None. `start_point_or_None` is the explicit start ref if one is present.
    """
    if not tokens:
        return None
    sub = tokens[0]
    args = tokens[1:]

    if sub in ("checkout", "switch"):
        create_flags = ("-b", "-B") if sub == "checkout" else ("-c", "-C")
        if not any(a in create_flags for a in args):
            return None
        # Find the create flag; the token after it is the new branch name,
        # then an optional start-point positional.
        idx = None
        for i, a in enumerate(args):
            if a in create_flags:
                idx = i
                break
        after = args[idx + 1:]
        pos = _positionals(after)
        if not pos:
            return None
        name = pos[0]
        start = pos[1] if len(pos) > 1 else None
        return (name, start)

    if sub == "branch":
        # `git branch <name> [<start>]` creates; flags-only / no positional does not.
        pos = _positionals(args)
        if not pos:
            return None  # list / -a / --list / etc.
        # Deletion / rename / copy flags are not creation.
        if any(a in ("-d", "-D", "-m", "-M", "-c", "-C", "--delete", "--move", "--copy") for a in args):
            return None
        name = pos[0]
        start = pos[1] if len(pos) > 1 else None
        return (name, start)

    if sub == "worktree":
        # `git worktree add [flags] [-b <name>] <path> [<start>]`
        if len(args) < 1 or args[0] != "add":
            return None
        add_args = args[1:]
        if not any(a in ("-b", "-B") for a in add_args):
            return None  # `worktree add <path> <branch>` w/o -b checks out existing
        # Extract -b <name>.
        name = None
        i = 0
        rest_positional = []
        while i < len(add_args):
            a = add_args[i]
            if a in ("-b", "-B") and i + 1 < len(add_args):
                name = add_args[i + 1]
                i += 2
                continue
            if a.startswith("-"):
                # Other flag (e.g. --detach, --checkout); skip lone flag.
                i += 1
                continue
            rest_positional.append(a)
            i += 1
        if name is None:
            return None
        # rest_positional = [<path>, <start>?]  -- start-point is after the path.
        start = rest_positional[1] if len(rest_positional) > 1 else None
        return (name, start)

    return None


def _git(dirpath, args, timeout=15):
    """Run `git -C dirpath <args>`; return (returncode, stdout_stripped)."""
    try:
        proc = subprocess.run(
            ["git", "-C", dirpath] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout.decode("utf-8", "replace").strip()
    except Exception:
        return 1, ""


def _is_git_repo(dirpath):
    rc, out = _git(dirpath, ["rev-parse", "--is-inside-work-tree"], timeout=10)
    return rc == 0 and out == "true"


def _local_main_matches_origin(dirpath):
    """Compare refs/heads/main to refs/remotes/origin/main. Returns True/False,
    or None if either ref can't be resolved."""
    rc1, local = _git(dirpath, ["rev-parse", "refs/heads/main"], timeout=10)
    rc2, remote = _git(dirpath, ["rev-parse", "refs/remotes/origin/main"], timeout=10)
    if rc1 != 0 or rc2 != 0 or not local or not remote:
        return None
    return local == remote


def _current_branch(dirpath):
    rc, out = _git(dirpath, ["rev-parse", "--abbrev-ref", "HEAD"], timeout=10)
    if rc != 0:
        return None
    return out


def main():
    if os.environ.get("MT_BRANCH_GUARD", "1") == "0":
        _allow()

    try:
        data = json.load(sys.stdin)
    except Exception:
        _allow()  # never block on malformed input

    if data.get("tool_name", "") != "Bash":
        _allow()

    command = (data.get("tool_input") or {}).get("command", "")
    if not command or "git" not in command:
        _allow()

    # Collect all branch-creation segments (with their optional -C path).
    creations = []
    for seg in _split_segments(command):
        try:
            tokens = shlex.split(seg)
        except Exception:
            continue  # unparseable segment -- ignore (never false-block)
        cpath, rest = _strip_git_c(tokens)
        if rest is None:
            continue  # not a git invocation
        parsed = _parse_creation(rest)
        if parsed is not None:
            name, start = parsed
            creations.append((name, start, cpath))

    if not creations:
        _allow()  # no branch-creation git command present

    # Evaluate each creation; deny on the first that violates the rule.
    for name, start, cpath in creations:
        repo_dir = cpath if cpath else os.getcwd()
        repo_dir = os.path.realpath(os.path.expanduser(repo_dir))

        if not _is_git_repo(repo_dir):
            continue  # can't evaluate -> allow this segment

        # Case 1: explicit start-point present.
        if start is not None:
            kind = _main_kind(start)
            if kind is None:
                continue  # deliberate off-non-main (feature/HEAD/SHA) -> allow
            if kind == "remote":
                # origin/main is the sanctioned base -- fetch first so the branch
                # is off *freshly-fetched* main (a real guarantee), then allow.
                # (Offline: fetch is a no-op; branch off last-known origin/main.)
                _git(repo_dir, ["fetch", "origin", "main"])
                continue
            # kind == "local": branching off LOCAL main -> require FRESH.
            _require_fresh_local_main(repo_dir, name)
            continue

        # Case 2: no explicit start-point -> off current HEAD.
        cur = _current_branch(repo_dir)
        if cur is None or _main_kind(cur) != "local":
            _deny(_deny_msg(name, note=None))
        # Current branch is main -> require FRESH.
        _require_fresh_local_main(repo_dir, name)

    _allow()


def _require_fresh_local_main(repo_dir, name):
    """Deny unless local main == origin/main. Fetches first for a real
    guarantee; on offline fetch failure falls back to the local comparison and
    notes the caveat. Uncertainty (unresolvable refs) -> allow (never
    false-block). Returns normally when allowed; calls _deny() otherwise."""
    rc, _ = _git(repo_dir, ["fetch", "origin", "main"])
    match = _local_main_matches_origin(repo_dir)
    if match is None or match:
        return  # fresh, or can't resolve -> allow
    note = None if rc == 0 else _OFFLINE_NOTE
    _deny(_deny_msg(name, note=note))


_OFFLINE_NOTE = (
    " (Note: could not reach origin to network-verify freshness; compared local "
    "main to the last-known origin/main only.)"
)


def _deny_msg(name, note):
    base = (
        "Branch-from-main guard: '{name}' would be created off a base that isn't "
        "fresh main. Branch off fresh main: `git checkout -b {name} origin/main` "
        "-- or name a start-point explicitly if you deliberately want to branch "
        "off this branch.".format(name=name)
    )
    if note:
        base += note
    return base


if __name__ == "__main__":
    main()
