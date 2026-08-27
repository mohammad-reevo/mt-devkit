---
name: create-testing-party-doc
description: Create a brief, skimmable Notion "testing party" doc for a feature/node, grounded in how the feature actually works (real backend/frontend code + PRD), not just a spec. Triggers on "create/make a testing party doc" for a feature.
---

# Create a Testing Party Doc

Produce a brief, human-toned, skimmable Notion testing-party doc that gets a group of
people testing a feature effectively. The doc must be grounded in how the feature
**actually works** — read the real code and the PRD, don't paraphrase a spec. Keep it
concise enough to skim in a minute, but concrete enough that a tester can configure and
exercise the feature without asking follow-ups.

**The doc is an invitation to find problems, not a catalogue of them.** See §6.

**One interruption.** Research, then hand over a capability menu and let the user say what
to test (§3). Everything the doc needs rides that single checkpoint — don't spread
questions across several turns.

## 1. Gather inputs

Split by when they're actually needed.

**Needed before research** — ask only if genuinely not inferable from the invocation:

- **Feature / node name** being tested.
- **Target Notion page URL** — where the doc gets written (often a blank placeholder page).
- **PRD URL** — often linked off the Linear project; look there before asking.
- **Reference testing-party doc URL** (optional) — for structure only; do **not** copy it.
  Its shape fits *its* feature; derive this doc's shape from this feature (§5).
- **PR context** — which authors and what window. A Linear project's issue assignees
  usually answer this; don't ask what you can look up.

**Not needed until drafting** — never ask up front; these ride the §3 checkpoint:

- **Where to try** — env/org, app link, credentials.
- **Where to report** — Slack channel.

## 2. Research — build the capability menu

The goal of research is a **capability menu**: the testable surfaces, what each one can do,
and what varies across them. That menu is what you hand the user in §3, and it's what the
doc's "What to test" section is built from.

**Research is done when the menu is complete.** Not when you know every UI label — a
handful of real labels is plenty, and harvesting exhaustive click paths is waste that gets
cut in review.

Run these concurrently; keep only the conclusions in the main thread.

- **Recent PRs** — reconstruct the feature arc (renames, redesigns, agent work, evals):
  `gh pr list --repo <org>/<repo> --author <handle> --state all --limit 40 --json number,title,mergedAt,url --search "created:>=<YYYY-MM-DD>"`
  Skim titles — you usually don't need to open the PRs.
- **Notion docs** — fetch the PRD, the reference doc (if any), and the target page with
  the `notion` MCP `fetch` tool.
- **Actual feature logic** — dispatch parallel `Explore` agents (one per side), asking each
  for *what a tester can exercise*, not for a code tour:
  - *Backend*: which surfaces the feature reaches, what varies across them (input types,
    output types, where it can and can't be used), and what a tester sees in run
    history / dry run.
  - *Frontend*: the inventory of capabilities in the UI — every distinct thing a tester
    can click, configure, or generate — plus the handful of labels needed to find them.

**Do not research open bugs, unfinished tickets, or gaps.** That's not what this doc is for
(§6), and it turns a one-checkpoint run into a negotiation.

## 3. Checkpoint — hand over the menu, let the user direct

Stop here. Report:

- **The capability menu** — the surfaces and what's testable on each. Short: a scannable
  list, not an essay. This is the user's menu to choose from, so it should be complete in
  coverage and thin in prose.
- **Anything genuinely ambiguous** about the feature's shape — at most a line or two.
- **The doc inputs still missing** — where to try, where to report.

Then ask what the **"What to test"** section should contain, and wait. The user decides the
test scope; you don't. They may hand you the axes directly, or say "your call from the
menu" — in which case default to: every surface, crossed with composing/configuring and
running/executing, high-level.

Resist re-opening this. One checkpoint, then draft.

## 4. Draft the doc

Use the outline in §5 as a **default starting point, not a fixed template** — reorder,
drop, or add sections as the feature warrants. Lead with what a tester needs.

## 5. Outline (flexible — adapt per feature)

Order matters: orient, then say where, then name the capabilities, then assign the work.
Suggestions come last.

- **Context** — what the feature is and when it's useful, in a few plain sentences. If it
  changes an *existing* surface as well as adding a new one, say so — testers need to know
  the old thing moved.
- **Goal** — what this testing party is trying to learn. Numbered if there's more than one
  thread.
- **Where to try** — env/org and credentials, chained compactly with arrows
  (e.g. `prod X org → app link → 1Password link`).
- **Where to report** — the channel link. Keep it lean; a link is usually enough — don't
  pad with "include a screenshot / expected vs. actual" unless the user asks for it.
- **How it works** — a **capability inventory**, not a click-path walkthrough. Name each
  distinct thing the feature offers with a one-line gloss (a numbered list works well), so
  the next section can assign them. Enough labels to find things, no more.
- **What to test** — **the center of gravity of the doc.** The user's answer from §3,
  rendered as surfaces × activities with concrete axes nested underneath (input types,
  output types, the areas to use it in). This is the assignment; everything above it is
  orientation.
- **Potential use cases** — last, and explicitly optional: ~5 high-level, skimmable ideas.
  **Name the concrete input source in each** (a webhook payload, a created/existing
  account, a form field) so each is directly testable. Invite testers to invent their own.
  These are inspiration, not instruction — "What to test" carries the actual work.

## 6. What does not go in the doc

A testing party exists to *find* problems. Cataloguing them in advance narrows what testers
look at and turns the doc into release notes.

- **No known-issues, bugs, or gaps section.** Don't warn testers off a broken area, don't
  list unfinished tickets, don't flag what isn't built yet. Describe the feature as built.
- **No "not yet supported" lines.** If a surface has no affordance, a tester will simply
  not test it — that costs nothing.
- **Caveats: default off.** A behavioral fact earns a place only if, without it, a tester
  would reasonably conclude "this is broken" (e.g. a function that doesn't exist under the
  name they'll look for). At most two, written inline in the **How it works** section —
  never as a trailing block of their own.

## 7. Writing style

- **Brief and skimmable** — someone should be able to read it in about a minute.
- **Human, low-jargon** — write for a tester, not an engineer. No file paths, class names,
  or internal identifiers in the doc body. Enough detail to act, no more.
- **No literal code or variable syntax in the body** — don't write `{{variables}}`,
  `{{$.trigger.x}}`, or format jargon like "E.164". Say it plainly: "reference previous
  nodes' and the trigger's values through variables", "format a raw phone number".
- **Link sparingly** — only where a tester genuinely needs to go deeper. Don't reflexively
  link the PRD; the user often trims it.
- **Placeholders** only for what the user still owes you after §3 — obvious inline markers
  like `*[link — to add]*`. If they answered at the checkpoint, there are no placeholders.

## 8. Publish

- Write into the **user-provided target page** with the `notion` MCP `notion-update-page`
  tool. For a blank page use `command: "insert_content"` with `position: {"type":"end"}`.
- Do **not** create a new page unless the user asked for one — the target page already
  exists in their doc tree.
- Report back the page URL, plus any placeholders left to fill, then hand it over for their
  revisions.
