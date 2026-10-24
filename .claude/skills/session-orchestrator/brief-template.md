# <project> · <slug> — sub-session brief

You are one sub-session of a multi-session project, conducted by the orchestrator session
**`<orchestrator name>`**. You own exactly one slice. Your job is to run it through the funnel
and report back; the orchestrator holds the rest of the project.

## The project

- Project brief (read it first): `~/.claude/spec/<project>-brief.md`
- Index (read-only for you): `~/.claude/spec/<project>-project.md`
<- Hackathon: <idea page URL> — the hackathon rules in `workflow` § Hackathon projects apply>

## Your slice

- **Slice:** `<slug>` — <one or two lines: what this slice builds>
- **Its contract with other slices:** <what it produces or consumes, e.g. the endpoint shape>
- **Repo(s):** <repos>
- **Worktree:** `<MAIN>/worktrees/<slug>` — you are already in it; each repo is on
  `mohammad/<slug>`, based on `<base>`.
- **Base:** `<base>` — your PR targets it. **Depends on:** <slices, or none>

## Run it

Run `workflow <mode> <slug>` with this brief as the idea. Scope's file header records
`> Mode: <mode>`, `> Project: <project>`, `> Base: <base>`, `> Worktree: <path>`<, and
`> Hackathon: <idea page URL>`>, and plan copies them.

## Report

Send each of these to `<orchestrator name>` with `SendMessage`, the first line being the status:

- `scoped` — plus any open question the scope left
- `planned` — plus the plan path
- `PR open <url>`
- `verified` — plus one line on what was proven
- `ready <url>` — babysit announced the PR ready for review (not in a hackathon, which stops at
  `verified`)
- `blocked <why>` — an escalation, a kickback, or a question you can't settle from the project
  brief. In assistant mode, wait for the orchestrator's answer; in agentic, take the recommended
  option, record the Assumption, and report it.

A message from the orchestrator — an answer, or an instruction to merge an updated base in — is
acted on as part of your drive.

## Boundaries

- Never merge a PR, never push to `<base>` or main directly.
- Never message anyone but the orchestrator; never touch another slice's worktree.
- In a hackathon, stop after `verified`. Otherwise your drive runs on into babysit as usual; stay
  available afterwards for review comments on your PR.
