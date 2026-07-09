#!/usr/bin/env python3
"""Scoped auto-approve: grant the permission the allowlist would already give,
for commands that only prompt because of Claude Code's built-in structural
guardrails (`cd <dir> && git ...`, `$VAR` expansion) -- but ONLY when the command
stays inside my own workspace.

Why this exists: mt-devkit's migration dropped devkit's acl-hook in favour of
native `permissions.allow`. Native permissions can't silence two built-in
guardrails that fire *before* the allowlist is consulted -- the `cd`-into-another
-dir-then-`git` warning (git can run that dir's hooks) and the `simple_expansion`
prompt on any `$VAR`. Both halt the session on commands I run constantly and
always approve (env-manager `check *`, worktree git inspection, `$CLAUDE_JOB_DIR`
temp writes). This hook recovers the "don't prompt me inside my own dirs"
behaviour as a thin, native slice -- not a port of the 1000-line ACL engine.

The decision (emit `allow` ONLY if ALL hold; otherwise emit nothing and let the
normal prompt flow decide -- deferring is always safe, it just returns to default
behaviour):
  1. Every binary invoked is already in `permissions.allow` as `Bash(<name>:*)`.
     The allowlist stays the single source of trust -- `rm`/`curl`/unknown
     binaries aren't in it, so they still prompt. Add a binary there and this
     hook honours it automatically.
  2. The effective working directory (after walking any `cd` chain), every `cd`
     target, every `git -C` target, and every output-redirect (`>`/`>>`) target
     resolves inside a trust root: ~/Desktop/code or ~/.claude.
  3. No command substitution (`$(...)`/backticks) and no unresolvable `$VAR`
     remains in any path we check -- if we can't prove where a path points, we
     can't prove it's in-boundary, so we defer.

This hook NEVER emits `deny` -- it only ever *adds* an allow. The `permissions
.deny` floor (force-push, `rm -rf ~`) and the branch-from-main guard still apply:
Claude Code evaluates deny over a hook allow, so those remain enforced.

Bypass: MT_AUTOAPPROVE=0.

Runs under /usr/bin/python3 (macOS system Python 3.9): keep 3.9-compatible
(no PEP 604 unions, no match/case).
"""
from __future__ import annotations

import json
import os
import re
import shlex
import sys


def _defer():
    # Emit nothing and exit 0: no decision, so the normal permission flow
    # (allowlist + built-in guards + prompt) still applies. This is the safe
    # fallback for any uncertainty -- it never grants more than default.
    sys.exit(0)


def _allow(reason):
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
    )
    sys.exit(0)


def _claude_dir():
    """The `.claude/` dir this hook lives in (…/.claude/hooks/<me>.py)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_allowlist_binaries():
    """Union of `Bash(<name>…)` binary names across settings.json and
    settings.local.json. The allowlist is the single source of which binaries
    are trusted; this hook reuses it rather than maintaining a second list."""
    bins = set()
    for fname in ("settings.json", "settings.local.json"):
        path = os.path.join(_claude_dir(), fname)
        try:
            with open(path) as f:
                data = json.load(f)
        except Exception:
            continue  # missing/malformed settings -> just contribute nothing
        allow = ((data.get("permissions") or {}).get("allow")) or []
        for rule in allow:
            if not isinstance(rule, str) or not rule.startswith("Bash("):
                continue
            inner = rule[len("Bash("):]
            if inner.endswith(")"):
                inner = inner[:-1]
            # Binary name is the token before the first ':' or whitespace, e.g.
            # "Bash(git:*)" -> git, "Bash(git diff:*)" -> git.
            name = re.split(r"[:\s]", inner, 1)[0].strip()
            if name:
                bins.add(os.path.basename(name))
    return bins


def _trust_roots():
    home = os.path.expanduser("~")
    return [
        os.path.normpath(os.path.join(home, "Desktop", "code")),
        os.path.normpath(os.path.join(home, ".claude")),
    ]


def _resolve(path, cwd):
    """Expand ~ and env vars, resolve relative to cwd, normalize. Returns the
    absolute normalized path, or None if an unresolvable `$` remains (an
    undefined variable -> we can't prove where it points)."""
    p = os.path.expanduser(os.path.expandvars(path))
    if "$" in p:
        return None  # undefined variable -- can't prove where it points
    # Globs / brace expansion / xargs `{}` placeholders resolve to a runtime path
    # we can't know statically (e.g. `git -C {}` fed by an xargs pipe) -> defer.
    if any(ch in p for ch in "{}*?[") :
        return None
    if not os.path.isabs(p):
        p = os.path.join(cwd, p)
    return os.path.normpath(p)


def _in_roots(abspath, roots):
    for root in roots:
        if abspath == root or abspath.startswith(root + os.sep):
            return True
    return False


def _split_segments(command):
    """Split a shell command into segments on &&, ||, ;, |, and newlines. Same
    approach as the branch guard: good enough to isolate each invocation's
    leading binary; anything it mis-splits fails a later shlex/allowlist check
    and defers."""
    tmp = command.replace("\n", ";")
    for op in ("&&", "||"):
        tmp = tmp.replace(op, ";")
    tmp = tmp.replace("|", ";")
    return [s.strip() for s in tmp.split(";") if s.strip()]


def _git_c_dir(tokens):
    """Return the `-C <path>` dir of a `git` invocation (last one wins), or None.
    Only meaningful when tokens[0] == 'git'."""
    path = None
    i = 1
    n = len(tokens)
    while i < n:
        tok = tokens[i]
        if tok == "-C" and i + 1 < n:
            path = tokens[i + 1]
            i += 2
            continue
        if tok.startswith("-C") and len(tok) > 2:
            path = tok[2:]
            i += 1
            continue
        if tok == "-c" and i + 1 < n:
            i += 2  # `git -c key=val` global config pair
            continue
        if tok.startswith("-"):
            i += 1
            continue
        break  # first non-global-option token = the subcommand
    return path


_REDIR_RE = re.compile(r"^(?:\d*|&)?>>?(.*)$")


def _redirect_targets(tokens):
    """Extract output-redirect (`>`,`>>`,`2>`,`&>`,`1>`) file targets. Returns
    (targets, ok); ok=False when a redirect is present but its target can't be
    confidently extracted (caller then defers rather than risk missing an
    out-of-boundary write). fd duplications like `2>&1` are not files -> skipped.
    Input redirects (`<`) are ignored: reads are already covered by the binary
    being allowlisted."""
    targets = []
    i = 0
    n = len(tokens)
    while i < n:
        t = tokens[i]
        if t in (">", ">>", "1>", "2>", "&>", ">|"):
            if i + 1 >= n:
                return targets, False
            targets.append(tokens[i + 1])
            i += 2
            continue
        if ">" in t:
            m = _REDIR_RE.match(t)
            if not m:
                return targets, False  # a '>' we don't understand -> be safe
            rest = m.group(1)
            if rest == "":
                if i + 1 >= n:
                    return targets, False
                targets.append(tokens[i + 1])
                i += 2
                continue
            if rest.startswith("&"):
                i += 1  # fd dup (e.g. 2>&1) -- not a file
                continue
            targets.append(rest)
            i += 1
            continue
        i += 1
    return targets, True


def _is_allowed(command, cwd, allow_bins, roots):
    """True iff every binary is allowlisted AND every effective cwd / cd target /
    git -C target / output-redirect target is inside a trust root, with no
    unresolvable expansion. Conservative: any doubt -> False (defer)."""
    if "$(" in command or "`" in command:
        return False  # command substitution -- can't statically verify
    if "{}" in command:
        return False  # xargs/find `{}` placeholder -- subcommand target is
        # runtime-determined (e.g. `xargs -I {} git -C {} …`), can't be placed
    if "$" in os.path.expandvars(command):
        return False  # an undefined variable remains -- can't prove what the
        # command does or where it points, so fall back to a prompt

    eff_cwd = os.path.normpath(cwd) if cwd else os.getcwd()

    for seg in _split_segments(command):
        try:
            tokens = shlex.split(seg)
        except Exception:
            return False
        if not tokens:
            continue

        binary = tokens[0]

        if binary == "cd":
            if len(tokens) >= 2:
                nxt = _resolve(tokens[1], eff_cwd)
                if nxt is None:
                    return False
                eff_cwd = nxt
            else:
                eff_cwd = os.path.expanduser("~")
            continue

        if os.path.basename(binary) not in allow_bins:
            return False  # not an allowlisted binary -> let normal flow prompt

        # The dir this command actually runs in must be inside my workspace
        # (this is the cd-into-untrusted-dir-then-git threat the guard targets).
        if not _in_roots(eff_cwd, roots):
            return False

        if os.path.basename(binary) == "git":
            cdir = _git_c_dir(tokens)
            if cdir is not None:
                resolved = _resolve(cdir, eff_cwd)
                if resolved is None or not _in_roots(resolved, roots):
                    return False

        targets, ok = _redirect_targets(tokens)
        if not ok:
            return False
        for tgt in targets:
            resolved = _resolve(tgt, eff_cwd)
            if resolved is None or not _in_roots(resolved, roots):
                return False

    return True


def _run():
    if os.environ.get("MT_AUTOAPPROVE", "1") == "0":
        _defer()

    try:
        data = json.load(sys.stdin)
    except Exception:
        _defer()

    if data.get("tool_name", "") != "Bash":
        _defer()

    command = (data.get("tool_input") or {}).get("command", "")
    if not command:
        _defer()

    cwd = data.get("cwd") or ""
    allow_bins = _load_allowlist_binaries()
    if not allow_bins:
        _defer()  # couldn't read the allowlist -> don't invent trust

    if _is_allowed(command, cwd, allow_bins, _trust_roots()):
        _allow("scoped auto-approve: allowlisted binaries within workspace")
    _defer()


def main():
    try:
        _run()
    except SystemExit:
        raise  # _defer()/_allow() exit 0 normally
    except Exception:
        # A hook bug must never block Bash: fail open to the normal prompt flow.
        sys.exit(0)


if __name__ == "__main__":
    main()
