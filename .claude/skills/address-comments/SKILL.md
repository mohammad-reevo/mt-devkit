---
name: address-comments
description: Triage the review comments on my PR and then act on the ones I agree to. Reads every open thread, verifies what it claims, and hands me a numbered report — one short entry per comment with your call, action items at the bottom — then STOPS for my review before any code changes or replies. Approvals given while we discuss accumulate but authorize nothing: the skill re-emits a finalized action table and waits for one explicit go before it executes. AI-bot comments, my comments, and other humans' comments each get a different default posture. The inbound mirror of pr-review. Triggers on "address the comments", "go through the PR comments", "what do the review comments say", "handle the bot comments", "/address-comments".
argument-hint: '[repo#n]'
---

> Personal rebuild — self-contained, no devkit dependency.
> Standalone tool. `babysit` surfaces unresolved threads; **this** decides what to do about them.

# address-comments — triage PR comments, then act on the agreed ones

Four steps. The gate before execution is the entire point of the skill:

1. **Triage** — read every open thread, verify what it claims, hand me a numbered report. No code
   touched, nothing posted to GitHub.
2. **My review** — we discuss, over as many rounds as it takes. I decide what happens to each
   comment. Nothing is acted on here.
3. **Finalize** — re-emit the whole action table with every decision applied, and stop. One
   explicit go on *that* table is what authorizes execution.
4. **Execute** — implement the agreed ones, then reply and resolve every thread.

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
| **AI review bot** (`*-code-review[bot]`, `reevo-builder-agent[bot]` — see `builder-agent.md`) | A **hypothesis**, not a finding — a model reading a diff, not a verified defect. Confirm the claim is true of *this* codebase before it earns an action item. **Push back and resolve is a first-class outcome**, not rudeness. |
| **Mohammad** (my own comments) | Authority on **intent and direction** — don't argue about what I want built. But still consequence-check the change it implies: my own comment on salestech-be#31062 moved logic to the service layer and silently invalidated the testing call. Authority over intent isn't authority over side effects. |
| **Another human** | Real context and authority an AI doesn't have. Verify the claim, then default toward implementing. Disagreement is legitimate but needs an argument, not a preference. |

Don't overcorrect into reflexive dismissal. "The bot said it" is not a reason to skip it, and most
bot comments that survive verification are worth doing.

**An approval carrying nits is not a gate.** A review that approves while leaving small comments
still goes through all four steps — the nits get triaged, tiered and resolved like anything else —
but nothing about the PR is blocked while that happens, so don't report it as if it were.

## Step 1 — the report

**Number the comments chronologically** — oldest posted is #1, newest is last, regardless of how
you group them (`github.md`). Action item #N addresses comment #N.

Per comment, three lines at most:

- **#N — `path:line` — <source>** — one line on what it asks.
- **Holds / doesn't hold / can't tell** — what you checked to decide. A claim you couldn't verify
  says so; never launder it into certainty. **A question is not a claim** — there is nothing to
  verify in "why the service layer here?", so don't force it into a verdict; it tiers as *Answer*.
- **Call** — one or two sentences: what you'd do and why.

Then the action items, one line each, in four tiers — the first three reusing `pr-review`'s
vocabulary:

| Tier | Meaning |
|---|---|
| **Implement** | Verified, bounded, and I'd obviously want it. |
| **Push back and resolve** | The claim doesn't hold against this codebase. The reply carries the reasoning. |
| **Answer** | A question, not a claim. Draft the factual answer here; I decide whether I post it or you do. |
| **Bring to me** | A large change, or a genuinely hard call either way. |

**Answer, in full.** GitHub carries answers and decisions — never discussions (`github.md`). So an
*Answer* is a single factual reply that closes the thread, drafted in the report and never posted
unilaterally: I often want to write it myself. Two things it is not. It is not a negotiation —
if the honest reply invites a round trip about whether the code *should* be this way, that's a
discussion, and discussions happen with me or over Slack, so it's a **Bring to me**. And it is
never invented: if the rationale predates your context, say exactly that instead of reconstructing
a plausible one.

**A request to talk overrides every tier above it.** "Can we discuss this?", "let's chat about
the approach", "can we hop on a call" → **Bring to me**, and you author no reply at all. This
needs saying because such a line usually rides along with a real claim ("this is wrong — can we
discuss?"), and triaging on the claim alone would answer the code half with a "done!" while
ignoring what they actually asked for. I handle these offline.

**Scope expansion is its own trigger, independent of size.** "While you're here…", "can you
also…", "separately, could we…", or a comment on a line this diff doesn't touch → **Bring to
me**, never silently implemented. A creep ask can be five lines long and still not belong in this
PR, so size is the wrong axis for it (`no-invented-requirements.md`).

**Read the report as a set before handing it over — reviewers contradict each other.** Two threads
can each verify individually and ask for opposite things of the same file or symbol; triaging
comment-by-comment is exactly what hides that. Scan the finished action items for it, and when it
happens flag the pair together and put **both** in *Bring to me* — never pick a winner. A bot
contradicting a human is the same check with an easy answer: human intent wins, and it still gets
flagged.

**Brevity is the requirement, not a nicety** — this is a thing I skim to find the two comments
that need me. A comment with an obvious answer gets one line, not a paragraph.

Then **stop.** Don't edit code, don't post a reply, don't start on the easy ones because they're
easy. Close with a single line inviting my review — not an offer to start executing, which isn't
on the table until step 3 has been approved.

## Step 2 — my review

Conversational, possibly several rounds. I confirm, override, or re-tier anything.

**Approvals arriving during discussion accumulate — they authorize nothing.** "#1 agreed, #2
agreed" mid-conversation is me working through the list, not releasing you to build. Record it and
keep discussing. It takes effect at step 3 and only there: don't dispatch an implementer, and
don't start on the ones I've already agreed to on the grounds that those are settled.

A round of review is over when *I* close it, not when the approvals look like enough.

## Step 3 — finalize

Discussion doesn't end itself. When it settles, **re-emit the action table in full** — every
comment, every tier, as decided — and then stop.

That table is the artifact I approve, so it has to stand alone:

- **Every override applied.** A tier I moved shows its new tier, not the original with a note.
- **Every open question resolved.** Nothing still reads "open" or "depends on".
- **Anything I never mentioned listed as `Unaddressed`** — a first-class row, never quietly
  carried at its triage tier and never quietly dropped. My silence is neither agreement nor
  refusal, and the row is what turns a guess into a confirmation. Usually I just missed it.
- **The drafted replies carried along**, push-backs and answers included: the wording that lands
  on the thread is part of what I'm approving (`github.md`).

Then wait for **one explicit go on this table**. That go is the only thing that authorizes step 4,
and it covers the table I showed — not the next batch, and not a comment that arrives afterwards.
A new comment restarts at step 1 for that thread.

**A message that mixes discussion with approval is discussion.** Re-finalize and ask again rather
than reading a go into it.

## Step 4 — execute

1. **Dispatch an `implementer`** per action item — product-repo code is never edited from here
   (`delegate-product-code.md`).
2. **The testing call gets re-derived**, and this is the case it exists for: a revision made after
   the PR is open is by definition not covered by the plan, so the implementer works out what the
   change now needs from `mt-devkit/.claude/references/testing-call.md`. A comment that moves code
   into a new layer is exactly the shape that invalidates the original call.
3. **Reply, then resolve, every thread** (`github.md`) — including the push-backs, whose reply is
   the reasoning for not changing anything, and the answers I told you to post. A pushed fix with
   the thread still open is not finished work. Reply via `addPullRequestReviewThreadReply`, resolve
   via `resolveReviewThread`.
   **Voice: terse and factual.** "Done in `<sha>`" is a complete reply. No thanking the reviewer
   for the catch, no restating their comment back at them, no sign-off. A push-back's reply is the
   reasoning and nothing else. Length is not politeness here — a thread is a record, not a
   conversation.
4. **Re-check the PR title and description** after pushing — comment-driven changes are exactly
   the kind that make a description stale (`github.md`). Edit from the **live** body; never
   rebuild it from a local draft, and never touch attached media.
5. **Report**: what changed, what got pushed back, what's still open and why.

## Guardrails

- **Nothing lands before the gate, and the gate is the finalized table.** No edits, no replies,
  no resolves in steps 1–3 — including on items I approved mid-discussion. The whole value is the
  pause, and a partial approval collapses it: a tier I was about to override gets built, and an
  item I forgot to mention gets silently skipped or silently assumed.
- **Verify before you agree, not after.** An action item that says "implement" asserts you checked
  the claim against the code. If you couldn't, it's a *bring to me*.
- **Escalate rather than pick a side.** A large change or a hard judgment call goes to me in the
  report — never decided unilaterally in either direction. Contradicting reviewers are the same
  rule with two threads instead of one.
- **No discussion happens in GitHub** (`github.md`). Answers and decisions land there; anything
  that wants a conversation comes to me, and I take it to Slack or we work it out together.
- **Every thread ends replied-to and resolved**, whichever tier it landed in. `done` gates on it.
- **Report, don't launder.** If a comment was addressed only partly, say which part.
