# <project> · session <letter> — brief

Read `~/.claude/tmp/<project>/protocol.md` first, then the project brief it names.
<Resuming after a handoff: then read `~/.claude/tmp/<project>/<letter>-handoff.md` and start PR <n>.>

You own <one PR | a chain of PRs, built in order, one per session>. Start with PR 1; the
orchestrator tells you when to hand off.

## 1. `<slug>` (<ticket or —>) — start now
- **Repo(s):** <repos>
- **Base:** `<base>` — your PR targets it.
- **Worktree:** `worktrees/<slug>` — your own, new for this PR; create it first, from the scratch
  dir you were spawned in (protocol § How you run a PR).
- **Builds:** <one to three lines: what this PR delivers, and the house skills it should follow>
- **Contract:** <what it produces for or consumes from other PRs, e.g. the endpoint shape>
- **Not yours:** <each shared concept another slice owns — "<concept>, owned by `<slice>`" — or none>.
  Build on the owner's result; never decide it here.
- **Depends on:** <hard: the PR it stacks on (base = that PR's branch, or the project base); soft:
  PRs sharing a file — never merged in, the second to land update-branches; or none>

## 2. `<slug>` (<ticket>) — later
- <same fields>
