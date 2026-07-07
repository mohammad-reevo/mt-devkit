---
name: mt-done
description: Close out the current worktree — gate the PR(s) for its checked-out branches (CI green + all review threads resolved), delete matching plan/scope spec files, then tear down the worktree + local branches. Manual only. `/mt-done cancel` abandons an idea without the gate. Use when a PR is ready to close out of your active set (merge happens separately). Triggers on "/mt-done", "close this out", "done with this".
---

> Personal rebuild — `mt-` prefix temporary (stripped at graduation to standalone repo).
> Funnel tail: **… → mt-verify → mt-babysit → mt-done** (see `~/.claude/spec/my-devkit-design.md`).

# mt-done — close out the worktree

**Manual only.** Runs only when I explicitly invoke `/mt-done`. Never auto — I review the PRs.

You close out the **current worktree**: gate the PR(s) for whatever branches are checked out,
delete their plan/scope spec files, and tear the worktree down. Deliberately minimal — no
archiving, no records, no session state. The PR is the source of truth.

## Two modes
- **`/mt-done`** — normal close-out (runs the gate).
- **`/mt-done cancel`** — abandon the idea: skip the gate, tear down anyway (dead exploration,
  superseded direction). No reason arg.

## Resolve what's being closed
1. Confirm the session is inside a worktree (cwd under `…/worktrees/<name>/`). If not → stop,
   "not in a worktree, nothing to close." Capture `<name>`.
2. For each sub-repo, get the **currently-checked-out** branch:
   `git -C "<worktree>/<subrepo>" branch --show-current`. These **0–2 branches** (normally
   `mohammad/<slug>`) are *exactly* what this close-out handles — nothing else.
3. For each branch, find its open PR: `gh pr list --head "<branch>" --json number,url,state`
   (run from that sub-repo so the repo is inferred).

## Normal mode — the gate (every resolved PR must pass BOTH)
- **CI green:** `gh pr view <n> --json statusCheckRollup` — every check `conclusion` is success.
- **All review threads resolved:** query **every** thread and check `isResolved` directly —
  never a filtered "unresolved" list (an `isOutdated` thread is still OPEN):
  ```bash
  gh api graphql -f query='query { repository(owner:"<owner>",name:"<repo>") {
    pullRequest(number:<n>) { reviewThreads(first:100) {
      nodes { isResolved isOutdated path } } } } }'
  ```
  Any `isResolved:false` (regardless of `isOutdated`) = fail.

Collect **all** failures across **all** PRs and report at once. If anything fails → **stop,
tear down nothing.** No merge requirement — a passing-but-unmerged PR closes out fine (merge
happens separately from your queue).

## Tear down (after the gate passes; immediately in cancel mode)
1. **Delete matching spec files** — for each branch, strip `mohammad/` → `<slug>`; delete
   `~/.claude/spec/<slug>-plan.md` and `<slug>-scope.md` if present. Plan-optional: a branch
   with no spec files just skips this.
2. **Remove the worktree + local branches** — invoke `mt-worktree` `remove <name>` (it exits
   the worktree first, removes the sub-repo + parent worktrees, deletes the **local**
   `mohammad/<slug>` branches). **Remote branches are never touched** — they back the open PRs
   and GitHub deletes them on merge.
3. **Don't touch or pull main** — I handle that separately.

## Report
What was closed: the PR link(s), which spec files were deleted, and that the worktree was
removed.

## Guardrails
- **Explicit only.** Never auto-run — only on my `/mt-done`.
- **Gate is all-or-nothing.** Any PR failing CI or with an open thread → stop, tear down
  nothing. Report every failure at once (don't fail on the first).
- **All threads, not a filtered list.** Query every thread's `isResolved`; outdated counts as
  open (per `github.md`).
- **Local branches only.** Never delete or push a remote branch.
- **Cancel skips the gate but is still a full explicit teardown** — same cleanup, no PR
  assumption (works even with no PR).
- **No state, no archive** (Wave 1: the files + the PR are the contract).
