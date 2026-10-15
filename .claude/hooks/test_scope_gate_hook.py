#!/usr/bin/env python3
"""Test-scope gate: one local pytest at a time, covering at most CAP test files and MAX_WORKERS workers.

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
  - it asks for more workers than the cap in a way that cannot be rewritten in
    place (`PYTEST_ADDOPTS`, `make -C <dir> pytest`).

Deny, too, when a run is in scope but would stack on another one:
  - another pytest process is alive on this machine (this session, a parallel
    subagent, or another session) -- the message names its PID and cwd;
  - the call asks for `run_in_background`.
Per-command caps cannot see these, and they are what exhausted a 36 GB machine:
four in-scope runs overlapped, one of them a run the Bash tool had moved to the
background at its 2-minute timeout and the agent then relaunched on top.

Rewrite, instead of deny, when the only problem is the worker count or timeout:
  - `-n` / `--numprocesses` above the cap, `auto`, or `logical` -> `-n <cap>`
  - `make pytest <paths>` -> the same run through `uv run pytest -n <cap> ...`
  - a Bash `timeout` under MIN_TIMEOUT_MS -> MIN_TIMEOUT_MS, so the run is never
    auto-backgrounded at the 2-minute default
The cap is MAX_WORKERS, or MAX_INTEGRATION_WORKERS when any path is under
`tests/integration/` -- each integration worker imports the whole app (Temporal,
Kafka, FalkorDB) and holds several GB.
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
import subprocess
import sys

# A run may cover at most this many test files, and use at most this many xdist
# workers. Hardcoded (single-user tooling, no env override).
CAP = 5
MAX_WORKERS = 2
MAX_INTEGRATION_WORKERS = 1
# The Bash tool's maximum. Below it, a slow run hits the timeout and is moved to the
# background, where it keeps running while the agent relaunches it.
MIN_TIMEOUT_MS = 600000

MAKE_PYTEST = "uv run pytest -n {n} --dist loadscope --record-mode=none --exitfirst"
RUN = MAKE_PYTEST.format(n=MAX_WORKERS)

INTEGRATION_DIR = os.sep + os.path.join("tests", "integration") + os.sep

# Executables whose process is a pytest run when `pytest` is among its arguments.
# Shells are left out on purpose: the Bash tool's `zsh -c "... uv run pytest ..."`,
# or a `pgrep -f pytest` wait loop, carries the word without being a run.
PYTEST_EXES = ("pytest", "py.test", "uv", "uvx")

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


def _too_many(value, cap):
    value = value.strip().lstrip("=")
    if value in ("auto", "logical"):
        return True
    return value.isdigit() and int(value) > cap


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
        "workers, {integration} for integration tests); GitHub PR CI runs the full suite "
        "on every push, so a broad local run only duplicates CI and pins the machine.\n"
        "\n"
        "Run the test files that cover the code you changed, named explicitly:\n"
        "  {run} tests/unit/<area>/test_<thing_you_changed>.py\n"
        "Find them with:  rg -l \"<symbol_you_changed>\" tests/\n"
        "\n"
        "If you are an implementer subagent and genuinely believe wider coverage "
        "is needed, do NOT widen on your own -- report it as drift and let the "
        "orchestrator decide.\n"
        "(`--collect-only` passes; so does a literal MT_TEST_SCOPE_GATE=0 prefix.)"
    ).format(what=what, cap=CAP, workers=MAX_WORKERS, integration=MAX_INTEGRATION_WORKERS,
             run=RUN)


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


def _is_integration(path):
    return INTEGRATION_DIR in path + os.sep


def _problems(command, cwd):
    """(reasons to deny, reasons the worker count needs a rewrite, worker cap, launches a run)."""
    deny, workers, runs = [], [], []  # runs: (kind, args, cwd, addopts)
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
                runs.append(("make-C" if "-C" in words else "make", rest, cwd, []))
            continue
        at = _pytest_at(words)
        if at is None:
            continue
        args = words[at + 1:]
        if COLLECT_ONLY.intersection(args) or INFO_OPTS.intersection(args):
            continue  # collection / info runs no tests
        runs.append(("pytest", args, cwd, addopts))

    integration = any(
        _is_integration(_resolve(p, run_cwd))
        for _, args, run_cwd, _ in runs for p in _path_args(args)
    )
    cap = MAX_INTEGRATION_WORKERS if integration else MAX_WORKERS
    for kind, args, run_cwd, addopts in runs:
        problem = _path_problem(args, run_cwd)
        if problem:
            deny.append(problem)
        elif kind == "make-C":
            deny.append("`make -C <dir> pytest` hardcodes `-n 12` and can't be "
                        "rewritten in place.")
        elif kind == "make":
            workers.append("`make pytest` hardcodes `-n 12`.")
        if any(_too_many(v, cap) for v in _worker_values(addopts)):
            deny.append("PYTEST_ADDOPTS sets more than {n} workers.".format(n=cap))
        if kind == "pytest" and any(_too_many(v, cap) for v in _worker_values(args)):
            workers.append("pytest with more than {n} workers{why}.".format(
                n=cap, why=" (integration tests)" if integration else ""))
    return deny, workers, cap, bool(runs)


def _process_table():
    """`pid ppid command` lines for every process; MT_TEST_SCOPE_GATE_PS stands in for the probe."""
    fake = os.environ.get("MT_TEST_SCOPE_GATE_PS")
    if fake is not None:
        return fake
    try:
        return subprocess.run(["ps", "-Ao", "pid=,ppid=,command="], capture_output=True,
                              text=True, timeout=5).stdout
    except Exception:
        # Legit business flow: the gate is fail-open by contract (see main); a process
        # table it can't read means it can't see a concurrent run, not that one exists.
        return ""


def _cwd_of(pid):
    if os.environ.get("MT_TEST_SCOPE_GATE_PS") is not None:
        return "?"
    try:
        out = subprocess.run(["lsof", "-a", "-p", pid, "-d", "cwd", "-Fn"],
                             capture_output=True, text=True, timeout=5).stdout
    except Exception:
        # Legit business flow: the cwd only decorates the deny message; the PID is
        # what the reader acts on.
        return "?"
    return next((line[1:] for line in out.splitlines() if line.startswith("n")), "?")


def _running_pytests():
    """(pid, cwd, command) of each live pytest run, one per run (its topmost process)."""
    procs = {}
    for line in _process_table().splitlines():
        parts = line.split(None, 2)
        if len(parts) == 3 and parts[0].isdigit():
            procs[parts[0]] = (parts[1], parts[2])
    me = str(os.getpid())
    runs = set()
    for pid, (_, cmd) in procs.items():
        argv = cmd.split()
        exe = os.path.basename(argv[0])
        if pid == me or not (exe in PYTEST_EXES or exe.startswith("python")):
            continue
        names = [os.path.basename(a) for a in argv]
        if exe in ("pytest", "py.test") or "pytest" in names or "py.test" in names:
            runs.add(pid)
    roots = [pid for pid in runs if procs[pid][0] not in runs]
    return [(pid, _cwd_of(pid), procs[pid][1]) for pid in sorted(roots, key=int)]


def _concurrent_message(running):
    listed = "\n".join(
        "  PID {pid} (cwd {cwd}): {cmd}".format(pid=pid, cwd=cwd, cmd=cmd[:160])
        for pid, cwd, cmd in running
    )
    return (
        "Test-scope gate: blocked -- another pytest run is still alive:\n{listed}\n"
        "One pytest at a time on this machine: every run holds the app per worker, and "
        "overlapping runs (this session, a parallel subagent, another session) exhausted "
        "RAM + swap on 2026-10-12 although none broke a per-command cap.\n"
        "\n"
        "Wait for it to finish. A run the Bash tool moved to the background is still "
        "running: read its output instead of relaunching it. If it is yours and stale, "
        "stop it. To wait in a loop, match the interpreter with a pattern that cannot "
        "match the loop's own command line, e.g. `pgrep -f '[p]ython.*pytest'` -- a "
        "bare `pgrep -f pytest` matches its own shell and never exits.\n"
        "If you are an implementer subagent, report the collision instead of waiting it out.\n"
        "(A literal MT_TEST_SCOPE_GATE=0 prefix bypasses the gate.)"
    ).format(listed=listed)


BACKGROUND_MESSAGE = (
    "Test-scope gate: blocked -- pytest may not run in the background.\n"
    "A backgrounded run keeps holding its memory while the next command starts, which is "
    "how runs come to stack. Run it in the foreground; the gate raises the Bash timeout "
    "to {ms} ms so it is never auto-backgrounded."
).format(ms=MIN_TIMEOUT_MS)


def _rewrite(command, cap):
    command = re.sub(r"(?<![\w./-])g?make\s+pytest(?![\w-])", MAKE_PYTEST.format(n=cap),
                     command)
    out, pos = [], 0
    for seg in re.finditer(r"pytest\b[^;&|\n]*", command):
        out.append(command[pos:seg.start()])
        out.append(WORKER_FLAG.sub(
            lambda m: m.group("flag") + str(cap) if _too_many(m.group("value"), cap)
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
        deny, workers, cap, launches = _problems(command, cwd)
    except ValueError:
        _allow()  # unparseable quoting: don't guess, don't block

    if deny:
        _deny(_deny_message("\n".join(deny)))
    if not launches:
        _allow()
    if tool_input.get("run_in_background"):
        _deny(BACKGROUND_MESSAGE)
    running = _running_pytests()
    if running:
        _deny(_concurrent_message(running))

    new_input, context = dict(tool_input), []
    if workers:
        new = _rewrite(command, cap)
        try:
            still_deny, still_workers, _, _ = _problems(new, cwd)
        except ValueError:
            still_deny, still_workers = [], ["unparseable after rewrite"]
        if new == command or still_deny or still_workers:
            _deny(_deny_message(" ".join(workers) + " It could not be rewritten in place."))
        new_input["command"] = new
        context.append(
            "Test-scope gate rewrote this command to cap pytest at {n} xdist workers: "
            "`{new}`. {why} Run `{run} <test files>` directly next time.".format(
                n=cap, new=new, why=" ".join(workers), run=MAKE_PYTEST.format(n=cap))
        )
    timeout = tool_input.get("timeout")
    if not isinstance(timeout, (int, float)) or timeout < MIN_TIMEOUT_MS:
        new_input["timeout"] = MIN_TIMEOUT_MS
        context.append("Test-scope gate set the Bash timeout to {ms} ms so this run is "
                       "never moved to the background.".format(ms=MIN_TIMEOUT_MS))
    if not context:
        _allow()
    _emit(updatedInput=new_input, additionalContext=" ".join(context))


if __name__ == "__main__":
    main()
