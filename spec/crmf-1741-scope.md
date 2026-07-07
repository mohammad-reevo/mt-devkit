# AI Node improve-instructions: make the whole-config scope visible — Scope

## Idea
The "Improve instructions" AskReevo button on the clean & transform node reads the
**whole node config** — all output fields and their instructions — when it improves,
but users don't realize that scope until after they run it. CRMF-1741 (reported via
Slack by michael.njauw) asks to make it obvious *upfront* that AskReevo considers
everything in the node config, not just the one field they were looking at. The fix
is a copy clarification at the point where the user invokes the feature.

## Approaches considered

### A — Clarify at the chat entry point (chosen)
Reword the auto-filled prompt the user sees before sending, and the coachmark's
description, so they state that AskReevo reviews the full node config (all output
fields and their instructions together) when improving. Pure FE copy, near-zero
risk. Reaches the user at the moment they open the improve chat, and the pre-filled
prompt doubles as steering for the agent.

### B — Clarify at the authoring surface (rejected)
Add a hint/tooltip on the placeholder-field UI so users learn at authoring time that
those fields feed the improve feature. Rejected by the user: not intuitive, and
placeholders carry little weight on a populated config — a dedicated authoring-time
hint is overkill for the payoff.

### C — Remove the coupling (rejected)
The ticket's own path 2 ("do away with it"). Incoherent: "custom placeholder fields"
are the `{{$.…}}` input-variable references embedded *inside* the very instructions
the AI rewrites, and every instruction is required to carry at least one. They can't
be separated from the improve context, so there's nothing to decouple.

## Chosen direction
A **frontend-copy-only** change. Rework the improve-instructions entry copy — the
pre-filled prompt shown before send, plus the coachmark description — so it makes
explicit that AskReevo looks across the **whole node configuration** when improving,
rather than a single field in isolation. Lean toward general "reviews all output
fields and their instructions together" phrasing over explicitly naming
placeholder/input fields (per the user: placeholders don't do much on a populated
config, so naming them is more noise than signal). No backend change, no behavior
change — only what the user reads at the point of use.

Note reconciling the ticket premise: the ticket describes a separate "Optimize Node
Output Field Instructions" panel — there is none. That panel *is* this AskReevo
improve-instructions button; the "identifies weaknesses" text is just the chat
agent's freeform reply. This scope touches only the entry copy for that button.

## Open questions
- Exact wording of the reworded prompt + description — draft during mt-plan; keep it
  short and plain, matching the existing tone. Current prompt for reference:
  *"Improve the output field instructions for this node so the model produces
  accurate, well-structured values."*
- Whether the copy should say "whole node configuration" (general) or name the
  input/placeholder fields explicitly. Current lean: general phrasing.
- Confirm the single source of the user-facing strings at plan time (the coachmark
  variant's `inputPrefix` + `description` in `coachmarkVariants.ts`) so both surfaces
  change in one place.

## Out of scope
- Any change to the placeholder-field authoring UI (rejected direction B).
- Any change to what the backend improve / flow-builder agent actually reads or does
  — behavior is unchanged; this is copy only.
- Improving the AskReevo agent's edit quality (separate, ongoing work).
- Any new endpoint or "optimizer" service (none exists; none is being added).
