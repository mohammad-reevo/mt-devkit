# Local test runs are targeted; CI is the exhaustive gate

## When to Apply
Whenever tests are about to be **run** locally against a product repo (`salestech-be`,
`frontend-monorepo`, …) — the `implement` close-out check, a plan's Verification section, an
`implementer` subagent's checks, or any ad-hoc "let me run the tests" moment.

## The Rule
**Never run a large or whole test suite locally.** Run only the tests that cover the body of
work in front of you — the specific test files or directories exercising the changed code —
plus lint and type-check. Leave the exhaustive sweep to GitHub PR CI.

- ✅ `uv run pytest tests/unit/<area>/test_<thing_you_changed>.py` — the file(s) or directory
  covering the change.
- ✅ **lint + type-check locally** — cheap, cached, and the fastest way to catch the common
  breakages. Get these right locally rather than leaning on CI for them.
- ❌ `pytest tests/unit` / `pytest tests/integration` — the whole tree.
- ❌ `pytest tests/unit/core/flow/` — a *subdirectory* is not automatically targeted;
  that one is 605 test files (~17k tests) and costs about the same as the whole tree.
- ❌ `make pytest …` — it runs with `-n 12`, fanning pytest-xdist across 12 cores.

## Hard-enforced: at most 25 test files per run

`test_scope_gate_hook.py` (PreToolUse on Bash) **denies** any pytest run that covers more than
**25 test files**, and any run that names no path at all (bare `pytest`, `make pytest`). Explicitly
named test files always pass, however many — naming files *is* the targeted behavior. Two escape
hatches, both visible in the command itself: `--collect-only`, and a literal `MT_TEST_SCOPE_GATE=0`
prefix.

**Why a hook and not more words:** prose already failed here once. The `implementer` agent
definition carried "never run a whole test suite locally" verbatim at the moment a subagent ran
`pytest tests/unit/core/flow/` — and that was *literally compliant*, because a subdirectory of
`tests/unit/` is not `tests/unit`. "Targeted" is an adjective; a cap is a number. The hook also
binds every caller — including subagents, which never read this file.

## Why
GitHub PR CI runs the **full** suite on every push, so a whole-tree local run proves nothing CI
won't prove — it just duplicates CI's work on hardware that can't take it. A full `pytest
tests/unit` (or `make pytest -n 12`) fans pytest-xdist across every core: one run pins the
machine, and two workflow sessions doing it at once makes it unusable (300–1100% CPU `python`
processes — a real incident, the laptop was "literally dying"). Targeted local runs give fast
feedback on the change without the meltdown; CI is the backstop for everything else.

Related: `test-economy.md` governs how many tests to **write**; this governs how many to **run**
locally.

This applies across all sessions working in this workspace.
