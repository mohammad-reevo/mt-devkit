---
name: verify
description: Verification phase of my personal dev workflow. Takes the pushed, reviewed branch from implement, implicitly picks a verification strategy (run scripts / skip / in-app with me), proves the change works, then opens the PR using the relevant repo's own pr-description skill + template. Directly invocable on any branch. Use after implement, or to verify + PR a branch on its own.
---

> Personal rebuild — self-contained, no devkit dependency.
> Part of the funnel: **scope → plan → implement → verify → babysit → done**
> (see `~/.claude/spec/my-devkit-design.md`).

# verify — prove it works, then open the PR

You pick up a **pushed, reviewed, green branch** (from implement) and carry it to an **open
PR** — but only once the change is proven to actually work. Two jobs: verify, then PR.

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

## 2. Verify per the strategy

- **Scripts-only** → run the script/flow (directly or via a subagent), capture pass/fail + the
  key output.
- **N/A** → note "no manual verification needed: `<reason>`" and go straight to the PR.
- **In-app** → drive the app live (browser MCP) with **me directing**: you propose a check, run
  it when I say go, we look at the result together, I call pass/fail. You can suggest checks; I
  steer. Capture a screenshot for UI changes.

**No workarounds** — if something needs a hack to test (flag off, missing data, auth), that's a
failure to surface and stop on, not a step to route around.

If verification surfaces a bug → fix it, re-run the check, commit + push. These after-the-fact
changes do **not** re-run implement's code review (it was a one-shot post-implementation gate).

## 3. Open the PR (only after it passes 100%)

Create the PR on the pushed branch (one per repo the change touches). For the description, use
**that repo's own PR convention** — its `.claude/skills/pr-description` skill and its
`pull_request_template.md`. If that skill is loaded in context, invoke it; otherwise **read**
its `SKILL.md` + `pull_request_template.md` from the sub-repo and follow them (they aren't
auto-loaded in the funnel session, so read-and-follow is the normal path). Fill it with
what/why (from Goals) + how-verified (strategy + step-2 results); attach the screenshot for UI
changes. Use the repo's own tooling — never devkit's `frontend-pr`/`backend-pr`, and don't
duplicate them.

Report the PR link + a one-line verification summary. Return to `/workflow` to continue —
it owns what comes next.

## Guardrails

- **Verify, don't rebuild.** You verify a finished branch — you don't re-run coding checks or
  re-review (implement owned those). Only fix what verification itself surfaces.
- **Strategy is your call, not a menu.** Pick N/A / scripts / in-app from what changed; only
  in-app pulls me in.
- **PR only when green.** The PR is created after verification passes 100% — never draft-then-fix.
- **Use the repo's own PR tooling.** The PR description follows the relevant repo's
  `pr-description` skill + `pull_request_template.md` (read-and-follow if not natively loaded) —
  never devkit's PR skills, and nothing duplicated into the harness.
- **No state, no auto-transition** (Wave 1: I drive). babysit is a separate opt-in phase.
