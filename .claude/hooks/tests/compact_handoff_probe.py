#!/usr/bin/env python3
"""Probe for compact_handoff_hook.py -- run it, don't reason about it.

    /usr/bin/python3 .claude/hooks/tests/compact_handoff_probe.py

Feeds real SessionStart payloads to the hook as a subprocess, against a scratch
pointer directory (MT_HANDOFF_POINTER_DIR), and asserts whether it injects the
handoff path. Exits non-zero on the first mismatch.
"""
import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir, "compact_handoff_hook.py"))


def run(pointer_dir, payload):
    env = dict(os.environ, MT_HANDOFF_POINTER_DIR=pointer_dir)
    out = subprocess.run([sys.executable, HOOK], input=json.dumps(payload),
                         capture_output=True, text=True, env=env, check=True).stdout
    return json.loads(out) if out.strip() else None


def main():
    with tempfile.TemporaryDirectory() as tmp:
        pointers = os.path.join(tmp, "sessions")
        os.makedirs(pointers)
        handoff = os.path.join(tmp, "topic.md")
        with open(handoff, "w") as f:
            f.write("# handoff\n")
        with open(os.path.join(pointers, "s-live"), "w") as f:
            f.write(handoff + "\n")
        with open(os.path.join(pointers, "s-stale"), "w") as f:
            f.write(os.path.join(tmp, "gone.md"))

        cases = [
            ("compact with pointer injects", {"source": "compact", "session_id": "s-live"}, True),
            ("startup is ignored", {"source": "startup", "session_id": "s-live"}, False),
            ("resume is ignored", {"source": "resume", "session_id": "s-live"}, False),
            ("no pointer stays silent", {"source": "compact", "session_id": "s-none"}, False),
            ("pointer to a missing file stays silent", {"source": "compact", "session_id": "s-stale"}, False),
            ("no session id stays silent", {"source": "compact"}, False),
        ]
        for name, payload, expect in cases:
            out = run(pointers, dict(payload, hook_event_name="SessionStart"))
            got = out is not None and handoff in out["hookSpecificOutput"]["additionalContext"]
            if got != expect:
                print("FAIL: %s -> %r" % (name, out))
                sys.exit(1)
            print("ok: " + name)


if __name__ == "__main__":
    main()
