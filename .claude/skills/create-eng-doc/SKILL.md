---
name: create-eng-doc
description: Create a house-format engineering design doc in Notion from a converged design + its companion PRD. Structure is pulled live from the team's Eng-Design template; substance is grounded in real code via research subagents; the doc is drafted in one pass after outline approval, then published to the Eng Docs database on the user's go. Standalone (not part of the scope→plan→implement funnel). Triggers on "create the eng doc", "write the eng design", "/create-eng-doc".
---

# Create an Engineering Design Doc

Turn a converged design (+ its companion PRD) into a house-format engineering design
doc in Notion, published to the **Eng Docs** database. This skill owns the *process
and the quality bar* — the section structure comes **live from the team's Notion
template** (never hard-coded here), and the substance is **grounded in real code**,
never paraphrased from a spec.

**Shape of the run:** one approval gate up front (the outline), a full draft written
in one pass, then the user drives edits, and one publish gate at the end. Keep the
main thread lean — delegate wide reads and code research to subagents; think in the
main thread.

## 1. Gather inputs

Collect (or infer from context) whatever isn't provided:

- **The converged design** — the "design bible" / scope doc / handoff brief the doc is built from.
- **The companion PRD** — the product contract (requirements, use cases, non-goals). Read it in full.
- **A target Notion draft page** — a personal page to write into (created if needed; see §5).
  The doc is **not** created in Eng Docs until publish.
- **Feature name** and the repos / subsystems the design touches.

Hold one rule above the rest: **most-recent source wins.** These docs are written
iteratively; when the PRD and an older design doc disagree, the newest (usually the
PRD) is authoritative. Note the conflicts explicitly rather than silently picking one.

Don't over-ask. If the essentials are there, proceed and infer the rest.

## 2. Pull the skeleton from the live template

The section structure is **not** hard-coded in this skill — fetch it live so it tracks
whatever the team changes. Exact IDs in `references/notion-workspace.md`.

- Read the canonical **Eng-Design template** (read-only — never modify it) for the
  current section list + per-section guidance blockquotes.
- Optionally fetch 1–2 recent **exemplar eng docs** from the Eng Docs database to
  calibrate depth and house style.
- When you create the draft page you may `apply_template` the template onto it, so the
  skeleton is instantiated from the team's own template.

## 3. Ground it in real code (auto-dispatch research)

This is the step that makes the doc *engineering*, not hand-waving. Fan out **research
subagents** (`Explore` / `general-purpose`) into the actual repos to map every
subsystem the design touches — existing services being reused, the precedent being
copied, the integration points. Have them return real `file:line` / service / function
names; keep the noisy exploration inside the subagents and only the findings in the
main thread.

Ground every load-bearing claim in a real identifier. "The resolver" is weak;
"`TemplateResolver` (`core/flow/runtime/template.py`)" is the house standard — see the
exemplars.

## 4. Propose the outline → get approval

Map the design onto the template's sections. For each: what it will say (1–2 lines),
and **flag sections that are N/A** for this feature, honestly (a pure-backend feature
has no Object Schema Changes; a reuse-only feature may have a trivial Security section
worth cutting). Present the outline and **get the user's approval before writing any
prose.** This is the one up-front gate.

## 5. Write the whole doc in one pass

On approval, write the **full doc** into the draft page — one pass, not
section-by-section. Then hand it over: the user reviews, edits directly in Notion, and
drops comments. Address their feedback when they ask; **re-fetch the page first** so
you build on their edits, not your last version.

Draft mechanics: write with the `notion` MCP `notion-update-page` tool
(`insert_content` / `replace_content` for a fresh page). The house-style rules —
numbered `## N.` headings, `---` dividers, masthead, answered `<details>` toggles,
one-physical-line paragraphs, honest N/A, the New/Changed/Reuses appendix — live in
`references/house-style.md`. Follow it.

## 6. Publish on the user's go

Only when the user says go:

- **Move** the draft into the **Eng Docs** database (`notion-move-pages` → data
  source). This preserves the page, its content, comments, and URL.
- **Set the row properties** — Doc name, Type: Eng Design, Status, Product Area,
  Author/Owner. Exact IDs + property schema in `references/notion-workspace.md`.
- **Never assign Reviewers, and never treat publishing as automatic.** Requesting
  review and the decision to publish are the user's — surface the doc as ready and stop.

## Guardrails

- **Ground in real code** — every load-bearing claim traces to a real identifier (§3).
- **Most-recent source wins** on conflicts between the PRD and older design docs.
- **No invented requirements** — describe the decided design, not "just in case"
  behavior. A gap the design leaves open is an Open Question, not an invented answer.
- **Response altitude** when synthesizing multi-agent research — lead with the
  load-bearing findings; don't dump transcripts into the doc or the chat.
- **Never assign reviewers; never merge/publish outward** without the user's explicit go.
- **Scratch files** go under `~/.claude/tmp/` (namespaced by the idea slug), never `/tmp`.
- **Standalone** — invoked directly, independent of the scope→plan→implement funnel.
