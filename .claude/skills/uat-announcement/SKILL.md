---
name: uat-announcement
description: Work out a "now in UAT" Slack announcement with me — a discussion, not a generator. I get creative with these, so the skill asks how I want this one to go (the angle, the hook, who it speaks to, whether I'd rather write it by hand), grounds what the feature actually does, offers ideas, and drafts only what we've agreed; the Outreach Sequences UAT post is a reference point, never a template. A `review` mode checks a draft for factual overclaims and small wording slips and stays short. Triggers on "UAT announcement", "help me write the UAT message", "let's do the UAT post", "review my UAT announcement", "check this UAT post", "/uat-announcement".
---

# uat-announcement — the "now in UAT" Slack post, worked out together

**UAT** is a feature on in prod for the GTM org only (`knowledge-base/concepts/release/release-stages.md`).
Everyone reading the post knows that — the message never explains it, and never says who has it.

These posts are mine and I get creative with them. The skill's job is to help me write a good
one, not to produce one: ask, suggest, ground the facts, and draft only as much as I want drafted.

## Router

- **`write`** (default — "help me write the UAT message", "let's do the UAT post") → **§ Write it together**.
- **`review`** ("review my UAT announcement", a pasted draft) → **§ Review**.

## § Write it together

1. **Ground the facts first, quietly.** Read the project's `knowledge-base/projects/<project>/`
   entries; check the code only for a claim they don't settle (`shipped-work-code-is-truth.md`).
   This is what keeps the post honest — it isn't shown back as a wall.
2. **Ask how I want to do it** — a few short questions, one at a time (`discussion-turns.md`):
   - What's the feature, in my words, and what's the one thing people should take away?
   - Any angle or hook this time — a theme, a bit, a running joke, a format twist?
   - Who is it talking to (GTM, the PO team, EPD — all, some, or someone else)?
   - Do I want to write it myself and have it reviewed, or build it up together?
   Skip a question the conversation already answered.
3. **Offer ideas, not a finished post.** A couple of openers or hooks to react to, which audience
   lines carry the most, what a short Q&A might cover. Name the one you'd pick.
4. **Draft only what's agreed**, in my voice, and iterate on my edits. When I'm writing it by hand,
   stop at ideas and hand over to § Review when I paste it.

**Reference point, not template.** The Outreach Sequences UAT post (2026-10-23) went: an
emoji-led opener ("Our first big integration is now in UAT: <feature> :rocket:"), one short
section per audience — *Hi GTM* (the sales line it unlocks), *Hi PO team* (how to use it),
*Hi EPD* (how it's built + a shoutout) — then short Q&A blocks (what "<term>" means here, how a
customer sets it up, what's coming). Custom emoji (`:wave-birb:`, `:bufo-*:`) are house tone.
Bring it up as one way it has worked when it helps; never default to reproducing it.

**Claims stay at "we support it".** A supported capability is listed plainly — "email clicks" as
a trigger event needs no caveat about link tracking being a per-org setting.

**Never suggest, unasked:**
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

Style, structure and creative choices are mine — not review findings. The never-suggest list
applies here too. No finding is a valid review: say it reads right.
