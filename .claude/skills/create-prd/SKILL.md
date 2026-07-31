---
name: create-prd
description: Create a house-format PRD in Notion from a converged design / product context. Structure is pulled live from the team's PRD template; the doc is drafted in one pass after outline approval, then published to the Eng Docs database on the user's go. Standalone (not part of the scope→plan→implement funnel). Reusable to edit an existing PRD, though the section-by-section editing style lives in a separate rule, not here. Triggers on "create a PRD", "write the PRD for X", "/create-prd".
---

# Create a PRD

Turn a converged design / product context into a house-format **Product Requirements
Doc** in Notion, published to the **Eng Docs** database. This skill owns the *process
and the format* — the section structure comes **live from the team's Notion PRD
template** (never hard-coded here), and the doc stays at **product altitude** (the what
and why, not the engineering how — that's the companion eng-design doc).

**Shape of the run:** one approval gate up front (the outline), a full draft written in
one pass, then the user drives edits, and one publish gate at the end. Keep the main
thread lean — delegate wide reads and research to subagents; think in the main thread.

Sibling skill: `create-eng-doc` (the engineering design that follows the PRD). Same
architecture; this is the PRD half.

## 1. Gather inputs

Collect (or infer from context) whatever isn't provided:

- **The converged design / product context** — the brief, scope doc, ideation notes, or
  ticket the PRD is built from.
- **The feature / workstream** and who owns it (Product / Eng / Design / GTM).
- **A target Notion draft page** — a personal page to write into (created if needed; see
  §5). The PRD is **not** created in Eng Docs until publish.
- **An existing PRD**, if this is an edit rather than a fresh create (see §2).

Hold one rule above the rest: **most-recent source wins.** When an older doc and a newer
one disagree, the newest is authoritative; note the conflict rather than silently
picking one.

Don't over-ask. If the essentials are there, proceed and infer the rest.

## 2. Pull the skeleton from the live template

The section structure is **not** hard-coded in this skill — fetch it live so it tracks
whatever the team changes. Exact IDs in `references/notion-workspace.md`.

- Read the canonical **PRD template** (read-only — never modify it) for the current
  section list + per-section italic guidance prompts.
- Optionally fetch 1–2 recent **exemplar PRDs** from the Eng Docs database to calibrate
  depth and house voice.
- **Create** from scratch: instantiate the skeleton on your draft page — `apply_template`
  the PRD template, or `notion-duplicate-page` it — so the sections + green-bg headings +
  masthead come from the team's own template.
- **Edit** an existing PRD: use it as the base; first confirm it's the real PRD, not a
  roadmap-DB row that merely links to it (a common trip-up).

## 3. Ground it in the product context

A PRD earns its keep at product altitude — the problem, the users, the outcomes. Pull the
substance from the converged design / context (and, where useful, dispatch research
subagents for competitor scans, existing product behavior, or metric definitions). Keep
the noisy exploration in the subagents; only the findings in the main thread.

This is the counterpart to create-eng-doc's "ground in real code": here you ground in the
*product* reality, not the codebase. Implementation detail belongs in the eng-design doc,
not the PRD.

## 4. Propose the outline → get approval

Map the design onto the template's sections. For each: what it will say (1–2 lines).
Apply the PRD authoring judgment in `references/house-style.md` — route each non-goal to
the feature that owns it, frame requirements as P0/P1, and answer the open questions the
design already resolves. Present the outline and **get the user's approval before writing
any prose.** This is the one up-front gate.

## 5. Write the whole PRD in one pass

On approval, write the **full PRD** into the draft page — one pass, not section-by-section.
Then hand it over: the user reviews, edits directly in Notion, and drops comments. Address
their feedback when they ask; **re-fetch the page first** so you build on their edits, not
your last version.

Draft mechanics: write with the `notion` MCP `notion-update-page` tool. The house-style
rules — green-bg `#` H1 headings, the two-column Team/Reference masthead, no H2/H3/dividers,
one-physical-line paragraphs, P0/P1 requirements, non-goal routing — live in
`references/house-style.md`. Follow it.

## 6. Publish on the user's go

Only when the user says go:

- **Create:** **move** the draft into the **Eng Docs** database (`notion-move-pages` → data
  source). Same page id + URL; content and comments preserved.
- **Edit:** copy the finalized body into the official PRD (`replace_content`), preserving
  title + properties; **back up the original first.**
- **Set the row properties** — Doc name, Type: PRD, Status, Product Area, Author/Owner.
  Exact IDs + schema in `references/notion-workspace.md`.
- **Never assign Reviewers, and never treat publishing as automatic.** Requesting review
  and the decision to publish are the user's — surface the doc as ready and stop.

## Guardrails

- **Product altitude** — the PRD states the what/why; engineering *how* goes in the
  companion eng-design doc, never here.
- **Live template, read-only** — the section skeleton comes from the template; never
  hard-code it and never modify the template.
- **Most-recent source wins** on conflicts between docs.
- **No invented requirements** — describe the decided product, not "just in case" behavior.
  A gap the design leaves open is an Open Question, not an invented answer.
- **Surgical on edits** — when editing an existing PRD, keep the author's prose verbatim
  except genuine changes (no polishing). (The section-by-section *diff presentation* is a
  separate doc-editing rule, not this skill.)
- **Response altitude** when synthesizing multi-agent research — lead with the load-bearing
  findings; don't dump transcripts into the doc or the chat.
- **Never assign reviewers; never merge/publish outward** without the user's explicit go.
- **Scratch files** go under `~/.claude/tmp/` (namespaced by the idea slug), never `/tmp`.
- **Standalone** — invoked directly, independent of the scope→plan→implement funnel.
