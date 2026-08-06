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
- ❌ `make pytest …` — it runs with `-n 12`, fanning pytest-xdist across 12 cores.

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
