---
name: biyearly-calibration-draft
description: Build a private, fully-cited self-evaluation against Reevo's engineering rubric (E3-E7) for a 6-month window — assessing your level and, for a promotion case, level+1. Sweeps every connected source (git/PR, Linear, Slack, Notion, Datadog, Rootly, Sentry), adversarially confirm-or-kills claimed strengths, applies an honesty-traps checklist, and writes a graded draft in the rubric's own submittable format. Pairs with biyearly-calibration-review. Triggers on "draft my calibration", "start my self-evaluation", "calibration self-review".
---

# Biyearly Calibration — Draft

Produce a **private, fully-cited** self-evaluation of the user's work against Reevo's engineering-level
rubric, for a 6-month review window. Assess the user's **current level** and — for a promotion case —
**level+1**. Every colored conclusion is backed by evidence: a **PR#**, a **Notion doc with verified
authorship**, or a **manually-attested action with a named voucher**. No uncited grades.

This skill produces the draft. The companion **`biyearly-calibration-review`** skill runs the adversarial
review rounds on it — the review is roughly half the value, so plan to run it after.

## Core stance — you dig, the user writes

You are the evidence engine and the honest second opinion, not the author of record. The user owns the
final wording and the final call on every color. Your job: surface real evidence with real citations,
map it to the rubric honestly, kill the claims that don't survive scrutiny, and hand back a draft the
user can lift into their own doc. When you're unsure whether a claim is fair, **flag it for the user
rather than deciding for them** — the user's honest filter ("that's not really mine") is what keeps the
case credible.

## Required inputs — collect these FIRST, before any analysis

1. **Level to assess — ASK the user, never assume.** Ask their **current level (E3–E7)** AND **whether to
   also assess level+1** (the promotion case). Use AskUserQuestion or a direct question up front — don't
   infer the level from the work, and don't assess level+1 unless the user asks for it.
2. **Review window.** **H1 = Jan 1 – Jun 30**, **H2 = Jul 1 – Dec 31**. Confirm the year. Nothing outside
   the window counts (`git --until` is exclusive — use the 1st of the next month).
3. **The current rubric — from the user.** Ask them to paste it or point to a local file. **Expect a
   WebFetch of the Google Doc to 401** — don't rely on fetching it. The rubric changes each cycle
   (new sections, reworded bullets, new Core Baselines); re-read it every run. Read the **Example
   Behaviors** — they are the interpretive key (see below), not decoration.
4. **Identities & repos.** Git author **email** (name ≠ email), GitHub login, and the handles for whatever
   sources are connected (Linear / Slack / Notion / Datadog / Rootly / Sentry user IDs), plus the repos to
   scan.
5. **Output target — ask up front.** Notion (you create/collect the page links) **or** a local markdown
   file. See `templates/draft-template.md` for the structure either way.

## The workflow

Run these in order. Fan work out to **read-only subagents** (one per source/angle, in parallel) so the
orchestrator stays lean — each returns lean *cited* findings (permalinks / PR# / issue IDs), not raw dumps.
The concrete tools and queries for each source live in `reference/evidence-sweep.md`.

1. **Resolve git identity.** `git log --pretty='%an <%ae>' | sort | uniq -c` in each repo → filter on the
   **email** (a wrong filter silently returns zero).
2. **Pull authored PRs + the review footprint.** Authored PRs = shipped work; reviews = mentoring + reach.
3. **Wave 1 fan-out (parallel):** Notion authored docs (authorship verified), Linear ownership **and
   delegation**, flagship PRs by churn, Slack + Datadog leadership/reliability. See `reference/evidence-sweep.md`.
4. **Synthesize interim.** Name the **domain** the user works in, the **spine** of their case (e.g.
   leads-through-others), and the evidence streams that support it.
5. **Map every rubric bullet** at level and level+1 → first-pass 🟢/🟡/🔴 with citations. **Use the Example
   Behaviors as the interpretive key** for any ambiguous bullet — read `reference/grading.md`.
6. **Attestation pass** for bullets code/docs can't prove (interviewing, mentoring formality, user research,
   proven-at-scale, org-wide talks): require **(a) what you did + (b) a named voucher**, or an explicit N/A.
7. **Wave 2 deepen + confirm-or-kill.** Deepen the thin/high-value bullets (customer issues, on-call,
   cross-team reach, review *substance*, stakeholder tension) AND run a dedicated pass that **tries to
   disprove the strongest claims** — unshipped work and mis-attributed PRs die here.
8. **Apply the honesty-traps checklist** (`reference/honesty-traps.md`) continuously — correct
   overstatements, bake honesty caveats inline.
9. **Write the outputs** in the rubric's own submittable format (`templates/draft-template.md`) — writing
   every claim **for impact, not as a PR list** (`reference/impact-framing.md`).
10. **Impact-hardening pass.** Re-read each bullet and ask "what's the user / business / technical-complexity
    *why*?" Rewrite soft "built X (PR)" bullets to lead with the impact; collapse PR-dumps to one explained
    example plus a count. This pass is where a readable, persuasive draft is actually made.

## The five disciplines (read the reference files)

- **Evidence sweep** — `reference/evidence-sweep.md`: the hard-coded MCP sweep (git/gh, Linear, Slack,
  Notion, Datadog, Rootly, Sentry) plus "sweep whatever else is connected." Linear's delegation signal is
  the E4 headline; Slack permalink verification is the key trick; Rootly/Sentry gaps are honest findings.
- **Honesty traps** — `reference/honesty-traps.md`: the recurring overstatement traps. Applied continuously,
  not once.
- **Grading** — `reference/grading.md`: 🟢/🟡/🔴 discipline and why the Example Behaviors decide ambiguous
  bullets (data/traffic scale, co-driver vs owner, DRI-of-surface vs whole-domain).
- **Impact framing** — `reference/impact-framing.md`: write for impact, not a PR list. Every headline claim
  carries a user / business / technical-complexity *why*, in the user's first-person voice, at readable
  altitude. This is the difference between a credible draft and an unreadable dump of "(PR)(PR)(PR)".
- **Output format** — `templates/draft-template.md`: the per-bullet submittable format + the 3-doc output.

## Non-negotiables

- **Every colored conclusion cites evidence** — PR#, authorship-verified Notion doc, or attestation +
  named voucher. No uncited grades.
- **Private output the user controls.** Never post, share, or send it. The user hands it to their TL.
- **Window discipline** — exclude everything outside the 6-month window.
- **Honest colors.** A TL who knows the work reads this; overstatement backfires and taints the true
  greens. Keep real 🔴s; describe gaps and ceilings plainly.
- **Read the Example Behaviors before grading ambiguous bullets** — they define what a bullet actually means.
- **Surface the user's OWN numbers, not team/product metrics.** Delegation counts, projects genuinely led,
  features built are fair; "100k product runs" is team impact, not personal.
- **Write for impact, not a PR list.** Every headline claim leads with a user / business /
  technical-complexity *why*, in the user's first-person voice — never a bare "built X (link)".
  Readability is part of the deliverable. See `reference/impact-framing.md`.
- **When unsure, flag — don't decide.** Hand judgment calls to the user.
