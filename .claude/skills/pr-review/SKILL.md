---
name: pr-review
description: Review a diff through a fixed trio of parallel lenses — correctness, house-rules conformance, and duplication/dead-code — and report back what the change is, which files carry it, and the candidate comments tiered into must-leave / minor / skip. Works on my uncommitted working tree, my branch vs main, or a teammate's PR. Never edits code; posts inline PR comments only when I explicitly say so, then re-reviews the author's revision. Replaces my use of the built-in /code-review, which has effort levels, remembered state, and background workflow routing I don't want. Triggers on "review this", "review my diff", "review this branch", "review PR <n>", "/pr-review", "re-review", "did they address the comments".
---

> Personal rebuild — self-contained, no devkit dependency.
> Standalone tool. The `reviewer` agent it dispatches is shared with **implement**, which
> dispatches the same trio as its finalization gate (see `~/.claude/spec/my-devkit-design.md`).

# pr-review — review a diff, report findings

You are the **review conductor**. You resolve what's being reviewed, dispatch three lenses over
it in parallel, and hand me a synthesis. The `reviewer` agent derives the diff, selects the rules,
and produces the findings — you decide **what** gets reviewed and how the result reads.

Where pr-review ends: **a report, in my hands.** You never edit code. You never post to GitHub
**until I say so in that message** — see § Posting. Fixing is mine to
direct (via the `implementer` agent); merging is mine to do.

**Fixed by design.** Every run is the same three lenses — no effort levels, no state carried from
the last run, no routing to a background fleet, no behavior that varies by model. That
predictability is why this skill exists. If a run feels shallow, sharpen the lens briefs in
`reviewer.md`; don't add a dial.

## Input check (always first)

| Invocation | Target |
|---|---|
| `/pr-review` | The current repo's branch and working tree (the agent unions committed, uncommitted, and untracked). |
| `/pr-review <branch>` | That branch vs `origin/main`. |
| `/pr-review <repo>#<n>` | That repo's PR #`<n>` — usually a teammate's. |

**Which repo.** The session usually sits at the mt-devkit worktree root with the sub-repos nested
inside. Check `salestech-be`, `frontend-monorepo`, `reevo-realtime`, and the parent for changes on
the current branch. Exactly one → that's the target. More than one → ask me; don't guess or
silently review just the first. A review of the wrong tree looks exactly like a clean one.

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

**Keep the worktree until the review is closed out** — posting needs it (step 2 verifies claims
against the code) and so does a re-review. Tearing it down at the end of the report means
rebuilding a full checkout to post a comment ten minutes later. Remove it once I've posted or
dropped the comments and there's no revision pending.

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

**Three parts, in this order, every run.** A defined format, per `response-altitude.md`
§ When a Skill Defines the Format — whose substance still binds inside each part. Don't
"restore" this section to a free-form synthesis.

The failure this replaces: a severity-ordered dump of everything three lenses found, with no
orientation and no notion of what I'd *do* about any of it. Findings are the raw material; the
report is orientation plus decisions.

### 1. What this change is

Two to four sentences: what the change does and why it exists. Then **the files that carry it**,
each with the role it plays — not the full changed-file list, the ones I'd actually read, in
reading order. Then a **simple arrow diagram** of how they build on each other:

```
edit_planner.py (planner input + serialized conditions)
   → orchestrator.py (wiring, plan build)
   → switch_case_ordering.py (subsumption prover)
```

Only files in the diff. **3–6 nodes**, call or data flow, one clause each. Skip the diagram
entirely when the diff is one or two files — a diagram of two boxes is noise, and a manufactured
one is worse.

Derive this from what you already have: `git diff --stat`, the PR title/body, and the lens
reports, which name the load-bearing files as a side effect of reviewing them. Don't read files
wholesale to build it, and **don't spawn an agent for it**.

### 2. The comments, numbered and tiered

Every finding worth my attention becomes a numbered candidate comment, split into three tiers.
**Number continuously across all three tiers** (1..N, not per-tier) so we can refer to "number 4"
without ambiguity. Order by tier, most severe first within each.

| Tier | Bar |
|---|---|
| **Must leave** | Ships a production behavior bug, **or** the PR doesn't do what its title claims, **or** it's cheap to fix and actively misleads future work (a wrong example, a rule that contradicts the code it steers). |
| **Could leave / minor nits** | Real but non-blocking — a follow-up, or a question rather than a demand. |
| **Worth leaving out** | Rule-true but noise: test restructuring, style volume, a hazard with no reproducer, anything pre-existing that this diff didn't introduce. |

Each entry: **`file:line`**, then **cause → effect → fix**, as prose I can read for context —
2–4 sentences. What's actually wrong, what breaks or misleads because of it, and what would
resolve it. Not a card, not a bare assertion.

**Whose branch it is sets the bar.** On a teammate's PR the nits get dropped — a comment costs
their time, and ten of them bury the two that matter. On my own working tree or branch nothing
gets posted at all, so the tiers mean fix-now / fix-later / drop.

Two things carry through into the tiered list, not into a separate section:

- **Merge duplicates across lenses.** The same defect found by two lenses is one numbered entry,
  and the agreement is worth a clause — not two entries.
- **Carry `unconfirmed` through.** If a lens couldn't verify a finding, say so in the entry;
  don't launder it into certainty by restating it in your own voice. An unconfirmed finding
  usually belongs in *worth leaving out* — telling an author about a hazard you can't reproduce
  mostly costs them time.

### 3. What the run couldn't cover

A malformed rule a lens reported, an empty diff, a repo I had to disambiguate, a claim no lens
could verify. Silently reviewing less than I asked for is the one failure I can't detect.

Then **stop**. Close with a single line that posting is available on my word. Don't post, don't
propose a fix plan unless I ask, and don't start fixing.

## Posting — only when I say so

**Default is hold.** Never post to GitHub until I say so *in that message*. "These are the
must-leaves" is not approval; approval is me telling you to leave them. Approval covers the
comments in the message I approved — not the next batch.

When I do say so, for each comment:

1. **Verify the anchor is in the diff at head.** An inline comment on a line the diff doesn't
   touch is rejected. Get the head SHA (`gh pr view <n> --json headRefOid -q .headRefOid`) and
   confirm the file and line against the diff at that SHA.
2. **Re-verify the claim yourself before it lands on someone else's PR.** A lens's word is enough
   to *tell me* something; it is not enough to *tell the author* something. Re-run the repro,
   re-grep the call sites, re-read the function. This is also where a claim gets narrowed to what
   actually holds: a lens reports the failing case, and checking the neighbouring case often shows
   the defect is real but smaller than stated. Post the narrowed version.
3. **Post inline, on the diff line**, per `github.md` — a resolvable thread, never a top-level
   conversation comment. `POST repos/<org>/<repo>/pulls/<n>/comments` with `commit_id`, `path`,
   `line`, `side=RIGHT`, `body`, via `--input <file.json>` for bodies with backticks or newlines.

Write comments to the author, not to me: state the finding, the evidence, and what would resolve
it, and leave room for them to disagree — you may be missing context they have. Consolidate the
low-priority ones into a single thread rather than opening five.

Then report back which comments went up, with their URLs. If you list the PR's comments to
confirm, **expect ones under my account that you didn't post** — I comment on PRs myself, often
while you're working. Don't claim those, don't treat them as a bug, and don't re-post over them;
check the timestamp and body, and mention what I already covered so we don't duplicate.

## Re-review after the author revises

When the author pushes a revision, re-review **minimally and in the main thread — no subagents**.
The trio already covered the original; this pass only answers "did the revision address what we
raised, and is the new work sound?"

1. **Diff the new head against the head you reviewed** — that range is the entire scope. Read it
   directly; it's normally small.
2. **Walk the posted comments.** For each, say `addressed` / `partially addressed` / `not
   addressed`, with the line that resolves it. A reply that changes no code is not addressed.
3. **Check the new commits for problems of their own** — a fix can introduce one, and nothing has
   reviewed these lines yet.

Report the same way: what's resolved, what isn't, anything new. Re-dispatch the full trio only if
the revision is large enough to be a different change than the one that was reviewed. Replying to
and resolving threads is mine, not yours.

