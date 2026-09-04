#!/usr/bin/env python3
"""KB write gate: knowledge-base changes must be seen before they land.

The knowledge base is gitignored, so a change to it leaves no diff, no PR and no
history -- nothing after the fact will ever show that an entry was rewritten. The
requirement is therefore awareness at write time: Mohammad sees every modification
as it happens, or it doesn't happen.

WHY THIS GATES Bash AND NOT Edit/Write
--------------------------------------
It used to match Edit|Write. That never fired, because the store lives in the
primary checkout and is symlinked into each worktree, and *three* separate guards
-- Claude Code's built-in session isolation, worktree_gate_hook, and the
background-isolation guard -- all resolve the symlink, see the primary checkout,
and refuse an Edit/Write from a worktree session. They are right to: if a symlink
could be followed into the primary, worktree isolation would be one `ln -s` away
from meaningless. The store was consequently unwritable from anywhere.

So the `kb` skill writes through the shell instead, which those guards do not
police, and this gate moved with it.

WHAT IT CAN AND CANNOT SEE
--------------------------
Recognising "this arbitrary shell command writes to the KB" is not decidable --
`cat >`, `tee`, `sed -i`, a heredoc into python, an editor, all look different.
So this does NOT try. It matches a path mentioning `knowledge-base` alongside one
of a known set of write operators. That reliably catches the `kb` skill, whose
write shape we control, plus the obvious hand-rolled cases.

It will miss an exotic write. That is accepted and worth stating plainly: this is
a backstop, not a wall. The behaviour is produced by the `kb` skill and the
`doc-edit-diff-first` rule; losing the backstop degrades that rather than
breaking it.

Runs under /usr/bin/python3 (macOS system Python 3.9): keep 3.9-compatible
(no PEP 604 unions, no match/case).
"""
from __future__ import annotations

import json
import re
import sys

# Kept identical to the constant of the same name in worktree_gate_hook.py.
KB_DIR_SEGMENT = "knowledge-base"

# Write operators worth recognising. Read-only commands (grep/ls/cat-without-
# redirect) deliberately do not appear -- reading the store is free.
WRITE_PATTERNS = (
    r">\s*\S*" + KB_DIR_SEGMENT,           # cat > kb/... , >> kb/...
    KB_DIR_SEGMENT + r"\S*\s*<<",           # heredoc into a kb path
    r"\btee\b[^|]*" + KB_DIR_SEGMENT,       # tee kb/...
    r"\bsed\b[^|]*-i[^|]*" + KB_DIR_SEGMENT,
    r"\b(cp|mv|rm|mkdir|touch|ln)\b[^|]*" + KB_DIR_SEGMENT,
    r"\bpython3?\b[^|]*" + KB_DIR_SEGMENT,  # a script that names a kb path
)


def _allow():
    # Emit nothing and exit 0: no decision, so other hooks / normal permissions
    # still apply. The gate only ever *adds* a decision; it never forces an allow.
    sys.exit(0)


def _ask(reason):
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
    )
    sys.exit(0)


def _looks_like_kb_write(command):
    if KB_DIR_SEGMENT not in command:
        return False
    return any(re.search(p, command) for p in WRITE_PATTERNS)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        _allow()  # never block on malformed input

    if data.get("tool_name", "") != "Bash":
        _allow()

    command = (data.get("tool_input") or {}).get("command", "") or ""
    if not _looks_like_kb_write(command):
        _allow()

    _ask(
        "KB write gate: this writes to the knowledge base, which is gitignored -- "
        "nothing after the fact will show it changed, so it gets confirmed now.\n"
        "  Before applying, show the change as a fenced ```diff block "
        "(- old, + new), then apply what was agreed.\n"
        "  The `kb` skill does this for you and owns the index-line and one-page "
        "rules; prefer it over a hand-rolled write."
    )


if __name__ == "__main__":
    main()
