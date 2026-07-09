#!/usr/bin/env python3
"""Implementer gate: product-repo code edits must go through the implementer subagent.

Personal ~/.claude-style enforcement for the mt-devkit workspace. The orchestrator
must not hand-edit product-repo code -- it delegates to a dispatched `implementer`
subagent so raw code / check output stays out of main context. This covers both
the funnel (implement dispatches implementer per task) and the plan-less /
post-implementation cases (a follow-up tweak, a revision after the plan shipped),
where no skill is driving the dispatch.

Detection: a subagent's tool call carries `agent_type` in the PreToolUse payload;
the orchestrator's does not (the field is absent, not null). We allow only when
`agent_type == "implementer"` -- so any orchestrator edit, and any other agent, is
gated. Requiring the specific type makes the gate immune to how the orchestrator
itself is labelled (absent vs. "claude" in a background job): it simply isn't
"implementer", so it's gated.

Gate fires (deny) only when ALL hold:
  - tool is Edit or Write
  - target path is inside a product sub-repo (by path SEGMENT, so it fires in
    worktrees too, not just the primary checkout)
  - the caller is not the implementer (agent_type != "implementer")
  - the edit adds >= FLOOR new lines (trivial edits pass)

No escape hatch, floor hardcoded: this is single-user tooling.

Runs under /usr/bin/python3 (macOS system Python 3.9): keep 3.9-compatible
(no PEP 604 unions, no match/case).
"""
from __future__ import annotations

import json
import os
import sys

# Product sub-repos (gitignored siblings). An edit whose path has any of these as
# a segment is product code and must go through the implementer.
PRODUCT_SUBREPOS = (
    "salestech-be",
    "frontend-monorepo",
    "reevo-realtime",
    "harvey-the-slack-bot",
)

# Orchestrator edits adding >= this many new lines to product code are denied.
# Below it, trivial edits pass. Hardcoded (single-user tooling, no env override).
FLOOR = 30


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


def _in_product_subrepo(file_path):
    # Match by path segment so both the primary checkout
    # (.../mt-devkit/salestech-be/...) and worktrees
    # (.../worktrees/foo/salestech-be/...) are covered.
    segments = os.path.normpath(file_path).split(os.sep)
    return any(repo in segments for repo in PRODUCT_SUBREPOS)


def _new_line_count(tool_name, tool_input):
    if tool_name == "Write":
        text = tool_input.get("content", "") or ""
    else:  # Edit
        text = tool_input.get("new_string", "") or ""
    if not text:
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)


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

    if not _in_product_subrepo(file_path):
        _allow()  # harness / spec / plan / task files: orchestrator edits directly

    if data.get("agent_type") == "implementer":
        _allow()  # the implementer doing its job

    if _new_line_count(tool_name, tool_input) < FLOOR:
        _allow()  # trivial edit -- inline is fine

    _deny(
        "Implementer gate: editing product-repo code ('{name}') from the main "
        "thread is blocked -- product code goes through the implementer subagent "
        "so raw code and check output stay out of your context.\n"
        "  Dispatch it:  subagent_type: implementer -- \"<the change>. "
        "Files: {path}\". It reads the source, makes the change, runs the checks, "
        "and reports lean.\n"
        "  (Edits under {floor} new lines pass inline; this one is larger.)".format(
            name=os.path.basename(file_path), path=file_path, floor=FLOOR
        )
    )


if __name__ == "__main__":
    main()
