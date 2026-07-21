# Review Protocol — the three rounds in detail

All three rounds run the same pacing (see SKILL.md): **level then level+1, one bullet at a time, auto-affirm
valid / stop only on shaky, always propose the exact change.** The user says which round and when.

---

## Round 1 — Colors

**Question per bullet:** does the assigned 🟢/🟡/🔴 hold up against the actual evidence and the rubric's
Example Behaviors?

- **Read the Example Behaviors first.** They define the bar. The classic miss: a bullet like "scalability"
  looks satisfied by a complex feature, but the examples are all data/traffic-scale metrics ("cut P90
  500→50ms", "load-tested 10×") — so no proven-at-scale work means 🟡, not 🟢.
- **Catch over-ambition.** A 🟢 resting on co-driven work, unshipped work, or a team metric is really 🟡.
  Flag it and propose the downgrade with the reason.
- **Catch honesty-trap trips** (mirror of the draft's `honesty-traps.md`): PM-authored doc claimed as the
  user's, teammate's PR claimed as "built", incident command with no responder record, whole-domain claim
  in a co-owned domain, unverified counts. Any of these → the color and/or wording needs a fix.
- **Affirm the sound ones.** If the evidence clearly meets the bar, say so in a line and move on — don't
  manufacture doubt.

## Round 2 — Links + wording

**This is where the credibility bugs hide.** Resolve **every** link with real tools — see
`reference/link-verification.md` for the per-source protocol. Flag and give the fix for:

- **Broken/malformed URLs** — e.g. `http://CRMF-761` (not a URL → `https://linear.app/reevo/issue/CRMF-761`);
  generic `app.slack.com/client/.../CHANNEL` deep-links that aren't message permalinks.
- **Wrong attribution** — a PR the user reviewed but didn't author, cited as "built by me" (`gh pr view N
  --json author` catches it).
- **Link lands on the wrong thing** — a permalink resolving to a teammate's "thanks" reply or a bot's
  message instead of the user's own diagnosis/decision. Deep-link the user's own message (with `?thread_ts=`).
- **Label mismatch** — the link's actual title/content doesn't match the claim's wording.

Plus **light wording/grammar** — but don't polish prose that's already fine (per the avoid-polishing rule).
Give the exact replacement text.

## Round 3 — Promotion-case strength

Now zoom out from correctness to persuasiveness of the **level+1 case**.

- **Pillars vs gaps.** Name the 2-3 pillars the case rests on (e.g. leading-through-others, domain
  ownership, flagship delivery) and the honest gaps (e.g. proven-at-scale/performance).
- **The rubric rewards quantified, at-scale impact and leading-through-others** — its Example Behaviors are
  almost all metrics. So: surface the user's **real** numbers (delegation counts, projects led, features
  built — NOT team/product metrics like "100k runs"), and make the leadership pillar unmissable.
- **Be honest about the gaps.** A candid "proven-at-scale is my thinnest area" reads as accurate
  self-assessment, which strengthens the credible parts. Don't paper over a real 🟡.
- **Highest-leverage reworks.** Point at the few changes that most strengthen the case — a pillar that's
  under-stated, a real number not yet surfaced, a 🟡 that a small reframe makes defensible — not a laundry
  list.

---

## After all rounds

Offer a **final re-review** once the user has applied every round's changes — since you won't have seen the
edits live. Re-verify the changed bullets/links end-to-end.
