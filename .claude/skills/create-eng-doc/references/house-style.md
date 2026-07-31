# House style — Reevo eng docs (Notion)

How to fill the template *well*. The template gives headings + placeholder guidance;
this is the quality bar the exemplars set. Structure comes from the live template — this
file is the "how to fill each section" layer.

## Structure & formatting

- **Numbered top-level sections**, `## N. Title` (H2), matching the template's
  numbering and order. If you drop or move a section, renumber cleanly and fix any
  cross-references (`§N`) that point at it.
- **`---` divider between sections** (the template uses them).
- **Masthead at the top**, before §1: Author(s), Created, Last Updated, Reviewers,
  Status, and a **Companion PRD** link. Trailing double-space for the soft line breaks;
  `<mention-date start="YYYY-MM-DD"/>` for dates (use the real current date, don't guess).
- **Open questions as answered `<details>` toggles** — `<summary>the question</summary>`
  with the resolution / current lean inside (tab-indented). Pose *and* answer (or give
  the current thinking); a bare unanswered list is weaker.
- **One physical line per paragraph** — Notion renders hard-wrapped prose with broken
  line breaks. Bullets stay one item per line.

## The quality bar (what makes it "engineering")

- **Ground every load-bearing claim in a real identifier** — a service, file
  (`path/to/file.py`), function, or PR number. This is the defining trait of the
  exemplars. Name the thing; "the resolver" is not enough.
- **Drop N/A sections honestly.** If a template section doesn't apply, write
  `N/A — <one line why>` (e.g. §6.1 Object Schema Changes for a feature that adds no
  core-object fields) rather than padding it. Cutting an entirely-irrelevant section is
  fine — just say you did.
- **Diagrams inline** where they earn their place — an ASCII architecture / data-flow
  diagram in a code fence (the exemplars use ` ```markdown ` / ` ```javascript `), a
  sample payload as ` ```json `.
- **Appendix lists files touched** as **New / Changed / Reuses**, per repo (backend and
  frontend). House convention.
- **Altitude:** the doc states the *decided* design and names the touchpoints; it is not
  a line-by-line implementation plan. Push exhaustive detail to build time. Unsettled
  points go in Open Questions, never invented in the body.

## Enhanced-markdown quirks (Notion MCP)

- If unsure of syntax, fetch `notion://docs/enhanced-markdown-spec` via `notion-fetch` —
  don't guess.
- `<details>` / `<summary>` for toggles; `<table header-row="true">` with `<tr>` / `<td>`
  for tables. `{color="green_bg"}` highlights a heading (PRD-style; the eng template uses
  plain H2, so rarely needed here).
- Edit with `update_content` (targeted search/replace) for small changes; `insert_content`
  to append; `replace_content` for a full rewrite. Prefer the smallest edit that captures
  the change, and match special characters exactly (em dashes, arrows, curly quotes) or
  the search won't match.
