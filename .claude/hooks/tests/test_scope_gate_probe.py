#!/usr/bin/env python3
"""Probe for test_scope_gate_hook.py -- run it, don't reason about it.

    /usr/bin/python3 .claude/hooks/tests/test_scope_gate_probe.py

Feeds real PreToolUse payloads to the hook as a subprocess, against a scratch tree
of test files, and asserts what it emits. Exits non-zero on the first mismatch.

Three outcomes, matching the hook's own contract:
  deny    -- hard block
  rewrite -- `updatedInput` with the worker count capped; checked against the
             expected rewritten command
  none    -- no output, so the normal permission flow applies
"""
import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir, "test_scope_gate_hook.py"))

RUN = "uv run pytest -n 2 --dist loadscope --record-mode=none --exitfirst"

# (command, expected outcome, expected rewritten command for "rewrite")
CASES = [
    # file cap
    ("uv run pytest t/test_1.py t/test_2.py t/test_3.py t/test_4.py t/test_5.py", "none", None),
    ("uv run pytest t/test_1.py t/test_2.py t/test_3.py t/test_4.py t/test_5.py t/test_6.py",
     "deny", None),
    ("uv run pytest t/test_1.py::TestX::test_y", "none", None),
    ("uv run pytest small/", "none", None),
    ("uv run pytest big/", "deny", None),
    ("uv run pytest", "deny", None),
    ("cd sub && uv run pytest ../big/", "deny", None),
    # worker cap
    ("uv run pytest -n 12 t/test_1.py", "rewrite", "uv run pytest -n 2 t/test_1.py"),
    ("uv run pytest -n auto t/test_1.py", "rewrite", "uv run pytest -n 2 t/test_1.py"),
    ("uv run pytest --numprocesses=8 t/test_1.py", "rewrite",
     "uv run pytest --numprocesses=2 t/test_1.py"),
    ("uv run pytest -n 2 t/test_1.py", "none", None),
    ("make pytest t/test_1.py", "rewrite", RUN + " t/test_1.py"),
    ("make pytest", "deny", None),
    ("make -C sub pytest ../t/test_1.py", "deny", None),
    ("PYTEST_ADDOPTS='-n 8' uv run pytest t/test_1.py", "deny", None),
    ("make pytest-k 'flow'", "deny", None),
    ("make falkor-ci", "deny", None),
    # launch forms
    ("timeout 600 uv run pytest big/", "deny", None),
    ("time python -m pytest big/", "deny", None),
    ("env FOO=1 pytest big/", "deny", None),
    ("grep -rn pytest pyproject.toml", "none", None),
    ("echo 'uv run pytest big/'", "none", None),
    # escape hatches
    ("uv run pytest --collect-only big/", "none", None),
    ("MT_TEST_SCOPE_GATE=0 uv run pytest big/", "none", None),
    ("uv run pytest --version", "none", None),
]


def make_tree(root):
    os.makedirs(os.path.join(root, "t"))
    for i in range(1, 7):
        open(os.path.join(root, "t", "test_{}.py".format(i)), "w").close()
    os.makedirs(os.path.join(root, "small"))
    for i in range(3):
        open(os.path.join(root, "small", "test_s{}.py".format(i)), "w").close()
    os.makedirs(os.path.join(root, "big", "nested"))
    for i in range(8):
        open(os.path.join(root, "big", "nested", "test_b{}.py".format(i)), "w").close()
    os.makedirs(os.path.join(root, "sub"))


def run(command, cwd):
    payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": cwd}
    proc = subprocess.run(["/usr/bin/python3", HOOK], input=json.dumps(payload),
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return "crash", proc.stderr
    if not proc.stdout.strip():
        return "none", None
    out = json.loads(proc.stdout)["hookSpecificOutput"]
    if out.get("permissionDecision") == "deny":
        return "deny", out["permissionDecisionReason"]
    if "updatedInput" in out:
        return "rewrite", out["updatedInput"]["command"]
    return "unknown", out


def main():
    root = tempfile.mkdtemp(prefix="scope-gate-probe-")
    make_tree(root)
    failures = 0
    for command, want, want_cmd in CASES:
        got, detail = run(command, root)
        ok = got == want and (want != "rewrite" or detail == want_cmd)
        print("{}  {:<7} {}".format("ok  " if ok else "FAIL", got, command))
        if not ok:
            failures += 1
            print("      want {} {}\n      got  {}".format(want, want_cmd or "", detail))
    print("\n{} / {} passed".format(len(CASES) - failures, len(CASES)))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
