# Impact Framing — write for impact, not a PR list

The most common failure of a first draft is a **wall of "built X (PR)"** — technically cited, but
unreadable and impact-free. A calibration is an *argument*, not a changelog. Every headline claim has to
tell the reader *why it mattered*, in the user's own voice. This is what separates a credible draft from a
dump of `(PR)(PR)(PR)`.

## The rule: every headline claim carries a "why"

For each evidence bullet, lead with one of three kinds of impact — whichever is true and strongest:

- **User impact** — the tangible customer benefit. *("narrows hundreds of candidate variables down to the
  type-compatible handful, making workflows materially easier for customers to build")*
- **Business / strategic importance** — how it aligned with a company priority. *("a core pillar of Golden
  Workflows, the inbound-lead-engine at the center of the company's product strategy")*
- **Technical complexity** — the hard problem solved. *("kept the validation model and picker model from
  drifting; resolved non-identifier JSONPath paths on both backend and frontend")*

If a bullet can't carry any of the three, it's probably not load-bearing — cut it, or fold it into a count.

## Before → after (the transformation to make)

- ❌ "Built the dynamic variable suggestion service ([PR])."
- ✅ "Built the variable-suggestions engine that narrows hundreds of candidate variables down to the
  type-compatible handful — turning an overwhelming list into a couple of clicks ([PR])."

- ❌ "Contributed to the editability release, completing 79 tickets ([Linear])."
- ✅ "Contributed to the editability release — the launch that shipped v1 of the product to all users and
  made it usable end-to-end — completing 79 tickets across it ([Linear])."

## Style (how the user's real doc reads)

- **First person, concrete, liftable** — "I built / I drove / I caught", so it drops straight into the
  user's own doc.
- **Honest verbs matched to the git record** — "architected / built out / extended / contributed to", not
  "built from scratch" when the primitive predates the user (cross-ref `honesty-traps.md`). A verb the git
  blame contradicts sinks the whole claim.
- **Readability over completeness** — pick the load-bearing PRs and *explain* them; don't chain five links
  after one claim. Breadth goes in a count ("326 PRs"); depth goes in a few explained examples.
- **The user's own numbers, not team metrics** — "delegated 22 tickets", "supports 45 nodes", not
  "100k product runs" (cross-ref `honesty-traps.md`, trap #6).

## The impact-hardening pass (how the doc is actually built)

After the first cited draft, run a dedicated pass — this is where most of the value is:

1. **Ask the "why" of every bullet.** Read each one and ask *"what's the user / business /
   technical-complexity why?"* If it's missing, add it; if there's no honest why, cut the bullet.
2. **Harden project importance.** Was the work part of a flagship initiative, or the v1 of the product?
   Borrow that significance for the *project* — honestly, and kept separate from the user's *role* in it
   (a team release stays "contributed to" even while you elevate the project's importance).
3. **Collapse PR-dumps.** Replace "(PR)(PR)(PR)" after one claim with a single explained example plus a
   count.
4. **Keep the honest dial visible.** When hardening a strategic claim ("primary product strategy"), flag it
   as a business claim only the user can confirm, and let them dial the strength ("a flagship initiative"
   vs "the primary strategy").

Run this pass **collaboratively**: surface each hardening candidate as a specific *before → after* (ideally
with a Ctrl+F search string so the user can find it in their doc), and let the user apply it as they see
fit. The user's judgment on strength and honesty is the final filter.
