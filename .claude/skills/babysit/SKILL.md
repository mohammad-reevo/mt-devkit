---
name: babysit
description: Watch CI checks + PR review threads for the current worktree's PR(s) in a poll loop, paced to a ~25-minute CI run (~10-minute polls, so review comments are still picked up promptly). Auto-starts as the funnel tail right after verify opens the PR; standalone it runs on my explicit invoke. Reports failing checks (trimmed logs) + unresolved threads; reruns a genuinely-flaky failure once. Use --watch-only for a single-shot check. Triggers on "/babysit", "babysit the PR", "watch CI".
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

**Two ways in, and only two.** `workflow` runs me automatically once `verify` has opened the PR —
that's the funnel tail, no approval needed. Outside a drive, I run when I'm explicitly invoked.
What I still never do is **nudge after a push** (the deliberate difference from devkit's): no
un-asked-for poll loop attaches itself to an ordinary `git push`.

Each invocation is **one poll iteration**: check, report, schedule the next.

## Resolve the PR(s) (first iteration)

The current branch is `mohammad/<slug>` in one or both sub-repos. For each sub-repo whose
checked-out branch matches the current branch (`git -C <subrepo> branch --show-current`), find
its PR — so a cross-repo idea (backend + frontend) is watched as one set:
- repo: `gh repo view --json nameWithOwner` (run in that sub-repo)
- PR: `gh pr list --head "<branch>" --json number,url,state`

No PR anywhere yet → report "no PR for `<branch>` yet — nothing to watch" and stop (don't loop).
No CI run yet (too early after push) → `ScheduleWakeup(120s)` and return (skip in `--watch-only`).

## Each iteration (per PR)

**Check** (in parallel across the PRs):
- CI: `gh pr checks <n>` (shows blocking vs informational) + `gh run view <run-id> --json
  jobs,status,conclusion,startedAt` for per-job status/conclusion **and the run's age**, which
  is what picks the next poll interval (see *Poll cadence*). Elapsed = `date -u +%s` minus
  `startedAt`.
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

## Poll cadence

**A full CI run takes about 25 minutes.** Polling every 90s against that just burns ~16 wasted
checks watching a run that was never going to be finished. So the cadence is driven by *what
we're actually waiting on*, and the **10-minute base interval exists for review comments** —
those can land at any moment, and they're the reason we don't simply sleep for 25 minutes.

| Where things stand | Next wakeup |
|---|---|
| PR exists, no CI run registered yet | **120s** — only waiting for the run to appear |
| CI in flight, run age **< 20 min** | **600s** — CI won't be done; this poll is for new review comments |
| CI in flight, run age **≥ 20 min** | **300s** — inside the expected finish window, tighten up to catch the result |
| CI finished; only unresolved threads left | **600s** — nothing but comments to watch |
| A rerun was just triggered | treat as a fresh run — back to the **< 20 min** row |

Take the **shortest** interval across the PRs being watched (a cross-repo idea polls on whichever
repo needs attention soonest). Never go below 120s, and **never above 600s** — ten minutes is the
longest I'm willing to go without noticing a new review comment.

**25 minutes is the expected duration, not a deadline.** Don't report a run as slow, stuck, or
hung while it's inside that window — it's simply still going. Only call it out once it's well
past (~40 min+), and even then as an observation, not a failure.

## Finish the iteration

- **`--watch-only`** → print the status table + unresolved threads, then exit. No wakeup, no loop.
- **Loop mode (default)** → all PRs green **and** zero unresolved threads → print "all green" and
  exit (do **not** invoke done, do **not** write any state). Otherwise schedule the next poll at
  the *Poll cadence* interval:
  `ScheduleWakeup(delaySeconds: <from the table>, reason: "<what we're waiting on — e.g. 'CI ~14 min in of ~25; checking for review comments'>", prompt: "Continue babysit — run one more poll iteration for the current worktree's PR(s).")`
- **Keep the loop quiet when nothing changed.** At a 10-minute cadence most iterations have no
  news. If no check changed state and no new thread appeared, emit **one line** ("CI still
  running, ~14/25 min, no new comments") — not a repeat of the full status table.

## Guardrails

- **Two entry points: the funnel tail, or my explicit invoke.** `workflow` starts me right after
  `verify` opens the PR. Never attach to a bare `git push` outside a drive, and never nudge.
- **Pace to the cadence table — a 90s poll is a bug.** CI takes ~25 min; the 10-minute base
  interval is there to catch review comments, not to hover over the run.
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
