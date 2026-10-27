---
name: keep-mergeable
description: Keep an approved PR mergeable until I merge it — poll it, and when `main` moves (BEHIND / DIRTY) merge the base in and resolve ONLY mechanical conflicts — a regenerated `schema.sql` or `openapi.json` — proving with a diff guard that the PR's own change is byte-identical before pushing. Any other conflict stops it. Never merges, never enqueues, never enables auto-merge — after a push it tells me to re-enqueue. Built for busy-main salestech-be PRs that go stale every time `main` moves. Manual only. Triggers on "keep this PR mergeable", "keep it up to date until I merge", "auto update-branch this", "/keep-mergeable".
argument-hint: <pr-url> [<pr-url>...]
allowed-tools:
  - Bash
  - Read
  - Edit
  - ScheduleWakeup
  - ToolSearch
  - PushNotification
---

# keep-mergeable — hold an approved PR merge-ready

`babysit` carries a PR to *reviewable*; this carries an **approved** one to *merged*, for the
stretch where the only thing happening is `main` moving underneath it. Each invocation is **one
poll iteration**: check, act if needed, schedule the next.

## The boundary — what this never does

- **Never merges, enqueues, or enables auto-merge** (`gh pr merge` in any form, `--auto`,
  `enqueuePullRequest`). Landing is mine (`github.md`). A push dequeues the PR and resets
  auto-merge; that is expected — tell me, and I re-enqueue.
- **Never adds a change beyond a merge-conflict fix.** No review fixes, no "while I'm here", no
  lint touch-ups. The diff guard below enforces this; a failure is a stop, not something to fix.

## Resolve the PR (first iteration)

From each URL: repo + number. The PR's branch must be checked out in this session's worktree
(`git -C <wt>/<repo> branch --show-current` equals `headRefName`); if it isn't, say so and stop —
never switch a tree to someone's branch. Only my own PRs (`author.login` is me).

## Each iteration (per PR)

**1. State.**
```bash
gh pr view <n> --json id,state,reviewDecision,mergeable,mergeStateStatus,baseRefName,headRefName,headRefOid
gh api graphql -f query='query { repository(owner:"<o>",name:"<r>") { pullRequest(number:<n>) {
  isInMergeQueue mergeQueueEntry { state position } } } }'
```
- `MERGED` / `CLOSED` → done for that PR; say so. All done → stop the loop.
- Not `APPROVED` → this isn't the stage for me — say so and stop; `babysit` owns pre-approval.

**2. Look ahead — will `main` break it?** Run while the PR is queued or ready to be:
`git fetch origin` then `git merge-tree --write-tree --name-only origin/<base> HEAD`; exit 1 means
a conflict today (the files are listed). salestech-be migrations are Liquibase changesets — one
timestamped file each, picked up by `includeAll` — so two migration PRs never conflict with each
other; Alembic is frozen and CI rejects new revisions.

**3. Behind or conflicted → update-branch.** `mergeStateStatus` `BEHIND` or `DIRTY` (and the PR is
not in the queue — the queue rebases what it holds) runs the procedure below. Otherwise nothing to
do; schedule the next poll.

## Update-branch, conflict fixes only

In the PR's repo checkout, with a clean tree (`git status --porcelain` empty — otherwise stop):

1. **Snapshot** the PR's own change:
   `python3 <this-skill-dir>/pr_diff_guard.py snapshot origin/<base> ~/.claude/tmp/<slug>/guard-<n>.json`
2. **Merge** the base — `git fetch origin && git merge origin/<base>` (never rebase,
   `git-merge.md`). salestech-be with the Assimilation Harness applied: if the merge aborts with
   "Your local changes … would be overwritten", follow the skip-worktree workaround in
   `knowledge-base/concepts/harness/assimilation-harness.md`, then re-apply the overlay.
3. **Resolve — only these, mechanically:**
   - `salestech_be/db/schema.sql` → regenerate, never pick a side:
     `uv run python -m scripts.db.generate_db_schema` (needs Docker).
   - `openapi.json` → regenerate, never pick a side: `uv run generate_openapi.py`.
   - **Anything else conflicted** → `git merge --abort`, report the files, and stop that PR's loop
     with `needs input`. A real conflict is a code decision, and that's mine.
4. **Guard** — `python3 <this-skill-dir>/pr_diff_guard.py check origin/<base> <snapshot>`. Exit 1
   means the PR's own change moved: **don't push**, show its output, leave the merge commit local,
   and stop.
5. **Commit and push** — `Merge origin/<base>` (salestech-be: no
   Claude co-author line, per its prohibitions). Push. Then tell me, also via `PushNotification`:
   "<PR link> updated to main — re-enqueue it". The local DB isn't touched.

## Poll cadence and close

`ScheduleWakeup(600s)`.
Prompt: "Continue keep-mergeable — one more poll iteration for <PR links>." Quiet when nothing
changed: one line ("#38770 approved, mergeable, queue position 4 — nothing to do").

The loop ends when every PR is merged or closed, or on a stop above (not approved, a non-mechanical
conflict, a guard failure, a dirty tree). It never ends by merging anything itself.
