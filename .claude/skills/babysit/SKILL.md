---
name: babysit
description: Watch CI checks + PR review threads for the current worktree's PR(s) in a poll loop. OPT-IN — runs only when I explicitly invoke it, never auto-starts. Reports failing checks (trimmed logs) + unresolved threads; reruns a genuinely-flaky failure once. Use --watch-only for a single-shot check. Triggers on "/babysit", "babysit the PR", "watch CI".
argument-hint: [--watch-only]
allowed-tools:
  - Bash
  - Read
  - ScheduleWakeup
---

> Personal rebuild — self-contained, no devkit dependency.
> Funnel tail: **… → verify → babysit → done** (see `~/.claude/spec/my-devkit-design.md`).
> Self-contained — no scripts, no devkit plugin; all inline `gh`.

# babysit — watch CI + PR comments

**Opt-in.** Runs **only** when I explicitly invoke it — never auto-starts, never nudges after a
push (that's the deliberate difference from devkit's). Each invocation is **one poll iteration**:
check, report, schedule the next.

## Resolve the PR(s) (first iteration)

The current branch is `mohammad/<slug>` in one or both sub-repos. For each sub-repo whose
checked-out branch matches the current branch (`git -C <subrepo> branch --show-current`), find
its PR — so a cross-repo idea (backend + frontend) is watched as one set:
- repo: `gh repo view --json nameWithOwner` (run in that sub-repo)
- PR: `gh pr list --head "<branch>" --json number,url,state`

No PR anywhere yet → report "no PR for `<branch>` yet — nothing to watch" and stop (don't loop).
No CI run yet (too early after push) → `ScheduleWakeup(60s)` and return (skip in `--watch-only`).

## Each iteration (per PR)

**Check** (in parallel across the PRs):
- CI: `gh pr checks <n>` (shows blocking vs informational) + `gh run view <run-id> --json jobs`
  for per-job status/conclusion.
- **PR threads — ALL of them, incl. outdated.** Query every thread and read `isResolved`
  directly (an `isOutdated` thread is still OPEN — never trust a filtered "unresolved" list,
  per `github.md`):
  ```bash
  gh api graphql -f query='query { repository(owner:"<owner>",name:"<repo>") {
    pullRequest(number:<n>) { reviewThreads(first:100) {
      nodes { isResolved isOutdated path line comments(first:1){nodes{body}} } } } } }'
  ```
  Any `isResolved:false` = unresolved.

**On a failed CI job** — surface just the failure, not the whole log:
`gh run view <run-id> --log-failed` (already only the failed steps); if still long, `grep`/`tail`
around the `##[error]` marker.

**Flaky rerun — at most once, only when it's not ours:** compare the failing test's file paths
against `git diff main...HEAD --name-only`. If **no overlap** (the failure doesn't touch anything
you changed) **and** this `headSha` hasn't been rerun yet → `gh run rerun <run-id> --failed`
**once**. If it fails again, or the failing paths overlap your diff → report it as actionable.
Track rerun state per `headSha` (a new push resets it).

**Report** (concise — don't fix, don't dispatch):
- A small status table: PR / workflow / job / status·conclusion.
- Unresolved threads: `path:line` + the comment body.
- Surface what's failing; **I** (or the orchestrator) decide how to fix. Track already-reported
  run IDs + thread IDs so you don't re-report the same thing every loop.

## Finish the iteration

- **`--watch-only`** → print the status table + unresolved threads, then exit. No wakeup, no loop.
- **Loop mode (default)** → all PRs green **and** zero unresolved threads → print "all green" and
  exit (do **not** invoke done, do **not** write any state). Otherwise:
  `ScheduleWakeup(delaySeconds: 90, reason: "polling CI + PR threads", prompt: "Continue babysit — run one more poll iteration for the current worktree's PR(s).")`

## Guardrails

- **Opt-in only.** Never auto-start or nudge — only on my explicit invoke.
- **All threads, not a filtered list.** Outdated counts as open (`github.md`).
- **Flaky rerun is one-shot per headSha,** and only when the failure doesn't overlap your diff.
  After that, report it — never rerun endlessly to force green.
- **Report, don't fix.** Surface failures + comments; don't dispatch fix agents or close out.
- **Poll inline, in main orchestration — never delegate the watch.** babysit is a main-loop
  task: one inline `gh` check + `ScheduleWakeup`, nothing more. Never dispatch a subagent to
  poll CI/threads, and never arm a persistent `Monitor` to watch — a delegated watcher lingers
  as a background task and silently duplicates the loop. Subagents are one-shot (bounded task →
  report → end); watching over time is the orchestrator's job, here in the main chat. This also
  means: don't bundle "report CI status over time" into an implement/verify subagent's prompt —
  that's what makes it arm a lingering monitor.
- **No state, no auto-transition.** Reaching green doesn't trigger done — closing out is my
  explicit `/done`.
