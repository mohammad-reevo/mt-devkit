---
name: pr-review
description: Review a diff through a fixed trio of parallel lenses — correctness, house-rules conformance, and duplication/dead-code — and report the findings to me. Works on my uncommitted working tree, my branch vs main, or a teammate's PR. Report-only: it never edits code and never posts to GitHub. Replaces my use of the built-in /code-review, which has effort levels, remembered state, and background workflow routing I don't want. Triggers on "review this", "review my diff", "review this branch", "review PR <n>", "/pr-review".
---

> Personal rebuild — self-contained, no devkit dependency.
> Standalone tool. The `reviewer` agent it dispatches is shared with **implement**, which
> dispatches the same trio as its finalization gate (see `~/.claude/spec/my-devkit-design.md`).

# pr-review — review a diff, report findings

You are the **review conductor**. You resolve what's being reviewed, dispatch three lenses over
it in parallel, and hand me a synthesis. The `reviewer` agent derives the diff, selects the rules,
and produces the findings — you decide **what** gets reviewed and how the result reads.

Where pr-review ends: **findings, reported to me.** You never edit code and never post to
GitHub. Fixing is mine to direct (via the `implementer` agent); commenting and merging are mine
to do.

**Fixed by design.** Every run is the same three lenses — no effort levels, no state carried from
the last run, no routing to a background fleet, no behavior that varies by model. That
predictability is why this skill exists.

## Input check (always first)

| Invocation | Target |
|---|---|
| `/pr-review` | The current repo's branch and working tree (the agent unions committed, uncommitted, and untracked). |
| `/pr-review <branch>` | That branch vs `origin/main`. |
| `/pr-review <repo>#<n>` | That repo's PR #`<n>` — usually a teammate's. |

**Which repo.** The session usually sits at the mt-devkit worktree root with the sub-repos nested
inside. Check `salestech-be`, `frontend-monorepo`, `reevo-realtime`, and the parent for changes on
the current branch. Exactly one → that's the target. More than one → ask me; don't guess or
silently review just the first.

**A bare `/pr-review <n>` is ambiguous** — a PR number alone doesn't say which repo, and the
change-scanning above is meaningless for someone else's branch. Ask me which repo rather than
picking one.

## PR targets: review in a throwaway worktree

A teammate's branch needs to be **on disk** — the lenses read surrounding code, not just the
diff — and it must never be checked out in a primary checkout ([[worktrees]] § Reviews). Use a
plain `git worktree add`, **not** the `worktree` skill: that skill creates feature branches across
all sub-repos, which is wrong for reading one repo at one ref.

```bash
gh pr view <n> --repo <org>/<repo> --json headRefName,baseRefName
git -C <repo> fetch origin
git -C <repo> worktree add ~/.claude/tmp/pr-review/pr-<n> origin/<headRefName>
```

Hand the agent that path as the repo and the PR's base ref as its base. **Report the findings
before removing the worktree**, so a teardown failure never costs me the review.

## Run the trio

Dispatch **three `reviewer` subagents in parallel** — one per lens: `correctness`, `house-rules`,
`duplication` — in a single message so they actually run concurrently.

Give each one: the lens name, the repo path, and the target (working tree / branch / PR base ref).
Do **not** hand it a diff or a rule list — the agent derives both, which is what keeps the base ref
and the rule selection defined in one place. The agent carries the rest of the contract, so don't
restate it inline.

Three lenses, every time. Don't add a fourth, don't drop one because the diff looks small, and
don't spawn extra finders to be thorough. A fixed trio is what makes two runs comparable.

## Report

Synthesize the three into one message at the altitude `response-altitude.md` prescribes. Beyond
that rule:

- **Merge duplicates across lenses.** The same defect found by two lenses is one finding, and the
  agreement is worth a clause — not two entries.
- **Carry `unconfirmed` through.** If a lens couldn't verify a finding, say so; don't launder it
  into certainty by restating it in your own voice.
- **Surface what the run couldn't cover** — a malformed rule a lens reported, an empty diff, a
  repo I had to disambiguate. Silently reviewing less than I asked for is the one failure I can't
  detect.

Then stop. Don't propose a fix plan unless I ask, and don't start fixing.

## Guardrails

- **Report-only.** No edits, no GitHub writes. There is no `--fix` and no `--comment`; if I want
  a fix I'll say so, and it goes through the `implementer` agent.
- **Fixed trio, no knobs.** If a run feels shallow, sharpen the lens briefs in `reviewer.md` —
  don't add a dial.
- **Never review in a primary checkout.** PR targets get a throwaway worktree; the primary trees
  stay on clean `main`.
- **Ask rather than assume** which repo. A review of the wrong tree looks exactly like a clean one.
