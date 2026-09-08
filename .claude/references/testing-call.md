# The testing call — what coverage a change warrants

Shared reasoning, read by `scope` (which makes the call for a direction) and by the
`implementer` agent (which re-derives it when no plan or scope covers the change). It decides
**what must be covered**, never how many tests to write — `.claude/rules/test-economy.md` owns
the count.

## The call

Name the **kinds** of test the change warrants and what each would cover:

- **Unit** — pure logic: mapping, presentation, formatting, a branch you can exercise with
  values. Mocks are fine, because no collaborator's behaviour is in question.
- **Integration** — a **new public service method**, or a **new data-layer surface**. What a
  service method most needs proven — org scoping, soft-deleted exclusion, a repository default
  like `exclude_deleted_or_archived` — lives in exactly the code a unit test mocks away. A green
  unit suite says nothing about it.
- **None** — a trivial change, or a pure refactor already covered at the behaviour level.

## The mechanical tell

Before concluding a service change needs nothing: does
`tests/integration/core/<domain>/test_<service>.py` already exist? If it does, the precedent is
settled — extend that file. Its absence isn't permission to skip; it only means there's no
precedent to follow.

## Re-derive when nothing covers the change

The call is anchored to **the code the change lands in**, not to the idea that started it. So it
gets re-derived, never inherited, whenever no plan or scope covers what's being built:

- a revision made after the PR is open (review moved the logic to another layer),
- a plan-less follow-up dispatched straight to the `implementer`,
- a task that drifted into a layer the plan didn't anticipate.

"Unit only", decided when the change lived in one layer, stops being true the moment the change
moves. Re-derive, then say what changed and why.

## Don't overcorrect

This names what must be **covered** — not a test count. One test folding several concerns over a
shared fixture is the target shape: a three-level tree, a foreign-org folder and a soft-deleted
folder in a single dict-equality assertion covers four concerns in one test. Read this alongside
`test-economy.md`, never against it.
