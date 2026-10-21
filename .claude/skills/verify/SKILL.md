---
name: verify
description: Verification phase of my personal dev workflow. Takes the pushed, reviewed branch from implement, implicitly picks a verification strategy (run scripts / skip / in-app), opens the PR (using the relevant repo's own pr-description skill + template), then proves it works — in-app checks included, run by the agent itself against the PR's Vercel preview (FE-only) or a local stack (BE), with screenshots captured and attached to the PR body via pr-screenshots. Only what genuinely needs me stays pending in the PR body. Directly invocable on any branch. Use after implement, or to verify + PR a branch on its own.
---

> Personal rebuild — self-contained, no devkit dependency.
> Part of the funnel: **scope → plan → implement → verify → babysit → done**
> (see `~/.claude/spec/my-devkit-design.md`).

# verify — open the PR, then prove it works

You pick up a **pushed, reviewed, green branch** (from implement) and carry it to an **open
PR**, with the change proven as far as it can be proven without me. Two jobs: open the PR, and
run the verification. Only what genuinely needs me (a human login the agent doesn't have) is written
into the PR body as pending — I pick that up with the PR, never during the drive.

Not your job: unit/integration **test-building** is decided in scope and built in
implement; **code review** already happened in implement; **CI babysitting** is babysit.
This skill is post-build, does-it-actually-work verification plus the PR.

## Input check (always first)

Find the plan — glob `~/.claude/spec/*-plan.md` and match against the idea (**never re-derive a
slug from prose**; confirm with me if more than one could fit). Read: **Goals** (the PR's
what/why), **Verification / Manual checks** (informs the strategy), **Repo** (where to run, and
which PR skill to use), **Declined review findings** (for the PR body). No plan (invoked directly
on a branch) → infer what to check from the diff and ask me.

**Explicit plan + worktree.** Invoked with a **plan path and a worktree path** (a `workflow`
project drive, where the session stays at the mt-devkit root), use those — never the session's
cwd; the plan's `> Worktree:` header supplies the path when present. Run git as
`git -C <worktree>/<repo> …`, `gh` from that directory (or with `--repo <owner>/<repo>`), and
give any subagent `<worktree>/<repo>` to work in.

## 1. Pick the verification strategy (implicit — you decide, don't make me choose)

Judge from what actually changed:

- **Scripts-only** — there's a programmatic way to exercise it (a runnable flow like the AI
  flow builder, a CLI, an API script). No coordination needed.
- **N/A** — no visual change, coding tests already cover it, and nothing complex in how the
  frontend consumes it. Nothing to manually verify.
- **In-app** — real visual changes or potential side effects. You drive the app yourself (§ 3).

State which you picked and why in one line, then proceed. Don't hand me a menu, and don't wait
for me — all three strategies run to completion inside the drive.

## 2. Open the PR (up front)

Open the PR on the pushed branch as soon as you've picked the strategy. The branch is already
reviewed and green from implement, so the PR isn't premature — and the in-app strategy needs it:
the Vercel preview builds from it, and its body carries the screenshots. (For a fast
**scripts-only / N/A** strategy the order doesn't matter — run the check first if you like.)

Create one PR per repo the change touches, **ready for review — never draft** — two in
salestech-be when implement split out a migration: `mohammad/<slug>-migration` against `main`,
and `mohammad/<slug>` against that migration branch, so its diff shows only the code. A split
PR's branch is the plan filename minus `-plan.md`. A project slice's or split PR's PR goes against
the plan's `> Base:` (`--base <base>`: the project base, the dependency's branch, or `main`) when
it has one — a project slice never `main` by default. For the
description, use the **`pr-description` skill** — it routes to that repo's own convention,
applies my house rules, and preflights the body against the repo's validator so a format miss
doesn't cost a CI cycle. Fill it with what/why (from Goals) + the verification plan/results
(note when in-app verification is still **pending**, and update it once it passes). When the
branch resolves to agentic (per `workflow` § Modes), it also carries every `Assumption:` line
from the scope and plan files.
In any mode, list every entry of the plan's `## Declined review findings` with its reason — a
finding implement declined is still mine to make the final call on.

**The body gets the strategy's outcome, never the coding checks.** implement already ran the
targeted tests, the commit hook ran lint and types, and CI runs them again — a green PR says so without a
sentence. Don't transcribe those results into the body; `## Verification` is for what CI cannot
prove (`pr-description` § Overrides).

Report the PR link right away, so I can start reading it while you run the verification.

## 3. Verify per the strategy

- **Scripts-only** → run the script/flow (directly or via a subagent), capture pass/fail + the
  key output.
- **N/A** → note "no manual verification needed: `<reason>`".
- **In-app** → run it yourself. Pick the surface from the diff:
  - **FE-only** → the PR's Vercel preview (URL in the PR's `<!-- vercel-deploy-previews -->`
    comment) against dev data — no local env.
  - **BE, or BE+FE** → a local stack for this worktree via the **`local-stack`** skill (one per
    session), signed in as the stack's pool org. Bring it up yourself (`local-stack up`, unless
    `local-stack list` already shows it live). Once its checks and screenshots are captured, take
    it down in the same pass (`local-stack down`) — never leave it up for review or `/done`; a
    later re-check brings it back up.

  Drive the UI with the browser MCP; read and set up data with **`backend-request`** (`--dev` for
  dev data, `--stack` for the worktree's local stack as its pool org). Dev writes (`--dev --write`) stay on clearly-test records or a dedicated test flow —
  never someone else's. A workflow check, for example: find test records
  (`POST /api/v1/contacts/_search_by_display_name_or_email_v2`), configure the test flow's draft
  (`PATCH /api/v1/flow/flow_definition/{id}`), validate it (`POST …/validate_graph`), promote it
  (`POST /api/v1/flow/user_flow/{id}/promote` — deploys and activates), fire the trigger by
  patching a contact (`PATCH /api/v1/contacts/{id}`), poll
  `POST /api/v1/flow/user_flow/{id}/flow_runs/_list`, and read `GET /api/v1/flow/flow_run/{id}`.

  For UI changes, capture and attach screenshots with the **`pr-screenshots`** skill — it signs in
  as the agent's own dev user, saves to `~/Downloads/images/<slug>/`, and embeds the images in the
  PR body itself. Give any verifier subagent the same skill.

  Still mine: anything needing a real human login the agent doesn't have.

**Never fake a pass.** If something can't be exercised as it stands (flag off, missing data,
expired auth), don't route around it with a hack and don't report a result that never ran.
Record it as **pending**, and say exactly what's outstanding and why. A verification you didn't
run is pending — never passed.

**Pending verification is an outstanding item, not a stop.** Two failure classes, and only one of
them halts the drive:

- **Environmental, or mine** — expired credentials, a service that's down, my availability. Note
  it, run whatever else you *can* run unattended, mark the rest pending in the PR body, and keep
  going. This never blocks the funnel from reaching a ready PR.
- **The change itself** — it can't work without a hack, or verification surfaces a structural
  problem. That still stops, and still kicks back to plan.

If verification surfaces a bug → fix it, re-run the check, then commit + push to the
**already-open PR**. These after-the-fact changes do **not** re-run implement's code review (it
was a one-shot post-implementation gate). If verification instead surfaces a **structural**
problem (the change is fundamentally wrong, not a fixable bug), that's a kickback to plan — say
so on the PR rather than papering over it.

Once the PR is open and you've run everything you can unattended, return to `/workflow` to
continue — it owns what comes next. Name the screenshot paths next to the PR link in the
hand-back. Name any verification still outstanding in the hand-back, as
a **reminder** rather than a question: the drive doesn't wait on it.

## Guardrails

- **Verify, don't rebuild.** You verify a finished branch — you don't re-run coding checks or
  re-review (implement owned those). Only fix what verification itself surfaces.
- **Strategy is your call, not a menu.** Pick N/A / scripts / in-app from what changed. None of
  the three waits for me — you run in-app yourself.
- **PR up front; fixes pushed to it.** The PR goes up as soon as the strategy is picked (the
  branch is already green + reviewed from implement), so it's ready and carrying the results by
  the time I get to it; any bug verification surfaces is pushed to the open PR. Still
  ready-for-review, never draft.
- **The PR description goes through the `pr-description` skill.** It reads the relevant repo's
  convention live and preflights the body — never devkit's PR skills, and nothing duplicated
  into the harness.
- **Testing is yours to run, never the funnel's to wait on me for.** Only what genuinely needs
  me (a human login the agent doesn't have) stays in the PR body as pending, named in the hand-back —
  and the drive still carries on to a ready PR.
- **No state, no auto-transition** (Wave 1: I drive). babysit is a separate phase — don't invoke
  it yourself; hand back to `workflow`, which starts it once the PR is open.
