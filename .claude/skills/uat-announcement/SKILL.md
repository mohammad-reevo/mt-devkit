---
name: uat-announcement
description: Draft or review the Slack message announcing that a feature is in UAT — Slack-ready text in the house shape (emoji opener, one short section per audience — GTM, PO team, EPD — then short Q&A blocks), feature claims grounded in the project's knowledge-base entries and code, and nothing added that wasn't asked for. Two modes — `draft` writes it, `review` checks my draft for factual overclaims and small wording slips and stays short. Triggers on "draft the UAT message", "write the UAT announcement", "review my UAT announcement", "check this UAT post", "/uat-announcement".
---

# uat-announcement — the "now in UAT" Slack post

**UAT** is a feature on in prod for the GTM org only (`knowledge-base/concepts/release/release-stages.md`).
Everyone reading the post knows that — the message never explains it, and never says who has it.

## Router

- **`draft <feature>`** ("draft the UAT message") → **§ Draft**.
- **`review`** ("review my UAT announcement", a pasted draft) → **§ Review**.

## § Draft

1. **Ground the claims.** Read the project's `knowledge-base/projects/<project>/` entries first;
   check the code only for a claim they don't settle. Every capability the post names must exist
   in what shipped (`shipped-work-code-is-truth.md`).
2. **Write it in this shape** — the Outreach Sequences UAT post (2026-10-23) is the model:
   - **Opener** — one emoji-led line: "Our first big integration is now in UAT: <feature> :rocket:"
   - **Hi GTM** — the sales line it unlocks.
   - **Hi PO team** — how to use it: the trigger, the nodes, the setting.
   - **Hi EPD** — how it's built, plus a shoutout.
   - **Q&A blocks**, short: what "<term>" means here, how a customer sets it up, what's coming next.
3. **House tone.** Fun custom emoji (`:wave-birb:`, `:bufo-*:`) belong. Short sections; no headings
   beyond the audience greetings.
4. Output Slack-ready text in one fenced block. Posting is mine.

**Claims stay at "we support it".** List a supported capability plainly — "email clicks" as a
trigger event needs no caveat about link tracking being a per-org setting. Don't qualify how a
supported capability behaves.

**Never add, unasked:**
- an ask to GTM about beta customers
- links to Notion or docs pages
- a feedback-channel line
- known-limitation callouts ("external sequences only show on the timeline")
- "customer setup pending vendor review" caveats

## § Review

Short. The author makes the calls; the review flags only:

- **Factual overclaims** — a claim wider than what shipped ("tracks any data in Outreach" when only
  contacts, enrollments and timeline activity sync). Check against the KB entries / code, and give
  the corrected wording.
- **Small wording and grammar** — "pause into" → "pause in".

Everything on the never-add list above is out of bounds for review suggestions too. No finding is
a valid review: say it reads right.
