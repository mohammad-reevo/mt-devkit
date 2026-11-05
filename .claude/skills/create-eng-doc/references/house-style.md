# House style — Reevo eng docs (Notion)

How to fill the template *well*. The template gives headings + placeholder guidance;
this is the quality bar the exemplars set. Structure comes from the live template — this
file is the "how to fill each section" layer.

## Structure & formatting

- **Numbered top-level sections**, `## N. Title` (H2), matching the template's
  numbering and order. If you drop or move a section, renumber cleanly.
- **Self-contained sections — no in-doc cross-references.** Each section reads on its own,
  top to bottom. Never write "see §4.3", link to another heading, or "(described below)";
  restate the one fact the reader needs instead. In review, a cross-reference is a must-fix.
  Give a distinct piece (a trigger, a node) its own subsection beside its peers rather than a
  sub-bullet of a component list that other sections then point back to.
- **`---` divider between sections** (the template uses them).
- **No masthead.** The doc opens at §1; author, status and reviewers live on the Eng Docs
  row's properties, which the user sets.
- **Trailing full stops: ask once.** Mohammad's docs end no paragraph or bullet with a full
  stop. Ask at the outline whether this doc follows that, then apply it in every section.
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
  a line-by-line implementation plan. Name services, modules and functions; leave `file:line`
  detail to `implementation-details.md` (SKILL.md §5). Unsettled points go in Open Questions,
  never invented in the body.
- **No progress status.** A design doc describes the design, not where the work stands —
  no "done", "in review", "shipped", and no ticket cells carrying a status.

## The golden example

The live Sequences Integration eng doc (ID in `notion-workspace.md`) is the reference for
how a finished doc looks. Read it before drafting and match its patterns — not its project
content. What it shows:

- **Background split by system** — the native side, the vendor side and the platform /
  kernel side as one table, rather than three prose blocks.
- **Architecture as chart + bullets + one paragraph** — an ASCII chart, then one bullet per
  component, then one paragraph on how the pieces are registered.
- **A journey worked in full, the rest as a table** — one example journey step by step, then
  a short table of the other journeys.
- **One of a kind in full, the rest as a table** — the first node described completely, its
  siblings in a table of only what differs.
- **Cross-cutting sections as short bolded bullets** — security, observability, rollout,
  testing and the like: one bolded lead per point, a sentence or two each.
- **Appendix of files as New / Changed / Removed / Reuses, per repo.**

## The mini example

The Workflows Duplication Detection doc (ID in `notion-workspace.md`) is the reference for a
mini design doc — one algorithm, no PRD, `Category: One-pager`. Read it for patterns, not
content. What it shows:

- **Five sections, no padding** — Overview, Goals and Non-goals, Background / Context,
  Proposed Architecture, and one "How OOTB Workflows Will Use This" section. No API, Data
  Model, Security, Rollout, Open Questions or Appendices sections, and no N/A stubs for them.
- **Background as the problem, then the current state in code** — why it matters, with a
  real prod number, then the existing services and the one existing check it improves on.
- **Architecture grows subsections as it needs them** — overview with an ASCII chart and a
  mapping table, scoring, classification and limits, validation, performance.
- **One worked example with real numbers, the rest as a table** — a single pair scored step
  by step, then a short table of pairs and the class each gets.
- **Validation against real data** — the design hand-scored against one org's real
  workflows in a table with a "Correct?" column, then the design changes the test forced.
- **The consumer section as bolded bullets** — what gets compared, where it runs, what the
  user sees, what stays with the user.
- **No trailing full stops.**

## Enhanced-markdown quirks (Notion MCP)

- If unsure of syntax, fetch `notion://docs/enhanced-markdown-spec` via `notion-fetch` —
  don't guess.
- `<details>` / `<summary>` for toggles; `<table header-row="true">` with `<tr>` / `<td>`
  for tables. `{color="green_bg"}` highlights a heading (PRD-style; the eng template uses
  plain H2, so rarely needed here).
- `replace_content` for the first full write of a fresh page; `insert_content` to append
  (a large page goes up in chunks — `replace_content`, then `insert_content` ×N).
- **After the draft, prefer handing the user wording over editing.** `update_content`
  re-serializes the whole page and can corrupt formatting far from the edit — a bullet whose
  text starts with `# ` (e.g. "# of steps") splits into an empty bullet plus an indented
  line. When an edit is handed over, make **one replacement per call**, never a batch, and
  re-fetch after to check nothing else moved. Match special characters exactly (em dashes,
  arrows, curly quotes) or the search won't match.
