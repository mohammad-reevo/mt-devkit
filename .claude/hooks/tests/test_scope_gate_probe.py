#!/usr/bin/env python3
"""Probe for test_scope_gate_hook.py -- run it, don't reason about it.

    /usr/bin/python3 .claude/hooks/tests/test_scope_gate_probe.py

Feeds real PreToolUse payloads to the hook as a subprocess, against a scratch tree
of test files, and asserts what it emits. Exits non-zero on the first mismatch.

Three outcomes, matching the hook's own contract:
  deny    -- hard block
  rewrite -- `updatedInput` with the worker count or timeout changed; checked against
             the expected rewritten command (and timeout, when the case names one)
  none    -- no output, so the normal permission flow applies

The process table is faked through MT_TEST_SCOPE_GATE_PS (empty unless a case sets
one), so a pytest running elsewhere on the machine never changes the result. Every
payload carries the minimum timeout unless a case overrides it.
"""
import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir, "test_scope_gate_hook.py"))

RUN = "uv run pytest -n 2 --dist loadscope --record-mode=none --exitfirst"
RUN_INTEGRATION = "uv run pytest -n 1 --dist loadscope --record-mode=none --exitfirst"
TIMEOUT = 600000

PYTEST_PROC = (
    "500 1 /x/.venv/bin/python3 /x/.venv/bin/pytest -n 2 tests/unit/test_a.py\n"
    "501 500 /x/.venv/bin/python3 -c import sys;exec(eval(sys.stdin.readline()))\n"
)
UV_PYTEST_PROC = (
    "600 1 uv run pytest tests/unit/test_a.py\n"
    "601 600 /x/.venv/bin/python3 /x/.venv/bin/pytest tests/unit/test_a.py\n"
)
NOT_A_RUN = (
    "700 1 /bin/zsh -c source snap.sh && eval 'uv run pytest t/test_1.py'\n"
    "701 1 /bin/zsh -c until ! pgrep -f pytest; do sleep 10; done\n"
    "702 1 grep -rn pytest pyproject.toml\n"
)

# (command, expected outcome, expected rewritten command for "rewrite", extras)
# extras: "input" merges into tool_input, "ps" fakes the process table,
#         "timeout" is the expected rewritten timeout.
CASES = [
    # file cap
    ("uv run pytest t/test_1.py t/test_2.py t/test_3.py t/test_4.py t/test_5.py", "none", None, {}),
    ("uv run pytest t/test_1.py t/test_2.py t/test_3.py t/test_4.py t/test_5.py t/test_6.py",
     "deny", None, {}),
    ("uv run pytest t/test_1.py::TestX::test_y", "none", None, {}),
    ("uv run pytest small/", "none", None, {}),
    ("uv run pytest big/", "deny", None, {}),
    ("uv run pytest", "deny", None, {}),
    ("cd sub && uv run pytest ../big/", "deny", None, {}),
    # worker cap
    ("uv run pytest -n 12 t/test_1.py", "rewrite", "uv run pytest -n 2 t/test_1.py", {}),
    ("uv run pytest -n auto t/test_1.py", "rewrite", "uv run pytest -n 2 t/test_1.py", {}),
    ("uv run pytest --numprocesses=8 t/test_1.py", "rewrite",
     "uv run pytest --numprocesses=2 t/test_1.py", {}),
    ("uv run pytest -n 2 t/test_1.py", "none", None, {}),
    ("make pytest t/test_1.py", "rewrite", RUN + " t/test_1.py", {}),
    ("make pytest", "deny", None, {}),
    ("make -C sub pytest ../t/test_1.py", "deny", None, {}),
    ("PYTEST_ADDOPTS='-n 8' uv run pytest t/test_1.py", "deny", None, {}),
    ("make pytest-k 'flow'", "deny", None, {}),
    ("make falkor-ci", "deny", None, {}),
    # integration tests: one worker
    ("uv run pytest -n 2 tests/integration/test_i.py", "rewrite",
     "uv run pytest -n 1 tests/integration/test_i.py", {}),
    ("uv run pytest -n 1 tests/integration/test_i.py", "none", None, {}),
    ("make pytest tests/integration/test_i.py", "rewrite",
     RUN_INTEGRATION + " tests/integration/test_i.py", {}),
    ("uv run pytest -n 2 t/test_1.py tests/integration/test_i.py", "rewrite",
     "uv run pytest -n 1 t/test_1.py tests/integration/test_i.py", {}),
    # launch forms
    ("timeout 600 uv run pytest big/", "deny", None, {}),
    ("time python -m pytest big/", "deny", None, {}),
    ("env FOO=1 pytest big/", "deny", None, {}),
    ("grep -rn pytest pyproject.toml", "none", None, {}),
    ("echo 'uv run pytest big/'", "none", None, {}),
    # background + timeout
    ("uv run pytest t/test_1.py", "deny", None, {"input": {"run_in_background": True}}),
    ("uv run pytest t/test_1.py", "rewrite", "uv run pytest t/test_1.py",
     {"input": {"timeout": None}, "timeout": TIMEOUT}),
    ("uv run pytest t/test_1.py", "rewrite", "uv run pytest t/test_1.py",
     {"input": {"timeout": 120000}, "timeout": TIMEOUT}),
    ("uv run pytest -n 8 t/test_1.py", "rewrite", "uv run pytest -n 2 t/test_1.py",
     {"input": {"timeout": None}, "timeout": TIMEOUT}),
    ("grep -rn pytest pyproject.toml", "none", None, {"input": {"run_in_background": True}}),
    # concurrency
    ("uv run pytest t/test_1.py", "deny", None, {"ps": PYTEST_PROC}),
    ("uv run pytest t/test_1.py", "deny", None, {"ps": UV_PYTEST_PROC}),
    ("uv run pytest t/test_1.py", "none", None, {"ps": NOT_A_RUN}),
    ("uv run pytest --collect-only t/test_1.py", "none", None, {"ps": PYTEST_PROC}),
    ("grep -rn pytest pyproject.toml", "none", None, {"ps": PYTEST_PROC}),
    # escape hatches
    ("uv run pytest --collect-only big/", "none", None, {}),
    ("MT_TEST_SCOPE_GATE=0 uv run pytest big/", "none", None, {}),
    ("MT_TEST_SCOPE_GATE=0 uv run pytest t/test_1.py", "none", None, {"ps": PYTEST_PROC}),
    ("uv run pytest --version", "none", None, {}),
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
    os.makedirs(os.path.join(root, "tests", "integration"))
    open(os.path.join(root, "tests", "integration", "test_i.py"), "w").close()


def run(command, cwd, extras):
    tool_input = {"command": command, "timeout": TIMEOUT}
    for key, value in extras.get("input", {}).items():
        if value is None:
            tool_input.pop(key, None)
        else:
            tool_input[key] = value
    payload = {"tool_name": "Bash", "tool_input": tool_input, "cwd": cwd}
    env = dict(os.environ, MT_TEST_SCOPE_GATE_PS=extras.get("ps", ""))
    proc = subprocess.run(["/usr/bin/python3", HOOK], input=json.dumps(payload),
                          capture_output=True, text=True, env=env)
    if proc.returncode != 0:
        return "crash", proc.stderr
    if not proc.stdout.strip():
        return "none", None
    out = json.loads(proc.stdout)["hookSpecificOutput"]
    if out.get("permissionDecision") == "deny":
        return "deny", out["permissionDecisionReason"]
    if "updatedInput" in out:
        return "rewrite", out["updatedInput"]
    return "unknown", out


def main():
    root = tempfile.mkdtemp(prefix="scope-gate-probe-")
    make_tree(root)
    failures = 0
    for command, want, want_cmd, extras in CASES:
        got, detail = run(command, root, extras)
        ok = got == want
        if ok and want == "rewrite":
            ok = detail.get("command") == want_cmd and (
                "timeout" not in extras or detail.get("timeout") == extras["timeout"])
        label = command + ("  " + json.dumps(extras) if extras else "")
        print("{}  {:<7} {}".format("ok  " if ok else "FAIL", got, label[:150]))
        if not ok:
            failures += 1
            print("      want {} {}\n      got  {}".format(want, want_cmd or "", detail))
    print("\n{} / {} passed".format(len(CASES) - failures, len(CASES)))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
