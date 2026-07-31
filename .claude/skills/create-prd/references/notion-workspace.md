# Notion workspace reference — Eng Docs (PRD)

IDs and mechanics for publishing a PRD to the Reevo **Eng Docs** database. Fetch live
where noted; never modify the template. If anything here looks stale, the live workspace
is the source of truth — re-fetch and trust it over these notes.

## Key IDs

- **Eng Docs database (data source):** `1bc7019c-b5b1-8021-bce5-000b4b24dbc5`
  (collection URL `collection://1bc7019c-b5b1-8021-bce5-000b4b24dbc5`). PRDs and eng-design
  docs are sibling rows in this same database.
- **Canonical PRD template (READ-ONLY — never edit):**
  `2ab7019cb5b1802289aac32876c60803` — title `[Template] (PRD) [Workstream]: [Feature
  Description]`; the section skeleton + per-section italic guidance prompts.
- **Exemplar PRDs** (fetch for depth / house-voice calibration): search the Eng Docs DB
  for recent `(PRD)` rows.

## Draft → publish mechanics

1. **Draft** in a personal page first (write into a page the user gives you, or create one
   under their Drafts). Instantiate the skeleton with `notion-update-page`
   `command: "apply_template"`, `template_id: 2ab7019cb5b1802289aac32876c60803` — or
   `notion-duplicate-page` the template and retitle it.
2. **Publish (create)** = `notion-move-pages` with
   `new_parent: {type: "data_source_id", data_source_id: "1bc7019c-b5b1-8021-bce5-000b4b24dbc5"}`.
   Same page id + URL; content and comments preserved.
3. **Publish (edit)** = copy the finalized body into the existing PRD with `notion-update-page`
   `command: "replace_content"` (back up the original first); title + properties are preserved.
4. **Set properties** with `notion-update-page` `command: "update_properties"`.

## PRD property schema (for `update_properties`)

- **Doc name** (title) — `(PRD) <Workstream>: <Feature Description>` (drop the `[Template]`
  prefix; fill the bracketed tokens).
- **Type** (multi-select) — the PRD option (`["PRD"]`; confirm the exact option name from
  the live schema).
- **Status** (status) — one of `Backlog` / `Planning` / `In progress` / … . New PRDs usually
  → `Planning` (confirm with the user); the template ships as `Backlog`.
- **Author(s)** and **Owner** (person) — arrays of Notion user IDs. Resolve the current user
  with `notion-fetch self`.
- **Product Area** (multi-select) — e.g. `["Workflows"]`.
- **Reviewers** (person) — **leave blank. The user assigns reviewers, never the skill.**

## Notes

- To refresh property options / confirm exact names, fetch the live schema:
  `notion-fetch collection://1bc7019c-b5b1-8021-bce5-000b4b24dbc5`.
- `notion-fetch self` returns the connected user's id / name / email — use it for Author / Owner.
