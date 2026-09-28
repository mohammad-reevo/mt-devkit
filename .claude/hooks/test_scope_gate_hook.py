#!/usr/bin/env python3
"""Test-scope gate: a local pytest run covers at most CAP test files and MAX_WORKERS workers.

Personal ~/.claude-style enforcement for the mt-devkit workspace. Local test runs
are targeted; GitHub PR CI is the exhaustive gate (see `local-test-scope.md`). The
failure this exists to stop: a run like `pytest tests/unit/core/flow/` -- 17k tests,
minutes of pinned CPU -- which reads as compliant against a rule whose examples are
`pytest tests/unit` and `make pytest`, and costs about the same. The second failure
is width, not breadth: every xdist worker holds its own app and database state, so
`make pytest` (hardcoded `-n 12`) exhausts the machine's RAM even on one file.

Prose could not close this. The `implementer` agent definition already carried the
"never run a whole test suite locally" paragraph when a subagent ran that exact
17k-test directory; a subdirectory of `tests/unit/` simply is not `tests/unit`.
"Targeted" is an adjective, not a ceiling -- so the ceiling is enforced here, as a
number, in the harness. Being a hook is the point: it binds every caller, including
subagents that never read a rule.

The caps and the `make` handling match the Assimilation Harness's `pytest_workers`
hook (salestech-be's team overlay), which this replaces for mt-devkit sessions.

Deny when a Bash command launches pytest AND any of:
  - it names no test path (whole-tree run: bare `pytest`, `make pytest`);
  - its paths cover more than CAP test files (a named file counts 1; a directory
    counts the test files under it);
  - it is `make pytest-k` (a pathless `-k`) or `make falkor-ci` (a CI job);
  - it asks for more than MAX_WORKERS workers in a way that cannot be rewritten in
    place (`PYTEST_ADDOPTS`, `make -C <dir> pytest`).

Rewrite, instead of deny, when the only problem is the worker count:
  - `-n` / `--numprocesses` above MAX_WORKERS, `auto`, or `logical` -> `-n MAX_WORKERS`
  - `make pytest <paths>` -> the same run through `uv run pytest -n MAX_WORKERS ...`
The rewrite is returned as `updatedInput` with no permission decision, so the normal
permission flow still applies to the rewritten command.

Escape hatches, both deliberate and visible in the command itself:
  - `--collect-only` (collection is cheap; it runs nothing)
  - a literal `MT_TEST_SCOPE_GATE=0` prefix on the command

Runs under /usr/bin/python3 (macOS system Python 3.9): keep 3.9-compatible
(no PEP 604 unions, no match/case).
"""
from __future__ import annotations

import json
import os
import re
import shlex
import sys

# A run may cover at most this many test files, and use at most this many xdist
# workers. Hardcoded (single-user tooling, no env override).
CAP = 5
MAX_WORKERS = 2

MAKE_PYTEST = (
    "uv run pytest -n {n} --dist loadscope --record-mode=none --exitfirst"
).format(n=MAX_WORKERS)

# Tokens that end one command and start another.
SEPARATORS = {";", "&&", "||", "|", "&", "|&", "(", ")", "{", "}"}

# Words that may precede `pytest` in the command that launches it
# (`uv run pytest`, `python -m pytest`, `timeout 600 pytest`, `command pytest`).
WRAPPERS = {
    "command", "exec", "time", "nice", "timeout", "env",
    "uv", "uvx", "run", "python", "python3", "-m",
}
DURATION = re.compile(r"^\d+[smhd]?$")
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")

# Options that consume the following token as their value -- skip that value when
# collecting path arguments, or `-k flow` would read `flow` as a path.
VALUE_OPTS = {
    "-k", "-m", "-n", "-p", "-c", "-o", "-W", "-r",
    "--deselect", "--ignore", "--ignore-glob", "--rootdir", "--maxfail",
    "--numprocesses", "--maxprocesses", "--dist", "--junitxml", "--junit-xml",
    "--last-failed-no-failures", "--timeout", "--confcutdir", "--basetemp",
    "--durations", "--tb", "--log-level", "--log-cli-level", "--cov",
    "--cov-report", "--record-mode", "--import-mode", "--capture",
    "--override-ini", "--verbosity",
}
INFO_OPTS = {"--version", "-V", "-h", "--help"}
COLLECT_ONLY = {"--collect-only", "--co"}

WORKER_FLAG = re.compile(
    r"(?P<flag>(?<!\S)(?:-n|--numprocesses)(?:\s*=\s*|\s+|(?=[0-9al])))"
    r"(?P<value>\d+|auto|logical)\b"
)

TEST_FILE_PREFIX = "test_"
TEST_FILE_SUFFIXES = ("_test.py",)


def _allow():
    # Emit nothing and exit 0: no decision, so other hooks / normal permissions
    # still apply. The gate only ever *adds* a deny or a rewrite; it never forces an allow.
    sys.exit(0)


def _emit(**fields):
    json.dump({"hookSpecificOutput": dict(hookEventName="PreToolUse", **fields)}, sys.stdout)
    sys.exit(0)


def _deny(reason):
    _emit(permissionDecision="deny", permissionDecisionReason=reason)


def _tokenize(command):
    lexer = shlex.shlex(command.replace("\n", " ; "), posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    return list(lexer)


def _segments(tokens):
    out, current = [], []
    for token in tokens:
        if token in SEPARATORS:
            if current:
                out.append(current)
            current = []
        else:
            current.append(token)
    if current:
        out.append(current)
    return out


def _too_many(value):
    value = value.strip().lstrip("=")
    if value in ("auto", "logical"):
        return True
    return value.isdigit() and int(value) > MAX_WORKERS


def _worker_values(args):
    values = []
    for i, arg in enumerate(args):
        if arg in ("-n", "--numprocesses") and i + 1 < len(args):
            values.append(args[i + 1])
        elif arg.startswith("--numprocesses="):
            values.append(arg.split("=", 1)[1])
        elif arg.startswith("-n") and len(arg) > 2 and not arg.startswith("--"):
            values.append(arg[2:])
    return values


def _pytest_at(words):
    """Index of `pytest` when this segment launches it, else None.

    A `pytest` token counts only in command position, after nothing but wrappers,
    their flags, and durations. That keeps `grep -rn pytest pyproject.toml` from
    reading as a run.
    """
    for i, word in enumerate(words):
        if word in ("pytest", "py.test") or word.endswith("/pytest"):
            return i
        if not (
            word in WRAPPERS
            or word.startswith("-")
            or DURATION.match(word)
            or word.endswith(("/python", "/python3"))
        ):
            return None
    return None


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
    path = os.path.expanduser(path.split("::", 1)[0])
    if not os.path.isabs(path):
        path = os.path.join(cwd, path)
    return os.path.normpath(path)


def _scope_message(offenders, total, no_paths):
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
    return what


def _deny_message(what):
    return (
        "Test-scope gate: blocked.\n"
        "{what}\n"
        "Local runs are targeted (at most {cap} test files, at most {workers} xdist "
        "workers); GitHub PR CI runs the full suite on every push, so a broad local run "
        "only duplicates CI and pins the machine.\n"
        "\n"
        "Run the test files that cover the code you changed, named explicitly:\n"
        "  {run} tests/unit/<area>/test_<thing_you_changed>.py\n"
        "Find them with:  rg -l \"<symbol_you_changed>\" tests/\n"
        "\n"
        "If you are an implementer subagent and genuinely believe wider coverage "
        "is needed, do NOT widen on your own -- report it as drift and let the "
        "orchestrator decide.\n"
        "(`--collect-only` passes; so does a literal MT_TEST_SCOPE_GATE=0 prefix.)"
    ).format(what=what, cap=CAP, workers=MAX_WORKERS, run=MAKE_PYTEST)


def _path_problem(args, cwd):
    """A scope problem with one run's paths, as message text; None when in scope."""
    paths = _path_args(args)
    if not paths:
        return _scope_message([], 0, no_paths=True)
    counts = [(p, _count_test_files(_resolve(p, cwd))) for p in paths]
    total = sum(c for _, c in counts)
    if total > CAP:
        return _scope_message([(p, c) for p, c in counts if c > 0], total, no_paths=False)
    return None


def _problems(command, cwd):
    """(reasons to deny, reasons the worker count needs a rewrite)."""
    deny, workers = [], []
    for words in _segments(_tokenize(command)):
        addopts = []
        while words and (ASSIGNMENT.match(words[0]) or words[0] == "env"):
            name, _, value = words.pop(0).partition("=")
            if name == "PYTEST_ADDOPTS":
                addopts = value.split()
        if not words:
            continue
        if words[0] == "cd" and len(words) > 1:
            # `cd salestech-be && pytest tests/...` resolves its paths against that dir.
            cwd = _resolve(words[1], cwd)
            continue
        if words[0] in ("make", "gmake"):
            targets = [w for w in words[1:] if not w.startswith("-") and "=" not in w]
            if "-C" in words:
                targets = targets[1:]  # the first non-flag word is -C's directory
            if "pytest-k" in targets:
                deny.append("`make pytest-k` is a pathless `-k`: it collects the whole "
                            "suite. Add `-k` to a named test file instead.")
            if "falkor-ci" in targets:
                deny.append("`make falkor-ci` is a CI job (`-n 4` over "
                            "`tests/falkordb/integration`).")
            if "pytest" in targets:
                rest = targets[targets.index("pytest") + 1:]
                problem = _path_problem(rest, cwd)
                if problem:
                    deny.append(problem)
                elif "-C" in words:
                    deny.append("`make -C <dir> pytest` hardcodes `-n 12` and can't be "
                                "rewritten in place.")
                else:
                    workers.append("`make pytest` hardcodes `-n 12`.")
            continue
        at = _pytest_at(words)
        if at is None:
            continue
        args = words[at + 1:]
        if COLLECT_ONLY.intersection(args) or INFO_OPTS.intersection(args):
            continue  # collection / info runs no tests
        if any(_too_many(v) for v in _worker_values(addopts)):
            deny.append("PYTEST_ADDOPTS sets more than {n} workers.".format(n=MAX_WORKERS))
        if any(_too_many(v) for v in _worker_values(args)):
            workers.append("pytest with more than {n} workers.".format(n=MAX_WORKERS))
        problem = _path_problem(args, cwd)
        if problem:
            deny.append(problem)
    return deny, workers


def _rewrite(command):
    command = re.sub(r"(?<![\w./-])g?make\s+pytest(?![\w-])", MAKE_PYTEST, command)
    out, pos = [], 0
    for seg in re.finditer(r"pytest\b[^;&|\n]*", command):
        out.append(command[pos:seg.start()])
        out.append(WORKER_FLAG.sub(
            lambda m: m.group("flag") + str(MAX_WORKERS) if _too_many(m.group("value"))
            else m.group(0),
            seg.group(0),
        ))
        pos = seg.end()
    out.append(command[pos:])
    return "".join(out)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        _allow()  # never block on malformed input

    if data.get("tool_name", "") != "Bash":
        _allow()

    tool_input = data.get("tool_input") or {}
    command = tool_input.get("command", "") or ""
    if "pytest" not in command and "falkor-ci" not in command:
        _allow()  # cheap reject before the parse

    if "MT_TEST_SCOPE_GATE=0" in command:
        _allow()  # deliberate, visible opt-out

    cwd = data.get("cwd") or os.getcwd()
    try:
        deny, workers = _problems(command, cwd)
    except ValueError:
        _allow()  # unparseable quoting: don't guess, don't block

    if deny:
        _deny(_deny_message("\n".join(deny)))
    if not workers:
        _allow()

    new = _rewrite(command)
    try:
        still_deny, still_workers = _problems(new, cwd)
    except ValueError:
        still_deny, still_workers = [], ["unparseable after rewrite"]
    if new == command or still_deny or still_workers:
        _deny(_deny_message(" ".join(workers) + " It could not be rewritten in place."))
    _emit(
        updatedInput=dict(tool_input, command=new),
        additionalContext=(
            "Test-scope gate rewrote this command to cap pytest at {n} xdist workers: "
            "`{new}`. {why} Run `{run} <test files>` directly next time."
        ).format(n=MAX_WORKERS, new=new, why=" ".join(workers), run=MAKE_PYTEST),
    )


if __name__ == "__main__":
    main()
