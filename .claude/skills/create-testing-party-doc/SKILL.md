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

## 1. Gather inputs

Ask for (or infer from context) whatever isn't already provided:

- **Feature / node name** being tested.
- **Target Notion page URL** — where the doc gets written (often a blank placeholder page).
- **PRD URL** — the source of truth for goals and use cases.
- **Reference testing-party doc URL** (optional) — for structure only; do **not** copy it.
- **PR context** — which authors and what time window (e.g. "past month from X and Y")
  to skim for the feature's recent development arc.
- **Where to try** and **Where to report** — env/org, credentials location, Slack channel.
  Any the user owns become clearly-marked placeholders in the doc (see §5).

Don't over-ask. If the user gave you the essentials, proceed and infer the rest.

## 2. Research (run in parallel)

Do these concurrently; keep only the conclusions in the main thread.

- **Recent PRs** — list the named authors' PRs across the relevant repos to reconstruct
  the feature arc (renames, redesigns, agent work, evals):
  `gh pr list --repo <org>/<repo> --author <handle> --state all --limit 40 --json number,title,mergedAt,url --search "created:>=<YYYY-MM-DD>"`
  Skim titles — you usually don't need to open the PRs.
- **Notion docs** — fetch the PRD, the reference doc (if any), and the target page with
  the `notion` MCP `fetch` tool.
- **Actual feature logic** — dispatch parallel `Explore` agents (one per side) so the doc
  reflects real behavior, not the PRD's intent:
  - *Backend*: config/schema, execution path, inputs/outputs, validation, failure modes,
    any agent/eval harness.
  - *Frontend*: the config panel UX, the instructions/prompt box, variable pickers,
    output bindings, run-history display, any AI-assist buttons.
  Tell each agent to report file paths + concrete detail (key fields, prompt structure,
  UI labels the user actually sees), organized by a short numbered list you give it.

## 3. Draft the doc

Use the outline in §4 as a **default starting point, not a fixed template** — reorder,
drop, or add sections as the feature warrants. Lead with what a tester needs.

## 4. Outline (flexible — adapt per feature)

Order matters: lead with what/why and the actionable bits; push reference detail to the
end. This default ordering worked well — adapt per feature.

- **Context** — what the feature is and when it's useful, in a few plain sentences.
- **Goal** — what this testing party is trying to learn (accuracy, edge cases, an agent's
  quality, etc.). Numbered if there's more than one thread.
- **Where to try** — env/org and credentials, chained compactly with arrows
  (e.g. `prod X org → app link → 1Password link`).
- **Where to report** — the channel link. Keep it lean; a link is usually enough — don't
  pad with "include a screenshot / expected vs. actual" unless the user asks for it.
- **Potential use cases** — ~5 high-level, skimmable ideas from the PRD's use-case section
  and/or any eval dataset. **Name the concrete input source in each** (a webhook payload,
  a created/existing account, a form field) so each one is directly testable. Invite
  testers to invent their own.
- **How it works (quick primer)** — put this **last**, as reference for testers who want
  it. The minimum needed to set the feature up and read its results: concrete steps and
  real UI labels, kept tight.

## 5. Writing style

- **Brief and skimmable** — someone should be able to read it in about a minute.
- **Human, low-jargon** — write for a tester, not an engineer. No file paths, class names,
  or internal identifiers in the doc body. Enough detail to act, no more.
- **No literal code or variable syntax in the body** — don't write `{{variables}}`,
  `{{$.trigger.x}}`, or format jargon like "E.164". Say it plainly: "reference previous
  nodes' and the trigger's values through variables", "format a raw phone number".
- **~5 use cases**, high-level, each tied to a concrete input source. Don't dump the whole
  PRD catalog.
- **Link sparingly** — only where a tester genuinely needs to go deeper. Don't reflexively
  link the PRD; the user often trims it.
- **Placeholders** for anything the user owns (env, credentials, report channel) — obvious
  inline markers like `*[link — to add]*` so they're easy to find. The user usually fills
  these in themselves during review.

## 6. Publish

- Write into the **user-provided target page** with the `notion` MCP `notion-update-page`
  tool. For a blank page use `command: "insert_content"` with `position: {"type":"end"}`.
- Do **not** create a new page unless the user asked for one — the target page already
  exists in their doc tree.
- Report back the page URL and explicitly list the placeholders left for the user to fill,
  then hand it over for their revisions.
