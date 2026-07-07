# AI Node improve-instructions: make the whole-config scope visible — Plan

> Scope: crmf-1741-scope.md
> Repo: frontend-monorepo (/Users/mohammad/Desktop/code/devkit/frontend-monorepo)

## Goals
Reword the two user-facing strings on the workflow "Improve instructions" AskReevo
entry point so they make explicit that AskReevo reviews the **whole node** (all
output fields and their instructions together) when improving — not the single field
the user was looking at. Copy-only, single file, no behavior change.

Concretely, in the `improve_clean_transform_instructions` coachmark variant:
- `inputPrefix` (the seed prompt the user reads before send, also the agent's steer)
  changes from *"Improve the output field instructions for this node…"* to open with
  *"Look at this node's full configuration, then improve the output field
  instructions…"*.
- `description` (the hero-card subtitle in the empty improve chat) changes from
  *"Reevo refines the instructions…"* to *"Reevo reviews the whole node — all its
  output fields and their instructions together — and refines them…"*.

## Non-goals
- No change to the placeholder-field authoring UI (scope rejected direction B).
- No change to `title` (*"Improve output field instructions"*), `ariaLabel`,
  `newInstanceTitle`, `id`, `appFeature`, or `icon` — action name and behavioral/
  analytics identifiers stay put.
- No change to the button's own visible label in `WorkflowImproveInstructionsButton.tsx`
  (separate hardcoded string; out of scope).
- No backend change; no change to what the flow-builder agent reads or does.
- No new endpoint / "optimizer" service (none exists; none added).

## Decisions
- **Exact wording** — resolved (see table in Goals / the two strings in Task 1).
  General "whole node" phrasing, placeholders not named (per user: they don't move
  the needle on a populated config).
- **General vs naming placeholder/input fields** — resolved: general phrasing.
- **Single source** — confirmed: `inputPrefix`, `title`, `description` for this
  feature exist only in the one variant object; no i18n/duplicate. One edit suffices.
- **Which surfaces to touch** — resolved: `inputPrefix` + `description` only (title
  stays). Both render to the user: `inputPrefix` seeds the composer
  (`ChatInstancePanel.tsx` via `useChatCoachmarkStore`), `description` renders as the
  welcome-hero subtitle (`CoachmarkWelcomeHero.tsx:35`).

## Tasks
- [x] 1. Reword the improve-instructions coachmark copy —
      files: `apps/reevo-webapp/src/modules/chat/client/constants/coachmarkVariants.ts`
      (variant `improve_clean_transform_instructions`, ~lines 107–117).
      Change exactly two string fields, leave every other field of the object
      untouched:
      - `inputPrefix` → `'Look at this node's full configuration, then improve the output field instructions so the model produces accurate, well-structured values.'`
      - `description` → `'Reevo reviews the whole node — all its output fields and their instructions together — and refines them so the model produces accurate, well-structured values.'`
      Done when: the file contains the two new strings, the variant still type-checks
      against `CoachmarkVariant`, and no other field of the variant changed.

## Verification
- **Coding checks** (frontend-monorepo root):
  - `pnpm lint:fix` — must pass (includes `lint:colors`; no colors touched, but runs clean).
  - `pnpm type-check` — must pass (string edits keep the `CoachmarkVariant` shape).
  - No unit tests reference this variant or its strings (confirmed) — none to update or run.
- **Manual check** (close-out): open a workflow → clean & transform node → click
  "Improve instructions". Confirm (a) the empty improve chat's hero subtitle shows the
  new `description` copy, and (b) the composer is pre-filled with the new `inputPrefix`
  text (seeded, not auto-sent). Screenshot the hero + seeded composer for the PR.
