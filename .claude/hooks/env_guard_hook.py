#!/usr/bin/env python3
"""Env secret guard: deny Read/Edit/Write of `.env` files -- they hold secrets.

Personal ~/.claude-style enforcement for the mt-devkit workspace (intentionally
NOT devkit-coupled). The worktree copies each sub-repo's `.env` into every
worktree and those files hold API keys; this hook keeps them out of the agent's
context, out of edits, and -- combined with `.env*` already being gitignored --
off any commit or PR.

The real leak vector is READING a full `.env` into context (secrets then live in
the transcript), so this gates `Read` as well as `Edit`/`Write`. It does NOT gate
Bash: `grep VAR .env` / `sed` surface a single line, not the whole file, which is
the intended line-scoped access (see the env-manager skill's `REEVO_BACKEND_PATH`
sed).

Match: basename `.env` exactly, or anything starting with `.env.` (`.env.local`,
`.env.test`). A trailing-dot is required -- `.environment` and `foo.env` are NOT
matched, matching devkit's edit_guard_hook `check_env_file`.

Allow (gate does not fire) when:
  - CLAUDE_ENV_GUARD=0    per-session escape hatch
  - tool is not Read/Edit/Write, or there is no file_path
  - basename is not a `.env` file

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


def _is_env_file(basename):
    return basename == ".env" or basename.startswith(".env.")


def main():
    if os.environ.get("CLAUDE_ENV_GUARD", "1") == "0":
        _allow()

    try:
        data = json.load(sys.stdin)
    except Exception:
        _allow()  # never block on malformed input

    if data.get("tool_name", "") not in ("Read", "Edit", "Write"):
        _allow()

    file_path = (data.get("tool_input") or {}).get("file_path", "")
    if not file_path:
        _allow()

    if not _is_env_file(os.path.basename(file_path)):
        _allow()

    _deny(
        "Env guard: '{name}' is a .env file -- it holds API keys/secrets, so "
        "reading it into context, editing, or writing it is blocked (secrets "
        "would leak into the transcript, a commit, or a PR).\n"
        "  Need one value? Read a single line via Bash instead: "
        "`grep '^VAR=' {path}` -- line-scoped access is fine, full-file access "
        "is not.\n"
        "  Bypass this session only: set CLAUDE_ENV_GUARD=0.".format(
            name=os.path.basename(file_path), path=file_path
        )
    )


if __name__ == "__main__":
    main()
