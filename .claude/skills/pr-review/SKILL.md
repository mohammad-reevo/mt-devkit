---
name: pr-review
description: Review a diff through a fixed trio of parallel lenses — correctness, house-rules conformance, and duplication/dead-code — and report back what the change is, which files carry it, and the candidate comments tiered into must-leave / minor / skip. Works on my uncommitted working tree, my branch vs main, or a teammate's PR. Two modes I pick, never the skill — the default full trio of parallel subagents, or `mini`, the same three lenses in one main-thread pass with no subagents, for a small diff. Never edits code; posts inline PR comments only when I explicitly say so, then re-reviews the author's revision. Replaces my use of the built-in /code-review, which has effort levels, remembered state, and background workflow routing I don't want. Triggers on "review this", "review my diff", "review this branch", "review PR <n>", "/pr-review", "/pr-review mini", "re-review", "did they address the comments".
argument-hint: '[mini] [branch | repo#n]'
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

**`mini` is not a dial.** The trio is fixed *within* a mode: mini runs the same three
lenses, against the same rules, and reports in the same format — it just runs them in one
main-thread pass instead of three subagents. What changes is where the work happens, not how deep
it goes. It's a cost choice about whether a change is worth three fan-outs, which is why **I** make
it and the skill never infers it. Two runs in the same mode stay comparable; that's the property
being protected, and it's what a depth dial would have destroyed.

## Input check (always first)

| Invocation | Target |
|---|---|
| `/pr-review` | The current repo's branch and working tree (the agent unions committed, uncommitted, and untracked). |
| `/pr-review <branch>` | That branch vs `origin/main`. |
| `/pr-review <repo>#<n>` | That repo's PR #`<n>` — usually a teammate's. |

**Mode.** A leading bare `mini` selects mini mode; anything else is full. It's a separate
axis from the target and composes with every row above — `/pr-review mini`,
`/pr-review mini <branch>`, `/pr-review mini <repo>#<n>`. Everything downstream is shared:
same target resolution, same review worktree for a PR, same report, same posting rules.

**The mode is mine to pick, never yours.** Don't infer it from how the diff looks, don't upgrade a
`mini` run to the trio because the change turned out hairy, and don't downgrade a full run
because the diff is two lines. If mini was the wrong call, finish the pass and say so in the
report (§ 3) — I'll re-run. A mode that drifts on its own is a mode that makes two runs
incomparable, which is the same failure the fixed trio exists to prevent.

**Which repo.** The session usually sits at the mt-devkit worktree root with the sub-repos nested
inside. Check `salestech-be`, `frontend-monorepo`, `reevo-realtime`, and the parent for changes on
the current branch. Exactly one → that's the target. More than one → ask me; don't guess or
silently review just the first. A review of the wrong tree looks exactly like a clean one.

**A bare `/pr-review <n>` is ambiguous** — a PR number alone doesn't say which repo, and the
change-scanning above is meaningless for someone else's branch. Ask me which repo rather than
picking one.

## PR targets: review in a review worktree

A teammate's branch needs to be **on disk** — the lenses read surrounding code, not just the
diff — and it must never be checked out in a primary checkout ([[worktrees]] § Reviews). Create
it with the `worktree` skill's **`create-review`** mode, which builds a read-only tree: the
parent plus only the repo being reviewed, detached at the PR head, no env and no deps.

```bash
gh pr view <n> --repo <org>/<repo> --json headRefName,baseRefName
bash $HOME/Desktop/code/mt-devkit/.claude/skills/worktree/worktree_setup.sh \
  "review-<n>" "$MAIN" --review <repo> origin/<headRefName>
```

Then `EnterWorktree(path: "$MAIN/worktrees/review-<n>")` — the **parent**, never the sub-repo.
Hand the agent `$MAIN/worktrees/review-<n>/<repo>` as the repo and the PR's base ref as its
base. **Report the findings before anything else**, so nothing downstream can cost me the
review.

**You never tear a review worktree down.** It has to outlive the report — posting re-verifies
claims against the code (§ Posting step 2), and a re-review diffs the author's revision against
the head you reviewed. Teardown is `/done`, on my word, same as any other worktree: it removes
the tree, the local branch, and the `~/.claude/tmp/review-<n>/` scratch dir in one go. Don't
offer to clean it up, and don't leave it somewhere `/done` can't reach.

Because the sub-repo is **detached**, `/done`'s PR gate finds no branch and passes vacuously —
that's deliberate. Gating a review tree on the *author's* PR would block my cleanup on their CI
and their unresolved threads. See `worktree` § `create-review`.

## Run the trio (full mode)

Full mode only — in `mini` skip this section entirely and use § Mini mode instead.

Dispatch **three `reviewer` subagents in parallel** — one per lens: `correctness`, `house-rules`,
`duplication` — in a single message so they actually run concurrently.

Give each one: the lens name, the repo path, and the target (working tree / branch / PR base ref).
Do **not** hand it a diff or a rule list — the agent derives both, which is what keeps the base ref
and the rule selection defined in one place. The agent carries the rest of the contract, so don't
restate it inline.

Three lenses, every time. Don't add a fourth, don't drop one because the diff looks small, and
don't spawn extra finders to be thorough. A fixed trio is what makes two runs comparable.

## Mini mode — one pass, in the main thread

Same three lenses, same rules, same report — no subagents. You read the diff and apply
correctness, house-rules, and duplication to it yourself, in one pass. This is the machinery
§ Re-review already uses, pointed at the whole diff instead of an incremental one.

1. **Derive the diff exactly as `reviewer.md` § Get the diff does** — the union of all three
   commands (committed, staged + unstaged, untracked), or the PR's base ref for a PR target. A
   new file has no diff; read it whole. All three empty → say so and stop, same as the agent.
2. **Select the rules.** Pipe that same changed-file list — all three parts of it — into
   `python3 .claude/skills/pr-review/select_rules.py <repo>` and read what comes back. Exit 3
   means the selection is good but some rule files are malformed: use the selected ones **and**
   report the malformed ones as a finding. Exit 2 means the list was empty or its paths weren't
   repo-relative — re-derive it rather than reviewing with no rules. Skipping this step is the
   one thing mini must never do: the sub-repo's own rules aren't in your context either, so
   without it the house-rules lens silently reviews against nothing.
3. **Apply the three lenses** using the briefs in `reviewer.md` § Your lens as written — they are
   the same lenses, and restating them here would let the two drift. Its § What you never do
   binds you too: never edit, never post, never report what CI already catches, never redesign,
   never pad. A lens with nothing to say is `clean`, and `unconfirmed` still means unconfirmed.
4. **Report in the § Report format** — all three parts, numbered and tiered the same way. The
   arrow diagram usually drops out on its own; § Report already says to skip it at one or two
   files.

Then **hold**, exactly as full mode does. § Posting is unchanged — the mode decides how the
review was produced, never what may be done with it, and approval still has to arrive in the
message that asks for it.

**If mini was the wrong call, say so rather than escalating.** A diff that turns out to be
large, to span repos, or to need the surrounding-code reading a lens does properly: finish the
pass, then put it in § 3 as a recommendation to re-run full. Silently spawning the trio breaks
the one guarantee mini makes, and a half-review reported as done is worse than either mode.

## Report

**Three parts, in this order, every run.** Both modes. A defined format, per `response-altitude.md`
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
   Write those payloads to **`~/.claude/tmp/review-<n>/`** — the slug dir `/done` deletes on
   teardown ([[scratch-files]]). Anywhere else and they outlive the review forever.

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

