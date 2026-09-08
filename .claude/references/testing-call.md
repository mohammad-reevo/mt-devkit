# The testing call — what a change must cover, and how many tests to write

Shared reasoning, read by `scope` (which makes the call for a direction), by the `implementer`
agent (which re-derives it when no plan or scope covers the change), and by `reviewer`'s
`house-rules` lens.

Two halves that constrain each other: **what must be covered** says a new service method needs
integration coverage; **how many tests to write** says that's one test, not four. Read either
half alone and you get the failure the other prevents.

## What must be covered

Name the **kinds** of test the change warrants and what each would cover:

- **Unit** — pure logic: mapping, presentation, formatting, a branch you can exercise with
  values. Mocks are fine, because no collaborator's behaviour is in question.
- **Integration** — a **new public service method**, or a **new data-layer surface**. What a
  service method most needs proven — org scoping, soft-deleted exclusion, a repository default
  like `exclude_deleted_or_archived` — lives in exactly the code a unit test mocks away. A green
  unit suite says nothing about it.
- **None** — a trivial change, or a pure refactor already covered at the behaviour level.

### The mechanical tell

Before concluding a service change needs nothing: does
`tests/integration/core/<domain>/test_<service>.py` already exist? If it does, the precedent is
settled — extend that file. Its absence isn't permission to skip; it only means there's no
precedent to follow.

### Re-derive when nothing covers the change

The call is anchored to **the code the change lands in**, not to the idea that started it. So it
gets re-derived, never inherited, whenever no plan or scope covers what's being built:

- a revision made after the PR is open (review moved the logic to another layer),
- a plan-less follow-up dispatched straight to the `implementer`,
- a task that drifted into a layer the plan didn't anticipate.

"Unit only", decided when the change lived in one layer, stops being true the moment the change
moves. Re-derive, then say what changed and why.

## How many tests to write

Write the **fewest tests that cover the most behavior**. Each test must justify its existence by
exercising a distinct code path. If removing a test wouldn't reduce confidence, it shouldn't
exist.

- **Combine related scenarios** into one test rather than writing a separate test per input. A
  single test with mixed entity types covers more than individual tests for each type.
- **Boundary cases** (empty input, missing data, zero-length lists) only need a test when the
  code has an explicit branch handling them. Don't test a no-op path.
- **Use parametrize** (`@pytest.mark.parametrize`, `test.each`) when testing the same logic with
  different inputs — don't write N copies of the same test.
- **Fallback behavior** (e.g. name → email, default values) deserves a test only when the
  fallback logic is non-trivial or error-prone.
- **Don't test the framework** — if a field is required by Pydantic/Zod, you don't need a test
  proving it rejects missing values.

### Anti-Patterns

| Don't | Do instead |
|---|---|
| One test per entity type doing the same thing | One test with mixed types |
| Separate tests for empty input, single input, multiple inputs | One test with representative input; empty only if there's a branch |
| 8 tests for a service with 2 code paths | 2-3 tests that hit both paths |
| Asserting obvious validation the schema already enforces | Test business logic the schema can't express |

### What this looks like when both halves hold

A three-level folder tree, a foreign-org folder and a soft-deleted folder folded into a single
dict-equality assertion: four concerns, one test, because the fixture is shared. That is the
target shape — integration coverage where mocks can't reach, without a test file per method.

---

Related: `local-test-scope.md` governs how many tests to **run** locally (CI is the exhaustive
gate); this governs what to cover and how many to write.
