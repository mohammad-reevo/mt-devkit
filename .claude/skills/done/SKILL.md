---
name: done
description: Close out the session's worktree(s) — gate the PR(s) for each one's checked-out branches (CI green + all review threads resolved), delete matching plan/scope spec files, then tear down the worktrees + local branches. Manual only. `/done cancel` abandons an idea without the gate. Use when a PR is ready to close out of your active set (merge happens separately). Triggers on "/done", "close this out", "done with this".
---

> Personal rebuild — self-contained, no devkit dependency.
> Funnel tail: **… → verify → babysit → done** (see `~/.claude/spec/my-devkit-design.md`).

# done — close out the session's worktrees

**Manual only.** Runs only when I explicitly invoke `/done`. Never auto — I review the PRs.

You close out **every worktree this session worked in** — usually one, but a session that
reviewed two PRs or split its work has several, and closing only the one you happen to be
standing in strands the rest. For each: gate the PR(s) for whatever branches are checked out,
delete their plan/scope spec files, and tear it down. Deliberately minimal — no archiving, no
records, no session state. The PR is the source of truth.

## Two modes
- **`/done`** — normal close-out (runs the gate).
- **`/done cancel`** — abandon the idea: skip the gate, tear down anyway (dead exploration,
  superseded direction). No reason arg.

## Resolve what's being closed
1. **Name every worktree this session worked in** — the one the cwd sits under
   (`…/worktrees/<name>/`) **and** every other one this session created or entered. You know
   these from the conversation; there is no session state on disk to read them from. If the
   session entered none → stop, "not in a worktree, nothing to close." Capture each `<name>`,
   then run steps 2–3 and the gate **once per worktree**.

   **Never enumerate `$MAIN/worktrees/` and close what's there.** That directory also holds
   other sessions' in-flight trees; only the ones *this* session created or entered are
   eligible. When there's more than one, list them before tearing any down.
2. For each sub-repo, get the **currently-checked-out** branch:
   `git -C "<worktree>/<subrepo>" branch --show-current`. These **0–2 branches** (normally
   `mohammad/<slug>`) are *exactly* what this close-out handles — nothing else.
3. For each branch, find its open PR: `gh pr list --head "<branch>" --json number,url,state`
   (run from that sub-repo so the repo is inferred).

## Normal mode — the gate (every resolved PR must pass BOTH)
- **CI green:** `gh pr view <n> --json statusCheckRollup,autoMergeRequest,state` — every check
  `conclusion` is success.
  - **Exception — the PR is already queued to merge:** then checks that are merely
    **incomplete** (pending / queued / in-progress / no `conclusion` yet) **don't block the
    gate** — GitHub won't land it until they pass, so there's nothing left for me to watch.
    Queued = `autoMergeRequest` non-null (auto-merge, "Merge when ready") **or**
    `isInMergeQueue: true` **or** `state: MERGED` (it already landed).
  - A check that actually **failed** (`failure`/`timed_out`/`cancelled`/`action_required`)
    still fails the gate **even when queued** — a queued PR sitting on a red check will never
    merge, so tearing its worktree down would strand it.
- **All review threads resolved:** query **every** thread and check `isResolved` directly —
  never a filtered "unresolved" list (an `isOutdated` thread is still OPEN). Same query picks
  up the merge-queue flag above:
  ```bash
  gh api graphql -f query='query { repository(owner:"<owner>",name:"<repo>") {
    pullRequest(number:<n>) { isInMergeQueue reviewThreads(first:100) {
      nodes { isResolved isOutdated path } } } } }'
  ```
  Any `isResolved:false` (regardless of `isOutdated`) = fail — **queued-to-merge never excuses
  an open thread.**

Collect **all** failures across **all** PRs of **all** worktrees and report at once. The gate is
all-or-nothing **within** a worktree — one failing PR → tear down nothing of that worktree — but
**independent across** worktrees: one whose own PRs all pass still closes out, since tearing it
down can only strand its own PRs. No merge requirement — a passing-but-unmerged PR closes out
fine (merge happens separately from your queue).

## Tear down (after the gate passes; immediately in cancel mode)

Run these **per worktree**, for each one that passed its own gate.

1. **Capture what outlives the worktree.** If this work belongs to a project with an entry under
   `knowledge-base/projects/`, invoke **`kb`** `update` to record what this PR actually changed —
   scope that shifted, decisions taken while implementing, anything I'd otherwise have to
   re-explain next session. If the **project itself** is finished (not just this PR), invoke
   **`kb`** `graduate <project>` so its durable residue reaches `concepts/` first.
   **This step is first because step 2 deletes the scope and plan files**, which is where that
   reasoning currently lives — after that it isn't recoverable. No project entry and nothing
   worth keeping is a fine answer: say so in one line. Don't manufacture an entry per PR.
2. **Delete matching spec + scratch files** — for each branch, strip `mohammad/` → `<slug>`;
   delete `~/.claude/spec/<slug>-plan.md` and `<slug>-scope.md` if present, and remove the
   scratch dir `~/.claude/tmp/<slug>/` if present (see `scratch-files.md`). Plan-optional: a
   branch with no spec files just skips the spec part. Use plain `rm` for the spec files and
   `rm -r` for the scratch dir — **never `rm -rf`** (the `-f` flag is permission-blocked and
   treated as dangerous; it gets denied).
3. **Remove the worktree + local branches** — invoke `worktree` `remove <name>` (it exits
   the worktree first, removes the sub-repo + parent worktrees, and deletes the **local**
   feature branches: `mohammad/<slug>` **and** whatever each tree actually had checked out).
   Those differ whenever a session splits its work — one sub-repo ends up on a branch named
   for the second PR rather than for the worktree, and matching on the worktree name alone
   strands it in the primary checkout. **Remote branches are never touched** — they back the
   open PRs and GitHub deletes them on merge.
4. **Don't touch or pull main** — I handle that separately.

## Report
What was closed, **per worktree**: the PR link(s), what went into the knowledge base (or that
nothing did), which spec files were deleted, and that the worktree was removed. If a PR passed on the queued-to-merge exception, **say so and name the
checks still running** — I'm closing out before CI finished, and GitHub will land it unattended.
Name any worktree left standing because its own gate failed, so nothing is silently skipped.

## Guardrails
- **Explicit only.** Never auto-run — only on my `/done`.
- **Every worktree the session worked in, not just the current one.** A session that reviewed
  two PRs or split its work has several; closing only the cwd's leaves the rest orphaned with
  nothing pointing at them. Take the list from the conversation — **never** by enumerating
  `$MAIN/worktrees/`, which also holds other sessions' in-flight trees.
- **Gate is all-or-nothing within a worktree**, independent across them. Any PR failing CI or
  with an open thread → tear down nothing *of that worktree*; the others still close out.
  Report every failure at once (don't fail on the first).
- **Queued-to-merge waives only *incomplete* CI** — never a red check, never an open thread.
  It's a wait-skip (the merge is already committed to), not a quality bypass.
- **All threads, not a filtered list.** Query every thread's `isResolved`; outdated counts as
  open (per `github.md`).
- **Local branches only.** Never delete or push a remote branch.
- **Cancel skips the gate but is still a full explicit teardown** — same cleanup, no PR
  assumption (works even with no PR).
- **No state, no archive** (Wave 1: the files + the PR are the contract).
