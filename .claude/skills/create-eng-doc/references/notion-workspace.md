# Notion workspace reference — Eng Docs

IDs and mechanics for the Reevo **Eng Docs** database. Fetch live where noted; never
modify the template. If anything here looks stale, the live workspace is the source of
truth — re-fetch and trust it over these notes.

## Key IDs

- **Eng Docs database (data source):** `1bc7019c-b5b1-8021-bce5-000b4b24dbc5`
  (collection URL `collection://1bc7019c-b5b1-8021-bce5-000b4b24dbc5`).
- **Canonical Eng-Design template (READ-ONLY — never edit):**
  `2b87019cb5b180a895a4e359e54a6d0c` — the section skeleton + per-section guidance
  blockquotes. A near-duplicate copy exists in the DB; standardize on this one.
- **Exemplar eng docs** (fetch for depth / house-style calibration):
  - "[Eng Design] - Workflows Platformization" — `3347019cb5b180a9bce0fd303ea6e8b4`
  - "Technical Design: AI Workflow Debugging" — `3957019cb5b180138995ee4f540fef77`

## Draft → publish mechanics

1. **Draft** in a personal page first (write into a page the user gives you, or create
   one under their Drafts). Optionally instantiate the skeleton with
   `notion-update-page` `command: "apply_template"`, `template_id:
   2b87019cb5b180a895a4e359e54a6d0c`.
2. **Publish** = `notion-move-pages` with
   `new_parent: {type: "data_source_id", data_source_id: "1bc7019c-b5b1-8021-bce5-000b4b24dbc5"}`.
   Same page id + URL; content and comments are preserved.
3. **Set properties** with `notion-update-page` `command: "update_properties"`.

## Eng Docs property schema (for `update_properties`)

- **Doc name** (title) — e.g. `[Eng Design] - <Feature> in <Area>`.
- **Type** (multi-select) — `["Eng Design"]`.
- **Status** (status) — one of `Backlog` / `Planning` / `In progress` / `Paused` /
  `Done` / `Canceled`. New docs usually → `Planning` (confirm with the user).
- **Author(s)** and **Owner** (person) — arrays of Notion user IDs. Resolve the current
  user with `notion-fetch self`.
- **Product Area** (multi-select) — e.g. `["Workflows"]` (options include Core CRM, AI,
  Reporting, Infrastructure / Platform, …).
- **Reviewers** (person) — **leave blank. The user assigns reviewers, never the skill.**

## Notes

- To refresh property options, fetch the live schema:
  `notion-fetch collection://1bc7019c-b5b1-8021-bce5-000b4b24dbc5`.
- `notion-fetch self` returns the connected user's id / name / email — use it for
  Author / Owner.
