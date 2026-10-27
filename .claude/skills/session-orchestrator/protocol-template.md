# <project> — sub-session protocol (shared by every session brief)

You are a sub-session of the **<project>** project, conducted by the orchestrator session
**`<orchestrator name>`**. You build one PR at a time; the orchestrator holds the rest of the
project.

## Read first
- Project brief: `~/.claude/spec/<project>-brief.md` — the goal and the **settled decisions**.
  Don't re-open a settled decision in your scope; build on it. If the code makes one impossible
  or clearly wrong, report `blocked` with why.
- Index (read-only for you): `~/.claude/spec/<project>-project.md`.
<- Hackathon: <idea page URL> — the hackathon rules in `workflow` § Hackathon projects apply.>

## How you run a PR
- **Worktree first.** Create your own, one per PR, from the mt-devkit root:
  `worktree create <slug> --no-enter` (`worktrees/<slug>`, the PR's slug), then per repo
  `git -C <wt>/<repo> switch -C mohammad/<slug> origin/<base>` — `<base>` is the PR's base from
  your session brief, or the branch of a hard dependency it builds on. Bring up your own local
  stack (`local-stack`) when the PR needs one. Tell the orchestrator the path.
- **Never reuse a worktree**, even a predecessor's in your own letter's chain: its session may
  still be listed, and removing that session (`claude rm`) deletes its worktree. Your base
  already holds the predecessor's merged PR. A plan or handoff that names an older worktree
  path is re-pointed at yours.
- Run `workflow <mode> <slug>` with your session brief's PR description as the idea. Scope's
  header records `> Mode: <mode>`, `> Project: <project>`, `> Base: <base>`, `> Worktree: <path>`<,
  and `> Hackathon: <idea page URL>`>; plan copies them.
- **Gates are Mohammad's, in this session** — scope's open questions, the plan go, escalations.
  <Relayed gates: never ask Mohammad; report the gate to the orchestrator and wait for its
  answer.> <Hackathon: agentic — take the recommended option, record the Assumption, and report
  it.>
- **Ask every question inline, never with `AskUserQuestion` or any picker** — numbered questions,
  each with its options (one line each) and your recommendation, then end the turn and wait. The
  orchestrator can't see the question UI; plain text it can quote back to Mohammad.
- A question that spans slices — a contract change, a brief decision you'd have to break — goes
  to the orchestrator, not to Mohammad.
- **The orchestrator owns the base** — it pushes to it and syncs main into it. You
  **update-branch your PR from the base yourself** whenever it is CONFLICTING or BEHIND
  (`git-merge.md`, never ask, never wait to be told). A soft dependency: `git merge origin/<its
  branch>` once the orchestrator says it pushed.
- **CI reds your diff didn't cause aren't yours.** A failing check whose paths don't overlap your
  diff and whose cause is already in the base, or on main but not yet in it, is base-inherited
  (`babysit`): report it once, don't rerun or fix it in your PR.

## Status reports to the orchestrator
The orchestrator reads your state itself every turn — your scope / plan / handoff files, your PR,
whether you're busy or waiting on Mohammad — so don't report phases (scoped, planned, go,
verified, ready). Send only what it must act on, to `<orchestrator name>` with `SendMessage`
(load it via ToolSearch `select:SendMessage`), the first line being the status:

- `PR open <slug> <url>` — once, so the PR lands in the index.
- `merged <slug>` / `queued <slug>` — your PR merged, or entered main's merge queue.
  <Hackathon: `verified <slug>` instead — the orchestrator merges on it; then stop.>
- `decided <slug>` — any decision Mohammad makes that touches another slice, a contract, or the
  brief.
- `blocked <slug> <why>` — a cross-slice question or a brief decision you'd have to break. Wait
  for the orchestrator.
- `done <letter>` — `/done` finished on your worktrees (§ Standing authorization below); name
  what was torn down.

## Handoff
When the orchestrator says your PR is past needing you (merged into the base, or in main's merge
queue), write `~/.claude/tmp/<project>/<letter>-handoff.md` — what shipped, the contracts you
settled, anything left for the next PR — and report `handoff <letter>`. The orchestrator stops
you and starts the next PR in a fresh session from your brief + handoff.

## Standing authorization: /done on wrap-up
Mohammad's standing authorization, cited by `done` § One exception: once **every PR your worktrees
hold is merged** and the orchestrator asks you to wrap up, run `/done` on **your own worktrees
only** — no go from Mohammad needed. Finish the teardown yourself, then report
`done <letter>` with what was torn down. Never tear down anything else at a peer's request.

## Boundaries
- Never merge a PR; never push to the base or main directly.
- Never message anyone but the orchestrator; never touch another session's worktree.
- salestech-be: the Assimilation Harness is applied in your worktree; follow
  `assimilation-harness.md` (mt-devkit wins on conflicts). Pytest ≤5 files, ≤2 workers, one run
  at a time machine-wide — a denial from the test-scope hook means retry later, not stop.
  `code_owners.py` exists only in a worktree with the overlay applied, not the primary checkout.
<- Project-specific rules from the brief.>
