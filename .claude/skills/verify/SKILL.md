---
name: verify
description: Verification phase of my personal dev workflow. Takes the pushed, reviewed branch from implement, implicitly picks a verification strategy (run scripts / skip / in-app with me), opens the PR up front (using the relevant repo's own pr-description skill + template) — before the slow in-app verification so it doesn't wait behind it — then proves the change works. Directly invocable on any branch. Use after implement, or to verify + PR a branch on its own.
---

> Personal rebuild — self-contained, no devkit dependency.
> Part of the funnel: **scope → plan → implement → verify → babysit → done**
> (see `~/.claude/spec/my-devkit-design.md`).

# verify — open the PR, then prove it works

You pick up a **pushed, reviewed, green branch** (from implement) and carry it to an **open
PR** with the change proven to work. Two jobs: open the PR and verify — and because in-app
verification is slow to set up, the PR goes up **first** so it doesn't wait behind the testing.

Not your job: unit/integration **test-building** is decided in scope and built in
implement; **code review** already happened in implement; **CI babysitting** is babysit.
This skill is post-build, does-it-actually-work verification plus the PR.

## Input check (always first)

Find the plan — glob `~/.claude/spec/*-plan.md` and match against the idea (**never re-derive a
slug from prose**; confirm with me if more than one could fit). Read: **Goals** (the PR's
what/why), **Verification / Manual checks** (informs the strategy), **Repo** (where to run, and
which PR skill to use). No plan (invoked directly on a branch) → infer what to check from the
diff and ask me.

## 1. Pick the verification strategy (implicit — you decide, don't make me choose)

Judge from what actually changed:

- **Scripts-only** — there's a programmatic way to exercise it (a runnable flow like the AI
  flow builder, a CLI, an API script). No coordination needed.
- **N/A** — no visual change, coding tests already cover it, and nothing complex in how the
  frontend consumes it. Nothing to manually verify.
- **In-app (with me)** — real visual changes or potential side effects. Needs me to orchestrate.

State which you picked and why in one line, then proceed. Don't hand me a menu — only the
in-app case pulls me in.

## 2. Open the PR (up front — before the slow verification)

Open the PR on the pushed branch as soon as you've picked the strategy — **before** in-app
verification, not after. The branch is already reviewed and green from implement, so the PR
isn't premature; and in-app setup (env spin-up + live testing) takes real time, so there's no
reason to make the PR wait behind it. (For a fast **scripts-only / N/A** strategy the order
doesn't matter — run the check first if you like — but a slow **in-app** loop must never block
PR creation.)

Create one PR per repo the change touches, **ready for review — never draft**. For the
description, use **that repo's own PR convention** — its `.claude/skills/pr-description` skill
and its `pull_request_template.md`. If that skill is loaded in context, invoke it; otherwise
**read** its `SKILL.md` + `pull_request_template.md` from the sub-repo and follow them (they
aren't auto-loaded in the funnel session, so read-and-follow is the normal path). Fill it with
what/why (from Goals) + the verification plan/results (note when in-app verification is still
**pending**, and update it once it passes). Use the repo's own tooling — never devkit's
`frontend-pr`/`backend-pr`, and don't duplicate them.

Report the PR link right away, so I can start attaching my own verification media to it while
you run the verification.

## 3. Verify per the strategy

- **Scripts-only** → run the script/flow (directly or via a subagent), capture pass/fail + the
  key output.
- **N/A** → note "no manual verification needed: `<reason>`".
- **In-app** → bring the local env up via env-manager **`run backend`** — standalone, that row
  already chains `run frontend` after it (the frontend caches a token the backend mints at startup,
  so it must be restarted against the fresh backend). Don't use `run all-envs` here: it additionally
  recycles docker and realtime, which a webapp check doesn't need and which costs minutes.
  Then drive the app live (browser MCP) with **me directing**: you propose a check, run it when I
  say go, we look at the result together, I call pass/fail. You can suggest checks; I steer.
  Capture a screenshot for UI changes.

  **Check whose services are already running first.** Ports 8000/3000 are shared across worktrees,
  so another session's stack may hold them — and verifying against it proves nothing about your
  branch. Resolve each listening pid's worktree (`lsof -p <pid> -a -d cwd -Fn`) before trusting it,
  and if the stack belongs to another worktree, ask me before taking the ports.

**No workarounds** — if something needs a hack to test (flag off, missing data, auth), that's a
failure to surface and stop on, not a step to route around.

If verification surfaces a bug → fix it, re-run the check, then commit + push to the
**already-open PR**. These after-the-fact changes do **not** re-run implement's code review (it
was a one-shot post-implementation gate). If verification instead surfaces a **structural**
problem (the change is fundamentally wrong, not a fixable bug), that's a kickback to plan — say
so on the PR rather than papering over it.

Once verification passes, return to `/workflow` to continue — it owns what comes next.

## Guardrails

- **Verify, don't rebuild.** You verify a finished branch — you don't re-run coding checks or
  re-review (implement owned those). Only fix what verification itself surfaces.
- **Strategy is your call, not a menu.** Pick N/A / scripts / in-app from what changed; only
  in-app pulls me in.
- **PR up front; fixes pushed to it.** The PR goes up before the slow in-app verification (the
  branch is already green + reviewed from implement), so it's ready while I test; any bug
  verification surfaces is pushed to the open PR. Still ready-for-review, never draft.
- **Use the repo's own PR tooling.** The PR description follows the relevant repo's
  `pr-description` skill + `pull_request_template.md` (read-and-follow if not natively loaded) —
  never devkit's PR skills, and nothing duplicated into the harness.
- **No state, no auto-transition** (Wave 1: I drive). babysit is a separate phase — don't invoke
  it yourself; hand back to `workflow`, which starts it once the PR is open.
