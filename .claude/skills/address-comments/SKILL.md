---
name: address-comments
description: Triage the review comments on my PR and then act on the ones I agree to. Reads every open thread, verifies what it claims, and hands me a numbered report — one short entry per comment with your call, action items at the bottom — then STOPS for my review before any code changes or replies. AI-bot comments, my comments, and other humans' comments each get a different default posture. The inbound mirror of pr-review. Triggers on "address the comments", "go through the PR comments", "what do the review comments say", "handle the bot comments", "/address-comments".
argument-hint: '[repo#n]'
---

> Personal rebuild — self-contained, no devkit dependency.
> Standalone tool. `babysit` surfaces unresolved threads; **this** decides what to do about them.

# address-comments — triage PR comments, then act on the agreed ones

Three steps. The gate between 2 and 3 is the entire point of the skill:

1. **Triage** — read every open thread, verify what it claims, hand me a numbered report. No code
   touched, nothing posted to GitHub.
2. **My review** — we discuss. I decide what happens to each comment.
3. **Execute** — implement the agreed ones, then reply and resolve every thread.

The failure this replaces: **compliance by default.** A comment says X, so the code becomes X —
no step between reading and implementing. A silently-accepted bad suggestion is worse than an
unaddressed comment, because the comment is visible and the regression isn't.

Where this ends: threads replied-to and resolved, on a green branch. Never merging, never
requesting review, never Slack — those are mine (`github.md`).

## Resolve the PR and its threads

Argument `repo#n` names the PR. With no argument, resolve it from the worktree's branch
(`gh pr view --json number,url,headRefOid`); more than one candidate → ask, don't guess.

Read **every** thread and check `isResolved` directly — an `isOutdated` thread is still open, and
a filtered "unresolved" list silently drops them (`github.md`):

```bash
gh api graphql -f query='query { repository(owner:"<org>",name:"<repo>") {
  pullRequest(number:<n>) { reviewThreads(first:100) {
    nodes { id isResolved isOutdated path line
            comments(first:20){nodes{author{login} body createdAt}} } } } } }'
```

Any `isResolved:false` is in scope. Also read top-level conversation comments — they aren't
threads and can't be resolved, but they can still carry a real ask.

## The three sources, and what each is worth

The bar is **verification, not source.** A real bug found by a bot is a real bug; a wrong claim
from a human is still wrong. What differs is the default posture when you're unsure.

| Source | Default posture |
|---|---|
| **AI review bot** (`*-code-review[bot]`, builder agent) | A **hypothesis**, not a finding — a model reading a diff, not a verified defect. Confirm the claim is true of *this* codebase before it earns an action item. **Push back and resolve is a first-class outcome**, not rudeness. |
| **Mohammad** (my own comments) | Authority on **intent and direction** — don't argue about what I want built. But still consequence-check the change it implies: my own comment on salestech-be#31062 moved logic to the service layer and silently invalidated the testing call. Authority over intent isn't authority over side effects. |
| **Another human** | Real context and authority an AI doesn't have. Verify the claim, then default toward implementing. Disagreement is legitimate but needs an argument, not a preference. |

Don't overcorrect into reflexive dismissal. "The bot said it" is not a reason to skip it, and most
bot comments that survive verification are worth doing.

## Step 1 — the report

**Number the comments chronologically** — oldest posted is #1, newest is last, regardless of how
you group them (`github.md`). Action item #N addresses comment #N.

Per comment, three lines at most:

- **#N — `path:line` — <source>** — one line on what it asks.
- **Holds / doesn't hold / can't tell** — what you checked to decide. A claim you couldn't verify
  says so; never launder it into certainty.
- **Call** — one or two sentences: what you'd do and why.

Then the action items, one line each, in three tiers reusing `pr-review`'s vocabulary:

| Tier | Meaning |
|---|---|
| **Implement** | Verified, bounded, and I'd obviously want it. |
| **Push back and resolve** | The claim doesn't hold against this codebase. The reply carries the reasoning. |
| **Bring to me** | A large change, or a genuinely hard call either way. |

**Brevity is the requirement, not a nicety** — this is a thing I skim to find the two comments
that need me. A comment with an obvious answer gets one line, not a paragraph.

Then **stop.** Don't edit code, don't post a reply, don't start on the easy ones because they're
easy. Close with a single line that execution is available on my word.

## Step 2 — my review

Conversational, possibly several rounds. I confirm, override, or re-tier anything. Approval covers
**the action items in the message I approved** — not the next batch, and not a comment that
arrives afterwards. A new comment restarts at step 1 for that thread.

## Step 3 — execute

1. **Dispatch an `implementer`** per action item — product-repo code is never edited from here
   (`delegate-product-code.md`).
2. **The testing call gets re-derived**, and this is the case it exists for: a revision made after
   the PR is open is by definition not covered by the plan, so the implementer works out what the
   change now needs from `mt-devkit/.claude/references/testing-call.md`. A comment that moves code
   into a new layer is exactly the shape that invalidates the original call.
3. **Reply, then resolve, every thread** (`github.md`) — including the push-backs, whose reply is
   the reasoning for not changing anything. A pushed fix with the thread still open is not
   finished work. Reply via `addPullRequestReviewThreadReply`, resolve via `resolveReviewThread`.
4. **Re-check the PR title and description** after pushing — comment-driven changes are exactly
   the kind that make a description stale (`github.md`). Edit from the **live** body; never
   rebuild it from a local draft, and never touch attached media.
5. **Report**: what changed, what got pushed back, what's still open and why.

## Guardrails

- **Nothing lands before the gate.** No edits, no replies, no resolves in step 1. The whole value
  is the pause.
- **Verify before you agree, not after.** An action item that says "implement" asserts you checked
  the claim against the code. If you couldn't, it's a *bring to me*.
- **Escalate rather than pick a side.** A large change or a hard judgment call goes to me in the
  report — never decided unilaterally in either direction.
- **Every thread ends replied-to and resolved**, whichever tier it landed in. `done` gates on it.
- **Report, don't launder.** If a comment was addressed only partly, say which part.
