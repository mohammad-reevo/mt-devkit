# PR descriptions: link related PRs, never dictate merge order

## When to Apply
When writing or updating a PR description — especially for a change split across repos
(`salestech-be` + `frontend-monorepo`, a stacked pair, or any set of PRs that land together).

## Rule
**Cross-reference related PRs. Never tell the reader what order to merge them in.**

- ✅ **Link freely.** "Backend counterpart: `<org>/<repo>#123`", "Frontend counterpart: …",
  "Depends on the schema added in #456". Naming the sibling PR is useful context and stays.
- ❌ **No sequencing instructions.** Drop "⚠️ Merge order — frontend first", "this must land
  before X", "merge after Y is deployed", and any section built around ordering.
- ❌ **No dedicated merge-order section or banner.** If the only content of a heading is
  ordering, delete the heading too.

Merge order is **mine** — I sequence and click every merge (see `github.md`). A PR description
telling me the order is at best redundant and at worst wrong by the time it's read.

## Describing cross-repo CI honestly

The usual reason this creeps in is a CI job that depends on the *other* repo's `main` — e.g.
`check-frontend-breaking-changes` regenerates the openapi client against `frontend-monorepo`
`main` and type-checks it. That's real and worth mentioning; just describe the **mechanism**
rather than issuing an instruction.

```markdown
<!-- ❌ Ordering instruction -->
**⚠️ Merge order: frontend-monorepo#15762 must merge before this PR.**
`check-frontend-breaking-changes` will be red until the FE change lands. There is no bypass.

<!-- ✅ Same information, stated as mechanism -->
Frontend counterpart: frontend-monorepo#15762.
`check-frontend-breaking-changes` regenerates the openapi client against frontend-monorepo
`main` and type-checks it, so that job reflects whatever is on FE `main` when it runs.
```

The reader learns the same thing and draws the ordering conclusion themselves.

## Why
Merge sequencing is a decision the author of the PR doesn't own — it depends on deploy windows,
what else is in flight, and which repo is safe to move first. Baking an order into the
description freezes a judgment that belongs to whoever merges, and it goes stale the moment the
situation changes. Describing the dependency mechanism keeps the useful signal without pretending
to make the call.

This applies across all repositories and projects.
