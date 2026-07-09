#!/usr/bin/env python3
"""Allow-by-default command guard + secret guard (PreToolUse: Bash|Read|Edit|Write).

Philosophy: allow everything except a small, curated set of dangerous shapes.
This replaces the earlier prove-then-allow hook, which prompted on everything it
couldn't positively prove safe -> constant interruptions. Here the default is
ALLOW, and a hook `allow` decision blankets over ALL of Claude Code's built-in
Bash structural guards (cd&&git, $VAR, cd-with-redirect, brace-with-quote) at
once -- so those never prompt. Safety lives entirely in the deny/ask lists below.

Outcomes (strictest wins across a compound command; deny > ask > allow):
  - deny  -> hard block.
  - ask   -> emit nothing -> the normal prompt appears (the pressure valve).
  - allow -> emit allow -> runs with no prompt, built-in guards suppressed.

Bash: allow-by-default; ask/deny only for the curated patterns (network->shell,
  sudo/eval, destructive git, recursive rm, gh merge/review, raw-disk writes,
  and whole-file secret dumps like `cat .env`). `bash -c`/`zsh -ic` payloads are
  classified recursively, so env-manager aliases (`zsh -ic 'kill-be-f'`) stay
  allowed while `bash -c "rm -rf ~"` is caught. Line-scoped secret reads
  (`grep VAR .env`, `sed`) stay allowed -- that's env-manager's legit access.
Read/Edit/Write: hands-off (emit nothing, so native permissions + the worktree
  gate keep working) EXCEPT secret files (.env, keys) -> deny. This subsumes the
  separate env-guard.

permissions.deny (rm -rf /, force-push) stays the native hard floor -- Claude
Code evaluates deny over a hook allow, so it still applies.

Fail-safe: any error -> emit nothing -> normal prompt (a bug degrades to
prompting, never to silently allowing something dangerous).

Bypass: MT_GUARD=0.

Runs under /usr/bin/python3 (macOS system Python 3.9): keep 3.9-compatible
(no PEP 604 unions, no match/case).
"""
from __future__ import annotations

import json
import os
import re
import shlex
import sys

ALLOW, ASK, DENY = "allow", "ask", "deny"
_RANK = {ALLOW: 0, ASK: 1, DENY: 2}

# Decision applied to secret-file access (Read/Edit/Write of a secret, or a
# whole-file dump like `cat .env`). DENY hard-blocks reading secrets into the
# transcript; flip to ASK for a prompt instead.
_SECRET_DECISION = DENY


def _emit(decision, reason):
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": decision,
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
    )
    sys.exit(0)


def _nothing():
    # Emit no decision -> normal permission flow (prompt / native rules) applies.
    sys.exit(0)


# --------------------------------------------------------------------------- #
# Secret-file detection -- shared by Bash tokens and Read/Edit/Write file paths
# --------------------------------------------------------------------------- #
# `.env`, `.env.local`, `.env.test` are secrets; `.env.example`/`.env.sample`/
# `.environment`/`foo.env` are not.
_ENV_RE = re.compile(
    r"^\.env(\.(?!example$|sample$|template$|dist$|defaults$)[A-Za-z0-9_.-]+)?$"
)
_KEY_BASENAME_RE = re.compile(r"^id_(rsa|dsa|ecdsa|ed25519)$")


def _is_secret_path(path):
    if not path:
        return False
    p = os.path.expanduser(os.path.expandvars(path)).replace("\\", "/")
    base = os.path.basename(p.rstrip("/"))
    if _ENV_RE.match(base):
        return True
    if _KEY_BASENAME_RE.match(base):
        return True
    if base.endswith(".pem") or base.endswith(".key"):
        return True
    if "/.ssh/" in p or p.endswith("/.ssh"):
        return True
    if "/.aws/credentials" in p or "/.gnupg/" in p:
        return True
    return False


# --------------------------------------------------------------------------- #
# Bash classification
# --------------------------------------------------------------------------- #
_SHELL_INTERPRETERS = {"bash", "sh", "zsh", "dash", "ksh"}
# Tools that dump a whole file to stdout -- reading a secret with one of these
# leaks it into the transcript. Line-scoped tools (grep/sed/awk/head/tail) are
# excluded on purpose: they surface a single line and are env-manager's legit
# way to read one value out of a .env.
_WHOLE_FILE_READERS = {"cat", "less", "more", "bat", "view", "xxd", "od", "strings", "nl", "tac"}

# curl/wget piped straight into a shell/interpreter -- the classic RCE vector.
_NET_SHELL_RE = re.compile(
    r"\b(?:curl|wget|fetch)\b[^|]*\|\s*(?:sudo\s+)?"
    r"(?:bash|sh|zsh|dash|python3?|node|perl|ruby)\b"
)
# `$(curl ...)` / `` `curl ...` `` used as a command source.
_SUBST_NET_RE = re.compile(r"[$`]\(?[^)]*\b(?:curl|wget|fetch)\b")
# Writing to a raw disk device -- catastrophic, never legitimate here.
_DISK_WRITE_RE = re.compile(r">\s*/dev/(?:sd[a-z]|disk\d|nvme\d|rdisk\d|hd[a-z])")
_DD_DEVICE_RE = re.compile(r"of=/dev/(?:sd[a-z]|disk\d|nvme\d|rdisk\d|hd[a-z])")


def _split_segments(command):
    """Split into segments on &&, ||, ;, |, and newlines (same approach as the
    branch guard) so each invocation's leading binary can be inspected."""
    tmp = command.replace("\n", ";")
    for op in ("&&", "||"):
        tmp = tmp.replace(op, ";")
    tmp = tmp.replace("|", ";")
    return [s.strip() for s in tmp.split(";") if s.strip()]


def _real_binary(tokens):
    """First token that is the actual command, skipping leading `VAR=val` inline
    env assignments (e.g. `CLAUDE_ENV_GUARD=0 bash -c ...`). Returns (name, args)
    or (None, [])."""
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if "=" in t and not t.startswith("-") and "/" not in t.split("=", 1)[0]:
            i += 1
            continue
        return os.path.basename(t), tokens[i + 1:]
    return None, []


def _dash_c_payload(args):
    """Return the payload string of a `-c`/`-ic`/`-lc` shell flag, or None."""
    for i, a in enumerate(args):
        if a.startswith("-") and "c" in a.lstrip("-") and not a.startswith("--"):
            return args[i + 1] if i + 1 < len(args) else None
    return None


def _classify_git(args):
    rest = [a for a in args if a not in ("--no-pager",)]
    sub = next((a for a in rest if not a.startswith("-")), None)
    if sub == "push":
        if "--no-verify" in rest or "--force" in rest or "-f" in rest:
            return ASK
        if any(a in ("main", "master") for a in rest):
            return ASK
        return ALLOW
    if sub == "reset" and "--hard" in rest:
        return ASK
    if sub == "clean" and any(a.startswith("-") and "f" in a for a in rest):
        return ASK
    return ALLOW


def _classify_gh(args):
    if len(args) >= 2 and args[0] == "pr":
        if args[1] in ("merge", "review"):
            return ASK
        if args[1] == "edit" and any(
            a in ("--add-reviewer", "--reviewer") for a in args
        ):
            return ASK
    return ALLOW


def _classify_segment(tokens, depth):
    if not tokens:
        return ALLOW

    binary, args = _real_binary(tokens)
    if binary is None:
        return ALLOW

    if binary in _WHOLE_FILE_READERS and any(_is_secret_path(a) for a in args):
        return _SECRET_DECISION

    if binary in _SHELL_INTERPRETERS and depth < 4:
        payload = _dash_c_payload(args)
        if payload is not None:
            return _classify_command(payload, depth + 1)
        # `bash script.sh` (a script file, not -c) -- running arbitrary code.
        if args and not args[0].startswith("-"):
            return ASK
        return ALLOW

    if binary in ("eval", "sudo", "doas"):
        return ASK
    if binary == "mkfs" or binary.startswith("mkfs."):
        return DENY
    if binary == "dd":
        return DENY if any(_DD_DEVICE_RE.match(a) for a in args) else ASK
    if binary == "shred":
        return ASK
    if binary == "rm":
        if "--recursive" in args or any(
            a.startswith("-") and not a.startswith("--") and ("r" in a or "R" in a)
            for a in args
        ):
            return ASK
        return ALLOW
    if binary == "git":
        return _classify_git(args)
    if binary == "gh":
        return _classify_gh(args)
    return ALLOW


def _classify_command(command, depth=0):
    if _DISK_WRITE_RE.search(command):
        return DENY
    if _NET_SHELL_RE.search(command) or _SUBST_NET_RE.search(command):
        return ASK
    worst = ALLOW
    for seg in _split_segments(command):
        try:
            tokens = shlex.split(seg)
        except Exception:
            # Unparseable quoting -- the command-level regexes above already ran,
            # so default this segment to allow rather than prompt on every odd
            # quote. Rare, and keeps friction down.
            continue
        d = _classify_segment(tokens, depth)
        if _RANK[d] > _RANK[worst]:
            worst = d
        if worst == DENY:
            break
    return worst


# --------------------------------------------------------------------------- #
# Entry
# --------------------------------------------------------------------------- #
def _run():
    if os.environ.get("MT_GUARD", "1") == "0":
        _nothing()

    try:
        data = json.load(sys.stdin)
    except Exception:
        _nothing()

    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input") or {}

    if tool == "Bash":
        command = tool_input.get("command", "")
        if not command:
            _nothing()
        decision = _classify_command(command)
        if decision == DENY:
            _emit(DENY, "Blocked: raw-disk destruction or whole-file secret read.")
        if decision == ASK:
            _nothing()  # surface the normal prompt
        _emit(ALLOW, "allow-by-default ACL")

    if tool in ("Read", "Edit", "Write", "NotebookEdit"):
        path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
        if _is_secret_path(path):
            if _SECRET_DECISION == DENY:
                _emit(DENY, "Blocked by ACL: secret file (.env / key material).")
            _nothing()  # ASK -> normal prompt on the secret file
        _nothing()  # non-secret file tool: hands off to native permissions

    _nothing()


def main():
    try:
        _run()
    except SystemExit:
        raise
    except Exception:
        # A hook bug must never block a tool: fail open to the normal prompt flow.
        sys.exit(0)


if __name__ == "__main__":
    main()
