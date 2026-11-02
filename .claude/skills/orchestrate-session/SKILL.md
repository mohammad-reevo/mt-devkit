---
name: orchestrate-session
description: Run a multi-PR project from one top-level session that holds only the project's context, while each PR runs in its own background Claude Code sub-session. The orchestrator frames the project, settles the design with me one decision at a time, presents a PR breakdown (hard/soft dependencies, which session builds which PRs) for approval, owns the project base branch when a hard-dep chain needs one (unrelated PRs go straight to main), spawns one sub-session per PR running `workflow`, each creating its own worktree, and re-checks every session's live state each turn (`session_status.py`: agent state, PR, checks, threads, merge queue, spec files) instead of reading their work; sessions run through babysit on their own and message it whenever they need its instruction or action — never halting silently. I answer each sub-session's gates in that session; the orchestrator owns everything cross-slice and tells me which session needs me and why. More PRs run concurrently, and no session carries the whole project in its context. A `summary` mode renders where every session stands. A hackathon (§ Hackathon) skips the planning phase and adds an orchestrator-owned base it merges into. Triggers on "orchestrate this project", "run this across sessions", "spin up sub-sessions for", "orchestrate-session summary", "/orchestrate-session", "/orchestrate-session summary".
---

# orchestrate-session — one session holds the project, sub-sessions do the work

Three layers, each with a narrower context than the one above:

```
orchestrator session   project brief, PR breakdown, index, base branch; spawns, routes, syncs
  └─ sub-session ×N    one PR each: `workflow assistant <slice>` scope → plan → implement → verify
       └─ subagents    the funnel's scoper / planner / implementer / reviewer / tester
```

This is `workflow` § Project drive with the slices moved out of the conductor's context: each PR
runs its own single-idea drive in its own session. Everything in `workflow` holds per slice.

Two modes: **run** (§ 1–7, the default) and **summary** (§ Summary).

## What a session can and can't do to another session

All verified on Claude Code 2.1.310.

| Capability | How |
|---|---|
| Spawn one | `claude --bg -n "<name>" --permission-mode <mode> [--model] [--effort] [--autocompact <tokens>] "<prompt>"`, run from the directory the session should work in. Prints the session id. No manual step from me. |
| See what's running | `ListAgents` (name, busy / idle); `claude agents --json` (id, name, status, cwd) |
| Talk to it | `SendMessage({to: "<name>"})`. It arrives at the receiver's next tool round, and an **idle session wakes on it** — no polling. It replies the same way, to the orchestrator's name. |
| Hear when it stops | `SendMessage(... notify_when_idle: true)` — one notice, one-shot; re-subscribe after each |
| Read its screen | `claude logs <id>` — a raw terminal render; last resort, never the main channel |
| Stop / resume | `claude stop <id>` keeps the conversation. `(cd <its cwd> && claude --bg --resume <full uuid> "<prompt>")` continues it — as a **new** background session carrying the old conversation; uuid from `~/.claude/projects/<cwd-slug>/<uuid>.jsonl`. A short id or another cwd opens an interactive picker ("No sessions match") and silently does nothing — check `claude logs <new id>` shows it working. |

Can't: **compact another session** (a message is read as text, never as `/compact`), approve its
permission prompts, or answer its `AskUserQuestion`. What follows from that:

- **A bloated sub-session is replaced, not compacted.** Spawn it with `--autocompact` so it
  compacts itself; if it still degrades, `claude stop` it and spawn a fresh one with the same
  brief. `workflow` detects the slice's phase from its spec files and git, so nothing is lost.
- **Same permission mode as the orchestrator.** A sub-session in a different mode holds
  cross-session messages for my approval, which silently stalls the protocol. Pass this session's
  own mode in `--permission-mode`.
- **Spawn in a subshell** — `(cd <dir> && claude --bg …)`. A bare `cd … && claude --bg …` moves
  the orchestrator's own cwd.
- **Stop before you spawn under a reused name.** A name resolves to the latest session, so the old
  one must be stopped first or messages go astray.
- **Missing from `claude agents` is not ended.** An idle session can drop off the list and
  reappear when I bring it up. Before spawning for a slice, its index owner must be one you or I
  deliberately stopped, or one I said to replace — never one that merely isn't listed.
- **Resume is a last resort, and asked first.** Every resume shows up as another session in my
  agents view. If a stopped session must continue, ask me, then resume exactly once (row above).
  Never spawn extra sessions to recover one.
- **`claude rm` only after the session's own `/done`.** It deletes "a background session and its
  worktree" (2.1.312 help). On a session whose cwd is a plain directory it didn't create, it
  leaves that directory in place (verified on 2.1.316). Every session is spawned in its own
  scratch dir (§ 4), so `claude rm` never sees a primary checkout as the session's tree, and runs
  only after `/done` has torn the session's worktree down; the scratch dir is removed by hand
  afterwards (§ 5 Wrap up). Never `claude rm` a session whose cwd is a primary checkout — `claude stop` it and leave it
  for me. Tearing down a worktree is `/done`'s.

## 1. Frame

Write the project brief `~/.claude/spec/<project>-brief.md` from `project-brief-template.md` (this
directory): the goal, what done looks like, **Decisions (settled — don't re-litigate)**, **Open**,
the orchestration choices, and the contracts between slices. It is what the orchestrator carries
and every sub-session reads — a decision recorded there is one no sub-session re-opens in its own
scope.

## 2. Plan

Skipped in a hackathon — `hackathon` execute's idea page is the plan (§ Hackathon).

1. **Settle the design with me**, one question at a time (`discussion-turns.md`). Each answer
   lands in the brief's Decisions as it is given; a question that stays open goes to Open, and the
   sub-session whose slice it belongs to asks it in its own scope.
2. **PR breakdown.** Slices are PRs: one independently buildable, reviewable piece each, named per
   scope's naming rule. Present three tables:
   - **PRs** — slice · ticket · base · hard deps · soft deps. **Hard** = can't build without the
     other PR's code; its session waits until that PR has pushed, then branches from it.
     **Soft** = both edit the same file. That is conflict bookkeeping, not ordering: once the
     earlier one pushes, the later one `git merge`s its branch, and whoever hits a conflict
     resolves it then.
   - **Sessions** — letter · the PRs it builds, in order · why they're grouped. A session builds
     **one PR at a time**, and a letter holds more than one PR **only for a hard-dep chain** —
     each PR on a fresh session (§ 5 Replace) in a fresh worktree. A soft dep never puts two PRs
     in one letter and never delays a spawn. At most **3 sessions building** at once — each may
     bring up a local stack (`local-stack`'s pool holds 5 orgs) and `local-test-scope.md` allows
     one pytest run machine-wide. A session over the cap waits for a finished one's slot; it is
     never folded into another letter to fit.
   - **Ownership** — concept · owning slice · what every other slice must not decide. One row per
     *behaviour* more than one slice touches (e.g. "hiding external sequence ids in Filter"),
     never per ticket or file. Every shared concept has exactly one owner; the rest build on its
     result. It lands in the project brief's Ownership section and in each session brief's
     **Not yours** line.
3. **Wait for my approval** of the breakdown. Nothing is set up before it.

**Base per PR.** `main`, by default — unrelated PRs, standalone tickets and bug fixes each merge
to main on their own. A **project base** exists only for a hard-dep chain (a PR sequence), and
only that chain's PRs target it, so the chain pays for CI and the merge queue once, on the final
base → main PR, instead of per PR. A project with no chain has no base. Hackathons always have
one (§ Hackathon). One exception, forced by CI: salestech-be fails any PR that mixes
`db/changelog/changes/*.sql` with code, so a **migration** is its own slice with base `main`
(`workflow` § Project drive step 2). Code that needs the table depends on it hard, and starts
once the migration has merged — and, when that code targets a base, once the orchestrator has
synced main into it.

## 3. Set up

- **Base branch per repo** a hard-dep chain touches — only when the breakdown has one — cut from
  fresh main (`workflow` § Project drive step 2). **The orchestrator owns the base**: it creates
  it, syncs main into it (after a migration lands, or when slices need something from main), and
  tells sessions with an open PR that it moved. Sub-sessions never push to or merge into the
  base — the final-PR session (§ 7) excepted — but each **update-branches its own PR from its base** (main or the project base)
  whenever it is CONFLICTING or BEHIND (`git-merge.md`, never ask), without waiting to be told.
- **Index** `~/.claude/spec/<project>-project.md` in `workflow`'s format, with the columns
  `Session` (`<letter> · <id>`) and `Depends on (hard / soft)`, the status `blocked`, and a
  `> Orchestrator:` header line (name, id, brief). With no base, its `> Base:` line reads `main`;
  with one, a `> Carry-over:` line collects what the final-PR session must fix (§ 5, § 7).
- **Protocol** `~/.claude/tmp/<project>/protocol.md` from `protocol-template.md` — the gates,
  reports, handoff and boundaries every sub-session shares.
- **Session brief** `~/.claude/tmp/<project>/<letter>-brief.md` from `session-brief-template.md`
  per session — the PRs it builds, in order, each with its contract and dependencies.

**Each session creates its own worktree**, as its first act; the orchestrator never runs
`worktree_setup.sh` or switches a session's repos. It creates only the session's **scratch dir**
(§ 4), so no session ever runs from the primary checkout. The session brings up its own local
stack, and creates any further tree it needs itself. **One worktree per PR, named after its
slug (`worktrees/<slug>`), never reused** — not even by the next session of the same letter,
whose predecessor may still be listed. The orchestrator stays at the mt-devkit root and reaches
PRs through `gh`.

## 4. Spawn

Per session whose first PR's hard dependencies have pushed (merged only in a hackathon), up to
the cap. First its scratch dir, new for this PR, then the session, from inside it:

```bash
SCRATCH=<MAIN>/worktrees/.sessions/<project>-<slug>
mkdir -p $SCRATCH/.claude && cp <MAIN>/.claude/settings.local.json $SCRATCH/.claude/
(cd $SCRATCH && claude --bg -n "<project> <letter> · <what it builds>" \
  --permission-mode <this session's mode> --autocompact 400000 \
  "You are session <letter> of the <project> project. Ask every question inline as text with options and a recommendation; never use the question UI. Read ~/.claude/tmp/<project>/<letter>-brief.md and follow it.")
```

Each line is load-bearing:
- **The name says what the session builds**, e.g. `crmf-3086 A · sequences field`: a few words
  from the PR's slice. The leading `<project>` slug ties it to its orchestrator in the agents
  view, and `session_status.py` matches on `<project> <letter> ` when an index row has no id yet.
- **Under `<MAIN>/worktrees/`** — gitignored, and inside the trusted mt-devkit tree. A dir under
  `~/.claude/tmp/` fails: `claude --bg` refuses it as "Workspace not trusted".
- **`settings.local.json` copied in** — the scratch dir is its own project, and without the
  `enabledMcpjsonServers` approvals the session stops at a "new MCP servers found" prompt nobody
  can answer. Every server in `<MAIN>/.mcp.json` must be listed there, or it stops anyway.
- **A plain dir, never the primary checkout or a worktree** — so `claude rm` deletes nothing that
  matters (§ What a session can do). From it the session runs `worktree create <slug>`, which
  enters the parent tree (`EnterWorktree` accepts it: the scratch dir sits in the same repo) —
  never `<wt>/salestech-be`, where Bash is blocked.

The session's brief names its base: `main`, or the branch of a hard dependency it builds on.

The inline-questions line is in the prompt, not only the protocol, because a session can hit a gate before it has finished reading; the orchestrator
can't see a question asked through the question UI. Record the session in the index
(`<letter> · <id>`) and set its PR to `scoping`. Then tell me the session is up, with its pointer (§ 5).

## 5. Conduct

The orchestrator waits: end the turn, and a message or I wake it.

**Pull, every turn.** Sessions can't be watched — I talk to them directly, so what they'd report
is stale by the time it arrives. Before answering me, and before acting on any message, run:

```bash
/usr/bin/python3 <MAIN>/.claude/skills/orchestrate-session/session_status.py <project>
```

One row per slice: its session's busy / idle and state (`blocked` = waiting on me), its PR's
state, mergeability, checks, review, open threads and merge-queue position, and which of its scope
/ plan / handoff files exist. Under the table, each `blocked` session's last message — the
question it is asking me. Update the index from it, then act on what changed — a merge, a
queued PR, a session now waiting on me. Never read a session's conversation beyond that quoted
message to find out.

**Gates are mine, in the sub-session.** Each sub-session runs `workflow`'s assistant mode and
asks me its own gates — scope's open questions, the plan go, implement escalations — in its own
session. The orchestrator settles only what the brief already settles or what has one dominant
answer, and passes those answers along so the session doesn't ask me again.

**Every pointer to a session carries its context.** I don't hold each slice's context, so whenever
the orchestrator sends me to a session it says, in a line or two, what that session is building,
where it is (scoping / planning / building / PR), and what it is waiting on me for — the
§ Summary block.

**Sessions run on their own and never halt silently.** Each drives its PR through the whole
funnel, babysit included, without a go from the orchestrator, and messages it whenever it needs
the orchestrator's instruction or action. Those messages are only what the orchestrator must act
on and can't see in an artifact — no scoped / planned / go / verified / ready. On each:

- **`PR open <url>`** → record the PR in the index (it's how the pull finds it).
- **`merged` / `queued`** (its PR merged, or entered main's merge queue) → base sync if it was
  a main PR and a base exists, then Replace / Wrap up (below).
- **`handoff`** → Replace (below).
- **`done`** → the wrap-up's idle wait (below).
- **`decided`** — I decided something in that session that touches another slice, a contract, or
  the brief → record it in the brief (Decisions or the contracts) and tell any affected session.
- **`blocked`** — a cross-slice question, or a brief decision the session would have to break →
  answer it from the brief, or bring it to me here; then relay the answer.
- **`base-red <check>`** — a base-inherited red on its PR → add it to the index's
  `> Carry-over:` line, the list the final-PR session (§ 7) fixes. No other action.
- **`need <what>`** — anything else it can't proceed without → act on it, or bring it to me.
- **A pushed dependency** → spawn sessions whose hard deps are now met, and tell sessions with a
  soft dep on it to `git merge origin/<its branch>`. A conflict from that merge or from an
  update-branch is the session's to resolve — no orchestrator call.
- **A session `not listed — ask Mohammad` in the pull** (missing from `claude agents`, work left)
  → it is not gone: idle sessions drop off that list and come back once I bring them up. Ask me to
  bring it back, naming the session and what it's needed for. Never spawn a replacement unless I
  say so, or it was deliberately stopped — two sessions in one worktree corrupt each other's
  merges and pushes.
- **A session `idle` but not `blocked`, with work left and no message** → a silent halt, which the
  protocol forbids. Ask it what it is waiting on.

**Idle notices only while waiting on a swap or a wrap-up** — after asking a session to hand off or
to `/done`, subscribe once (`SendMessage({to: "<name>", message: "", notify_when_idle: true})`)
so its stop is clean. No standing subscriptions: every notice is a turn of noise.

**Replace — one PR per session.** Once a session's PR no longer needs its context — **merged**
for a PR into the project base (no merge queue there), **in the merge queue** for a PR into main —
tell it to hand off. It writes `~/.claude/tmp/<project>/<letter>-handoff.md` (what shipped, the
contracts it settled, what's left for the next PR) and reports `handoff`. If its letter has a next
PR: wrap it up (below), then spawn a fresh session under the **same letter**, named for its next
PR, with the brief and the handoff, in a new scratch dir (§ 4); it creates its own worktree for the next PR — never the
predecessor's. A slice split mid-flight (e.g. a code-owners carve-out) gets a new letter, never a
second PR in the current session. Until its session wraps up, review comments and CI on a PR are
that session's.

**Wrap up — once a session's PR is merged into the base, or in main's merge queue.** No waiting
on the queue: a queued PR has nothing left for its session to do.

1. Message it to run `/done` on **its own worktrees only**, citing the protocol's standing
   authorization (`done` § One exception), and to report `done <letter>` with what was torn down.
2. **Wait for its idle notice** after that report — never stop it on the `done` message itself,
   which can arrive while teardown is still running (stopping it then leaves a half-deleted
   worktree). Check read-only that its worktrees are gone, then `claude stop <id>`,
   `claude rm <id>`, and `rm -r` its scratch dir (`claude rm` leaves it), and mark it `done` in
   the index.
3. **The session finishes its own teardown.** The orchestrator never removes a sub-session's
   worktree. If teardown was interrupted, ask me, then resume it once (§ What a session can do).

**Kicked out of the queue after wrap-up** → spawn a fresh session under the same letter with its
brief and handoff, in a new scratch dir (§ 4); it recreates its worktree from the PR's branch
(`switch -C mohammad/<slug> origin/mohammad/<slug>`), fixes it, and re-queues.

**Relayed gates** — for a small project, at my ask: sub-sessions never ask me; they report each
gate to the orchestrator and wait, and the orchestrator brings me **one session's gate at a time**
(that slice's context, then its questions) and relays my answers. Sessions still run concurrently;
only their gates are serialised. Record it in the index's `> Mode:` line and the protocol.

The orchestrator **never** writes slice code, reads slice diffs, or runs a slice's checks — that
context belongs in the sub-session. It reads only the messages, the brief, the index, and the
`session_status.py` pull.

## 6. Summary

`orchestrate-session summary` — and unasked whenever the orchestrator needs my input on a
session. Build it from a fresh `session_status.py` run (§ 5 Pull) and the index — a session whose
agent state is `blocked`, or that sent `blocked`, needs me. Then two tiers:

**Needs your input** — one block per session waiting on me:

1. **Needs your input?** yes — what for, in one line, from the question the pull quotes.
2. **Current PR:** the slice, one line on what it does, and its phase.
3. **Owns:** every PR the session's letter is responsible for.

**No input needed** — one line per remaining session: letter · current PR · phase.

I answer each session in its own session.

## 7. Finish

**No base:** once every PR is merged or in main's merge queue, show the index table — each PR
lands on its own, and there is nothing more to open.

**With a base:** once every chain PR is merged into the base, show the index table and run
`pr-explanation` on the base → main diff. Merging slices into the base stays mine (`workflow`
§ Project drive step 7). **The final base → main PR is the orchestrator's, built by a final-PR
sub-session** — one per base (per repo), so the reconciliation's conflicts and CI logs never
enter the orchestrator's context:

1. **Spawn it** like any session (§ 4), letter `Z<repo initial>`, in a worktree whose repo is on
   the base itself (`switch -C mohammad/<project>-base origin/mohammad/<project>-base`). Its
   brief names the base, the repo, and the index's `> Carry-over:` list — the base-inherited reds
   and pending verifications logged during the project (§ 5). It is the **one session authorized
   to push to the base**.
2. **It runs no scope or plan.** It merges `origin/main` into the base **once** and resolves every
   conflict, fixes every CI failure — the carry-over reds included — then opens the PR base →
   main via `verify` (ready, never draft; its body links every slice PR), and babysits it to
   green with every thread resolved. Then it reports `ready <url>`, and the orchestrator adds the
   PR to the index as the last row and tells me it is ready for my double-check.
3. **Cross-repo order is a mechanism.** The frontend base's PR type-checks against FE main, so it
   greens only once the backend final PR has merged, deployed, and the client regen is on FE main
   (`openapi-regen.md`). Its session reports that as the one red left, not as a failure.
4. Merging it stays mine; the session wraps up (§ 5) once it merges or is queued.

**After a base merges, follow-ups go to main** as ordinary PRs, each in its own session — never
back onto the merged base.

Either way every session has been wrapped up as its PR merged or queued (§ 5), so nothing is left
running; the orchestrator's own `/done` is mine to call.

## Hackathon

When the project brief and the index carry `> Hackathon: <idea page URL>` (set by `hackathon`
execute), § 2 is skipped, the orchestrator also merges into the base branches, and § 7 is
replaced:

- **Mode is agentic**, for every sub-session; hackathon rules apply per `workflow` § Hackathon
  projects (MVP bar, no CI gate, nothing reaches main).
- **Bases** are `mohammad/hackathon-<idea-slug>-base` in each repo (salestech-be and
  frontend-monorepo typically both).
- **The orchestrator merges.** It merges a slice's PR into its hackathon base once the slice
  reports `verified` (`gh pr merge <url> --merge`), then messages every running slice on that base
  to `git merge origin/<base>`, and spawns the sessions that were waiting on it. **Only the
  orchestrator merges, only into a hackathon base** — sub-sessions never merge anything, and
  nothing ever merges into main.
- **Backend → frontend contract.** After a backend slice merges, the orchestrator regenerates the
  spec on the BE base and the client against it (`openapi-regen.md` § Generating against a
  backend branch that isn't deployed yet), commits the regenerated client **onto the FE hackathon
  base** and pushes it, then tells the FE slices to merge it in. Pushing the generated client is
  allowed here and only here: the FE base never merges, so nothing leaks into FE history.
- **The demo.** Once every slice is merged into the bases, the orchestrator checks out the bases
  in its own worktree (`worktree create hackathon-<idea-slug> --no-enter`, each repo switched to
  its base), brings up one local stack across BE and FE, runs the end-to-end demo, and hands back
  to `hackathon` § Prove it.

## Guardrails

- **The orchestrator holds context, not work.** If it is about to read code, it should be asking a
  sub-session instead.
- **The orchestrator owns the base and each session's scratch dir; the session owns its
  worktree** — creating it, working in it and tearing it down. Neither touches the other's.
- **A base PR doesn't fix CI it didn't cause.** A red whose cause is already in the base, or on
  main but not yet in it, is base-inherited (`babysit`): reported once, fixed by the final-PR
  session (§ 7).
- **Sub-sessions never merge, never message anyone but the orchestrator, never touch another
  session's worktree.**
- **The final base → main PR is the orchestrator's**, built through its final-PR session (§ 7);
  the orchestrator never reconciles a base itself.
- **Merging into main or the project base, and requesting reviews, stay mine** in every mode —
  a hackathon base is the one thing the orchestrator merges into.
