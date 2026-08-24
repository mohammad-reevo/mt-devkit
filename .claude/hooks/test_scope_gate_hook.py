#!/usr/bin/env python3
"""Test-scope gate: a local pytest run may not cover more than CAP test files.

Personal ~/.claude-style enforcement for the mt-devkit workspace. Local test runs
are targeted; GitHub PR CI is the exhaustive gate (see `local-test-scope.md`). The
failure this exists to stop: a run like `pytest tests/unit/core/flow/` -- 17k tests,
minutes of pinned CPU -- which reads as compliant against a rule whose examples are
`pytest tests/unit` and `make pytest`, and costs about the same.

Prose could not close this. The `implementer` agent definition already carried the
"never run a whole test suite locally" paragraph when a subagent ran that exact
17k-test directory; a subdirectory of `tests/unit/` simply is not `tests/unit`.
"Targeted" is an adjective, not a ceiling -- so the ceiling is enforced here, as a
number, in the harness. Being a hook is the point: it binds every caller, including
subagents that never read a rule.

Gate fires (deny) when a Bash command launches pytest AND either:
  - it names no path at all (whole-tree run: bare `pytest`, `make pytest`), or
  - the paths it names resolve to more than CAP test files.

Explicit `.py` files (and `file.py::node` ids) always pass, however many are named:
naming files IS the targeted behaviour this gate wants.

Escape hatches, both deliberate and visible in the command itself:
  - `--collect-only` (collection is cheap; it runs nothing)
  - a literal `MT_TEST_SCOPE_GATE=0` prefix on the command

Runs under /usr/bin/python3 (macOS system Python 3.9): keep 3.9-compatible
(no PEP 604 unions, no match/case).
"""
from __future__ import annotations

import json
import os
import shlex
import sys

# A run may cover at most this many test files. Above it, name the files that
# cover your change. Hardcoded (single-user tooling, no env override).
CAP = 25

# Tokens that end one command and start another -- a `pytest` right after one of
# these is a launch, not an argument.
SEPARATORS = ("&&", "||", ";", "|", "(", "{")

# Tokens that directly precede a launched `pytest` (`uv run pytest`,
# `python -m pytest`, `make pytest`).
LAUNCHERS = ("run", "-m", "make", "exec")

# Options that consume the following token as their value -- skip that value when
# collecting path arguments, or `-k flow` would read `flow` as a path.
VALUE_OPTS = (
    "-k", "-m", "-n", "-p", "-c", "-o", "-W", "-r",
    "--deselect", "--ignore", "--ignore-glob", "--rootdir", "--maxfail",
    "--numprocesses", "--dist", "--junitxml", "--last-failed-no-failures",
)

TEST_FILE_PREFIX = "test_"
TEST_FILE_SUFFIXES = ("_test.py",)


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


def _pytest_arg_runs(tokens):
    """Every pytest launch in the command: (argument tokens, chdir-or-None).

    A `pytest` token counts as a launch only in command position -- first token,
    after a separator, after a launcher, or after an inline `VAR=value` prefix.
    That is what keeps `grep -rn pytest pyproject.toml` from reading as a run.

    A `cd <dir>` earlier in the command is captured too: `cd salestech-be && pytest
    tests/...` resolves its paths against that dir, not the tool's cwd. Without
    this the paths look nonexistent, count 0, and the gate waves the run through --
    which is exactly how the sub-repo runs in this workspace are usually written.
    """
    runs = []
    chdir = None
    for i, token in enumerate(tokens):
        if token == "cd" and i + 1 < len(tokens):
            chdir = tokens[i + 1]
            continue
        if token != "pytest":
            continue
        if i == 0:
            launched = True
        else:
            prev = tokens[i - 1]
            launched = (
                prev in SEPARATORS or prev in LAUNCHERS or "=" in prev
            )
        if not launched:
            continue
        args = []
        for token in tokens[i + 1:]:
            if token in SEPARATORS:
                break
            args.append(token)
        runs.append((args, chdir))
    return runs


def _path_args(args):
    """The positional path arguments of one pytest run (options dropped)."""
    paths = []
    skip_next = False
    for token in args:
        if skip_next:
            skip_next = False
            continue
        if token.startswith("-"):
            # `--ignore=x` carries its value inline; `--ignore x` consumes the next.
            if "=" not in token and token in VALUE_OPTS:
                skip_next = True
            continue
        paths.append(token)
    return paths


def _count_test_files(path):
    """Test files a path covers: 1 for a file, the recursive count for a dir."""
    if os.path.isfile(path):
        return 1
    if not os.path.isdir(path):
        return 0  # nonexistent path: pytest's error to report, not ours
    total = 0
    for _, _, filenames in os.walk(path):
        for name in filenames:
            if not name.endswith(".py"):
                continue
            if name.startswith(TEST_FILE_PREFIX) or name.endswith(TEST_FILE_SUFFIXES):
                total += 1
    return total


def _resolve(path, cwd):
    # `tests/unit/x.py::TestCase::test_y` addresses the file before the `::`.
    path = path.split("::", 1)[0]
    if not os.path.isabs(path):
        path = os.path.join(cwd, path)
    return os.path.normpath(path)


def _deny_message(offenders, total, no_paths):
    if no_paths:
        what = (
            "This command names no test path, so it runs the whole tree "
            "(cap: {cap} test files)."
        ).format(cap=CAP)
    else:
        listed = "\n".join(
            "  {path}  ->  {count} test files".format(path=p, count=c)
            for p, c in offenders
        )
        what = (
            "This run covers {total} test files (cap: {cap}):\n{listed}"
        ).format(total=total, cap=CAP, listed=listed)

    return (
        "Test-scope gate: blocked.\n"
        "{what}\n"
        "Local runs are targeted; GitHub PR CI runs the full suite on every push, "
        "so a broad local run only duplicates CI and pins the machine.\n"
        "\n"
        "Run the test files that cover the code you changed, named explicitly:\n"
        "  uv run pytest tests/unit/<area>/test_<thing_you_changed>.py\n"
        "Find them with:  rg -l \"<symbol_you_changed>\" tests/\n"
        "\n"
        "If you are an implementer subagent and genuinely believe wider coverage "
        "is needed, do NOT widen on your own -- report it as drift and let the "
        "orchestrator decide.\n"
        "(`--collect-only` passes; so does a literal MT_TEST_SCOPE_GATE=0 prefix.)"
    ).format(what=what)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        _allow()  # never block on malformed input

    if data.get("tool_name", "") != "Bash":
        _allow()

    command = (data.get("tool_input") or {}).get("command", "") or ""
    if "pytest" not in command:
        _allow()  # cheap reject before the parse

    if "MT_TEST_SCOPE_GATE=0" in command:
        _allow()  # deliberate, visible opt-out

    try:
        tokens = shlex.split(command)
    except ValueError:
        _allow()  # unparseable quoting: don't guess, don't block

    runs = _pytest_arg_runs(tokens)
    if not runs:
        _allow()  # `pytest` appeared, but nothing launched it

    cwd = data.get("cwd") or os.getcwd()

    for args, chdir in runs:
        if "--collect-only" in args or "--co" in args:
            continue  # collection runs no tests

        paths = _path_args(args)
        if not paths:
            _deny(_deny_message([], 0, no_paths=True))

        base = _resolve(chdir, cwd) if chdir else cwd
        counts = [(p, _count_test_files(_resolve(p, base))) for p in paths]
        total = sum(c for _, c in counts)
        if total > CAP:
            offenders = [(p, c) for p, c in counts if c > 0]
            _deny(_deny_message(offenders, total, no_paths=False))

    _allow()


if __name__ == "__main__":
    main()
