# Notion workspace reference — Eng Docs

IDs and mechanics for writing a Reevo eng doc. Fetch live where noted; never
modify the template. If anything here looks stale, the live workspace is the source of
truth — re-fetch and trust it over these notes.

## Key IDs

- **Canonical Eng-Design template (READ-ONLY — never edit):**
  `2b87019cb5b180a895a4e359e54a6d0c` — the section skeleton + per-section guidance
  blockquotes. A near-duplicate copy exists in the DB; standardize on this one.
- **Golden example** (read before drafting; what it shows is in `house-style.md`):
  "Sequences Integration" eng doc — `3df7019cb5b180adb612c0e461e2f999`. Live, so read it for
  patterns, not content.
- **Mini example** (a one-pager; what it shows is in `house-style.md` § The mini example):
  "[Eng Design] - Workflows Duplication Detection Algorithm" —
  `40c7019cb5b180788d65e04117f514cf`.
- **Other exemplar eng docs** (optional, for depth calibration):
  - "[Eng Design] - Workflows Platformization" — `3347019cb5b180a9bce0fd303ea6e8b4`
  - "Technical Design: AI Workflow Debugging" — `3957019cb5b180138995ee4f540fef77`

## Mechanics

- Write into the page the user gives (§1 of the skill). To instantiate the skeleton on an
  empty page: `notion-update-page` `command: "apply_template"`, `template_id:
  2b87019cb5b180a895a4e359e54a6d0c`.
