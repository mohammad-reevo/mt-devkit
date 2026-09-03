#!/usr/bin/env python3
"""KB write gate: knowledge-base edits must be seen before they land.

The knowledge base (`knowledge-base/`) is gitignored, so a change to it leaves no
diff, no PR, and no history -- nothing after the fact will ever show that an entry
was rewritten. The requirement is therefore awareness at write time: Mohammad sees
every modification as it happens, or it doesn't happen.

That is what this gate enforces. It does not try to stop a determined write (a
`cat >` through Bash is not covered, same as every other gate here); it makes a
silent, incidental edit impossible, which is the actual failure mode.

The sanctioned path is the `kb` skill: it shows a fenced red/green diff, waits for
a yes, and only then writes. See `doc-edit-diff-first.md` for the general rule --
this hook is the KB-specific enforcement of it.

Gate fires only when BOTH hold:
  - tool is Edit or Write
  - target path has `knowledge-base` as a path SEGMENT (so it fires in worktrees
    too, not just the primary checkout)

Decision is "ask", not "deny": the point is a visible confirmation, not a wall.
A deny would also block the `kb` skill itself, leaving no way in at all.

Runs under /usr/bin/python3 (macOS system Python 3.9): keep 3.9-compatible
(no PEP 604 unions, no match/case).
"""
from __future__ import annotations

import json
import os
import sys

# An edit whose path has this as a segment is knowledge-base content.
KB_DIR_SEGMENT = "knowledge-base"


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


def _in_knowledge_base(file_path):
    segments = os.path.normpath(file_path).split(os.sep)
    return KB_DIR_SEGMENT in segments


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        _allow()  # never block on malformed input

    tool_name = data.get("tool_name", "")
    if tool_name not in ("Edit", "Write"):
        _allow()

    tool_input = data.get("tool_input") or {}
    file_path = tool_input.get("file_path", "")
    if not file_path:
        _allow()

    if not _in_knowledge_base(file_path):
        _allow()

    _ask(
        "KB write gate: '{name}' is knowledge-base content, which is gitignored -- "
        "nothing after the fact will show this changed, so it gets confirmed now.\n"
        "  Before applying, show the change as a fenced ```diff block "
        "(- old, + new), then apply what was agreed.\n"
        "  The `kb` skill does this for you and owns the index-line and one-page "
        "rules; prefer it over a hand-edit.".format(name=os.path.basename(file_path))
    )


if __name__ == "__main__":
    main()
