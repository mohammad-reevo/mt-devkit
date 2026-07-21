---
name: biyearly-calibration-review
description: Adversarially review an existing calibration draft against Reevo's engineering rubric (E3-E7) in three rounds — color validity, real tool-verified link checking, and promotion-case strength. Companion to biyearly-calibration-draft; run after the draft exists. Collaborative and paced: level then level+1, one bullet at a time, auto-affirm valid / stop only on shaky, always propose exact-change wording. Triggers on "review my calibration", "check my self-evaluation", "calibration review round".
---

# Biyearly Calibration — Review

Run adversarial review rounds on an **existing** calibration draft. The review is roughly **half the total
value** — the draft is the easy part; this is where over-ambition, broken/mis-attributed links, and framing
weaknesses get caught, the kind a human never catches by eye. Produced by `biyearly-calibration-draft`, but
works on any draft the user hands you.

## Inputs

1. **The draft** — Notion page links or a local markdown file.
2. **The rubric** — from the user (paste/file; expect a Google Doc WebFetch to 401). Re-read the **Example
   Behaviors** — they decide ambiguous bullets.
3. **The evidence dossier** if one exists — lets you re-verify without re-sweeping.
4. **Which round(s)** the user wants. The user orchestrates — they say which round, and when.

## The three rounds

Run in this order, but **only when the user asks for each** — they drive the pace.

- **Round 1 — Colors.** Pressure-test every 🟢/🟡/🔴 against the evidence + the Example Behaviors. Catch
  over-ambition (a 🟢 that's really 🟡; a claim that trips an honesty trap). Discuss, don't decree.
- **Round 2 — Links + wording.** **Resolve every link with real tools** (`reference/link-verification.md`) —
  this is where the credibility bugs hide: broken URLs, wrong-attribution PRs, links landing on someone
  else's message, mismatched labels. Plus light grammar/wording.
- **Round 3 — Promotion-case strength.** Pillars vs gaps; the highest-leverage reworks. Be honest about the
  proven-at-scale gap; make the leading-through-others pillar unmissable; surface the user's real numbers.

Detail for each round is in `reference/review-protocol.md`.

## Pacing (how to run every round)

This is a collaborative review the user orchestrates. Hold to it:

- **Level then level+1.** Do all the current-level bullets first, then level+1 (the promotion case).
- **One bullet at a time.** Don't dump the whole round at once.
- **Auto-affirm valid, stop only on shaky.** If a bullet's verdict is sound, affirm it in a line and move on
  automatically. **Stop and discuss only when the verdict is shaky or invalid** — that's where the user's
  attention is worth spending.
- **Always propose the exact change.** When something needs fixing, give the precise wording/color/link to
  change to — not "consider revising." The user applies changes themselves as they see fit.
- **You won't see the user's edits.** The user edits their own doc between rounds and you won't see it live —
  trust them, and offer a final re-review once all rounds' changes are in.

## Non-negotiables

- **Round 2 verifies links with tools, not eyes.** Every link resolved; wrong-attribution and broken URLs
  flagged with the fix. See `reference/link-verification.md`.
- **Honest review.** A 🟢 that should be 🟡 gets flagged, even if it weakens the case — an overstatement a TL
  catches taints every true green.
- **Read the Example Behaviors** before affirming any ambiguous-bullet color.
- **Discuss, don't decree.** Surface the tradeoff and propose; the user owns the final call.
- **Private throughout.** Never post/share/send the draft or the review.
