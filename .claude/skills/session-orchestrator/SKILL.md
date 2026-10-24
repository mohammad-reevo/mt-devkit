---
name: session-orchestrator
description: Run a multi-part project from one top-level session that holds only the project's context, while each part — a slice — runs in its own background Claude Code sub-session that I never have to open. The orchestrator frames the project, splits it into slices, sets up a base branch per repo and a worktree per slice, spawns one sub-session per slice running `workflow <mode>` (which itself works through subagents), then tracks them through messages instead of reading their work. More slices run concurrently, and no session carries the whole project in its context. Generic — real projects use it as-is; a hackathon (§ Hackathon) adds an orchestrator-owned base it merges into. Triggers on "orchestrate this project", "run this across sessions", "spin up sub-sessions for", "/session-orchestrator".
---

# session-orchestrator — one session holds the project, sub-sessions do the work

Three layers, each with a narrower context than the one above:

```
orchestrator session   project framing + the index; spawns, routes, merges (hackathon only)
  └─ sub-session ×N    one slice each: `workflow <mode> <slice>` scope → plan → implement → verify
       └─ subagents    the funnel's scoper / planner / implementer / reviewer / tester
```

This is `workflow` § Project drive with the slices moved out of the conductor's context: the
index, branches and worktrees work the same, but each slice runs its own single-idea drive in its
own session instead of being interleaved in this one. Everything in `workflow` holds per slice.

## What a session can and can't do to another session

All verified on Claude Code 2.1.310.

| Capability | How |
|---|---|
| Spawn one | `claude --bg -n "<name>" --permission-mode <mode> [--model] [--effort] [--autocompact <tokens>] "<prompt>"`, run from the directory the session should work in. Prints the session id. No manual step from me. |
| See what's running | `ListAgents` (name, busy / idle); `claude agents --json` (id, name, status, cwd) |
| Talk to it | `SendMessage({to: "<name>"})`. It arrives at the receiver's next tool round, and an **idle session wakes on it** — no polling. It replies the same way, to the orchestrator's name. |
| Hear when it stops | `SendMessage(... notify_when_idle: true)` — one notice, one-shot; re-subscribe after each |
| Read its screen | `claude logs <id>` — a raw terminal render; last resort, never the main channel |
| Stop / resume | `claude stop <id>` keeps the conversation; `claude --bg --resume <id>` continues it |

Can't: **compact another session** (a message is read as text, never as `/compact`), approve its
permission prompts, or answer its `AskUserQuestion`. Two consequences shape this skill:

- **A bloated sub-session is replaced, not compacted.** Spawn it with `--autocompact` so it
  compacts itself; if it still degrades, `claude stop` it and spawn a fresh one with the same
  brief. `workflow` detects the slice's phase from its spec files and git, so nothing is lost.
- **Same permission mode as the orchestrator.** A sub-session in a different mode holds
  cross-session messages for my approval, which silently stalls the protocol. Pass this session's
  own mode in `--permission-mode`.
- **Never `claude rm`.** It deletes the session's worktree too. Tearing down is `/done`'s.

## 1. Frame and split

- **Frame the project** in the project brief `~/.claude/spec/<project>-brief.md`: the goal, what
  done looks like, the slices, and the contract between them — the API, schema or types one slice
  produces for another. This file is what the orchestrator carries and every sub-session reads.
- **Slices.** One per independently buildable piece, each its own PR. Name them per scope's
  naming rule. A slice that needs another's code depends on it; across repos, a frontend slice
  that consumes a new backend endpoint depends on that backend slice.
- **Concurrency.** At most **3 sub-sessions building** at once: each one can bring up a local
  stack (`local-stack` has a fixed pool of 5 orgs) and the machine holds only so many, and
  `local-test-scope.md` allows one pytest run at a time machine-wide — a sub-session denied by it
  retries rather than stopping. Queue the rest and spawn as building ones finish.

## 2. Set up

Write the index `~/.claude/spec/<project>-project.md` in `workflow`'s format, plus a `Session`
column (`<name> · <id>`) and the status `blocked`. Then, as in `workflow` § Project drive:

1. **Base branch per repo** a slice touches, cut from fresh main (§ Project drive step 2).
2. **Worktree per slice**, `worktree create <slug> --no-enter`, one after another, each repo
   switched onto the slice's base (step 3). plan reuses an existing worktree, so the sub-session
   never creates a second one.

The orchestrator itself stays at the mt-devkit root and reaches every tree by path.

## 3. Spawn

Per slice whose dependencies are met (a dependency is met once it has **pushed** — merged only in a
hackathon):

1. Write its brief from `brief-template.md` (this directory) to
   `~/.claude/tmp/<project>/<slug>-brief.md`.
2. Spawn it from the slice's worktree:
   ```bash
   cd <MAIN>/worktrees/<slug> && claude --bg -n "<project> · <slug>" \
     --permission-mode <this session's mode> --autocompact 400000 \
     "You are a sub-session of the <project> project. Read ~/.claude/tmp/<project>/<slug>-brief.md and follow it."
   ```
3. Record the session in the index, set the slice to `scoping`, and subscribe:
   `SendMessage({to: "<project> · <slug>", message: "", notify_when_idle: true})`.

## 4. Conduct

The orchestrator now waits: end the turn, and messages wake it. Each sub-session reports at every
transition (the brief's § Report). On each message:

- **Status** (`scoped`, `planned`, `PR open <url>`, `verified`, `ready <url>`, `blocked <why>`) → update the index
  row, re-subscribe to that session's idle notice.
- **A pushed dependency** → spawn the slices waiting on it, and tell any running dependent to
  `git merge origin/<dependency branch>`.
- **A question** → answer it from the project brief when the brief settles it. Otherwise it is a
  gate, and `workflow` § Modes decides: assistant — batch every pending sub-session question into
  one ask to me and relay the answers; agentic — the sub-session already took its recommendation,
  so just check the Assumption against the brief and correct it if it contradicts.
- **The plan gate** (assistant mode): collect every slice's plan, present them to me together,
  and send each sub-session my go — the same single gate as § Project drive step 4.
- **An idle notice with no final report** → the session stopped mid-flight. Read its last report
  and `claude logs`; resend the brief's resume line, or replace the session (above).

The orchestrator **never** writes slice code, reads slice diffs, or runs a slice's checks — that
context belongs in the sub-session. It reads only the reports, the index, and PR metadata.

## 5. Finish

Each sub-session's drive carries on into babysit for its own PR — it holds the slice's context,
so review threads are addressed there, not here. Once every slice reports `ready <url>`: show the
index table and run `pr-explanation` per PR. From there `workflow` § Project drive steps 7–8
apply — merging and the final PR to main are mine. Leave the sub-sessions running so a later
review comment lands in a session that knows the slice; `/done` tears down the worktrees.

## Hackathon

When the project brief and the index carry `> Hackathon: <idea page URL>` (set by `hackathon`
execute), the orchestrator also owns the base branches, and § 5 is replaced:

- **Mode is agentic**, for every sub-session; hackathon rules apply per `workflow` § Hackathon
  projects (MVP bar, no CI gate, nothing reaches main).
- **Bases** are `mohammad/hackathon-<idea-slug>-base` in each repo (salestech-be and
  frontend-monorepo typically both).
- **The orchestrator merges.** It merges a slice's PR into its hackathon base once the slice
  reports `verified` (`gh pr merge <url> --merge`), then messages every running slice on that base
  to `git merge origin/<base>`, and spawns the slices that were waiting on it. **Only the
  orchestrator merges, only into a hackathon base** — sub-sessions never merge anything, and
  nothing ever merges into main.
- **Backend → frontend contract.** After a backend slice merges, the orchestrator regenerates the
  spec on the BE base and the client against it (`openapi-regen.md` § Generating against a
  backend branch that isn't deployed yet), commits the regenerated client **onto the FE hackathon
  base** and pushes it, then tells the FE slices to merge it in. Pushing the generated client is
  allowed here and only here: the FE base never merges, so nothing leaks into FE history.
- **Sub-sessions run their own stacks** to verify their slice (`local-stack`).
- **The demo.** Once every slice is merged into the bases, the orchestrator checks out the bases
  in its own worktree (`worktree create hackathon-<idea-slug> --no-enter`, each repo switched to
  its base), brings up one local stack across BE and FE, runs the end-to-end demo, and hands back
  to `hackathon` § Prove it.

## Guardrails

- **The orchestrator holds context, not work.** If it is about to read code, it should be asking a
  sub-session instead.
- **Sub-sessions never merge, never message anyone but the orchestrator, never touch another
  slice's worktree.**
- **Merging into main and requesting reviews stay mine** in every mode, hackathon included.
