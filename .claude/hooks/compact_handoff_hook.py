#!/usr/bin/env python3
"""Compact handoff: after a compaction, point the session back at its handoff.

`handoff-session` (default mode) writes a living handoff for a session that keeps
running, plus a pointer file at ~/.claude/tmp/handoffs/.sessions/<session_id> holding
the handoff's path. Compaction keeps the session id, so on SessionStart with
source "compact" this hook finds that pointer and injects "read <handoff> first"
as additional context -- the auto-summary drops environment details and rules
set mid-session, and the handoff is where they survive.

No pointer, a pointer to a missing file, or any other source -> no output, so a
session that never wrote a handoff is untouched.

MT_HANDOFF_POINTER_DIR overrides the pointer directory (the probe uses it).

Runs under /usr/bin/python3 (macOS system Python 3.9): keep 3.9-compatible.
"""
import json
import os
import sys

POINTER_DIR = os.environ.get(
    "MT_HANDOFF_POINTER_DIR", os.path.expanduser("~/.claude/tmp/handoffs/.sessions"))


def main():
    payload = json.load(sys.stdin)
    if payload.get("source") != "compact":
        return
    session_id = payload.get("session_id") or ""
    pointer = os.path.join(POINTER_DIR, os.path.basename(session_id))
    if not session_id or not os.path.isfile(pointer):
        return
    with open(pointer) as f:
        handoff = f.read().strip()
    if not os.path.isfile(handoff):
        return
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": (
            "This session was just compacted. Before anything else, read its handoff "
            "`" + handoff + "` in full: it holds the environment, the rules the user set "
            "(verbatim -- they still bind), what is blocked on the user, and the next step. "
            "Resume from its Next steps; refresh it with `handoff-session` as "
            "work moves on."),
    }}))


if __name__ == "__main__":
    main()
