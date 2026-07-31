# House style — Reevo PRDs (Notion)

How to fill the PRD template *well*. The template gives the headings + a one-line italic
prompt per section; this is the quality bar + the authoring judgment on top. Structure
comes from the live template — this file is the "how to fill each section" layer.

## Structure & formatting

- **All section headings are top-level `#` H1 with a green background:**
  `# Heading {color="green_bg"}`. This applies to the masthead headings and every body
  section. No H2/H3, no dividers, no toggles — flat green H1s are the one visual convention.
- **Masthead at the top** — a two-column block: left `# Team` + a small table
  (Design / Product / Engineering / GTM → names), right `# Reference docs` + one link per
  line. Preserve the two-column layout and green headings from the template.
- **One physical line per paragraph** — Notion renders hard-wrapped prose with broken line
  breaks. Bullets stay one item per line.
- **Section set** comes live from the template (currently: Overview · Goals · Non-goals ·
  Success metrics · User stories · Requirements · Proposed solution · Competitor analysis ·
  Use cases · Dependencies · Open questions). Follow whatever the live template says.
- **Italic section prompts** — the template seeds each section with a one-line italic
  guidance prompt. Replace it with real content (or keep it as a hint while drafting and
  strip on finalize — the user's call).

## The quality bar (what makes it a good PRD)

- **Product altitude.** State the problem, the users, the outcomes, the scope. Name
  architectural touchpoints only in behavior/contract terms — the engineering *how* lives
  in the companion eng-design doc, not here.
- **Requirements as P0 / P1**, with stable **R-numbers** (R1, R2, …) so they're traceable in
  review; annotate build-state if useful.
- **Route each non-goal to the feature that owns it** — an exclusion that points at the
  feature covering it is stronger than a bare "out of scope."
- **Answer the open questions the design already resolves.** Pose *and* answer (or give the
  current lean); a bare unanswered list is weaker. Genuinely-open items stay open.
- **Success metrics** mix adoption + quality/error rates + a qualitative "reduction in
  'I had to manually do X'" signal.
- **No invented requirements** — unsettled points go in Open Questions, never guessed into
  the body.

## Authoring judgment (recurring gotchas)

- **Roadmap-row check** — the "existing PRD" you're handed may be a roadmap-DB row that just
  links to the real PRD. Follow the link before editing.
- **Diff the design before rewriting** — when updating an existing PRD, compare the new design
  against it and surface divergences to the user before editing; don't silently rewrite a
  PM-owned doc.
- **Capability-gap check** — when a decision removes/deprecates something (a node, a flow), ask
  what capability that leaves unserved and address it (cover it, or defer it as a named
  non-goal / open question).
- **Verbatim except deltas** — on edits, keep the author's exact wording everywhere the
  substance didn't change; the diff should contain only functional changes.

## Enhanced-markdown quirks (Notion MCP)

- If unsure of syntax, fetch `notion://docs/enhanced-markdown-spec` via `notion-fetch` — don't guess.
- `{color="green_bg"}` after a heading gives the green background; `<columns>` + a
  `<table header-row="true" header-column="true">` builds the masthead.
- Edit with `update_content` (targeted search/replace) for small changes; `insert_content` to
  append; `replace_content` for a full rewrite. Prefer the smallest edit that captures the
  change, and match special characters exactly (em dashes, arrows, curly quotes) or the search
  won't match.
