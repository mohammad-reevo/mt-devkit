# AskReevo question picker cut off in chat panel — Scope

**Ticket:** CRMF-1745 — https://linear.app/reevo/issue/CRMF-1745/askreevo-text-truncated-in-ai-node-field-selection-dropdown

## Idea
In AskReevo, when the assistant asks the user to make a selection (the `ask_user_input`
picker — e.g. "Which fields do you want the AI node to write to on the account?"), the
picker renders inside the chat panel but is clipped: the question and its options don't
fully fit and read as cut off / awkwardly wrapped. This was reported from the workflow
"clean & transform → Improve instructions" flow, whose questions tend to be long and
multi-part, but the picker component itself is generic AskReevo.

The root cause is a container problem, not a content problem: the question UI wraps its
text correctly on its own, but the picker's container is pinned to the bottom of the chat
and capped at a **fixed ~half-panel height** with overflow hidden — so tall content gets
clipped. The fix is to give the (already-correct) picker the vertical room it needs.

## Approaches considered

### Widen the chat panel / open workflows in full-width
Give the picker more horizontal space (wider sidebar, or launch the workflow chat in
full-width mode where the sheet already gets a larger max width).
**Rejected — two reasons:** (1) the app doesn't have the horizontal space to spare, and
(2) width doesn't generalize — a long-enough or numerous-enough question set re-overflows
at any fixed width. Width moves the cliff, it doesn't remove it.

### Workflow-only special-mode styling
Thread the existing workflow context signal (the `appFeature` tag on these chats) into the
picker and give it a workflow-specific layout, leaving the generic look untouched.
**Rejected —** the clipping lives in shared code with no workflow-only seam; branching a
shared component on "am I in a workflow?" is a FE special-mode anti-pattern, and the fix is
a generic readability improvement every AskReevo user benefits from anyway.

### Redesign the picker's internals (vertical question list / one-at-a-time wizard)
Replace the horizontal breadcrumb tab strip with a vertical stacked list or a step-by-step
wizard so long question text never competes for width.
**Rejected as the fix —** the question UI itself works; redesigning it is out of proportion
to the bug and steps on a design the picker's author built intentionally. The clip is a
container-height issue, addressable without touching the picker's layout.

### Stretch the picker container vertically to fit its content (chosen)
Keep the question UI exactly as-is; change its container from a fixed height cap to a
content-driven, bounded height that grows to fit and returns to compact when short.

## Chosen direction
Let the `ask_user_input` picker's container **size to its content vertically**, up to a
bound that preserves room for the conversation and the chat input above it — then collapse
back to compact when the content is short ("stretch, then go back to normal"). The
already-correct question UI is not modified; only its container's height behavior changes,
from a fixed ~half-panel cap to a bounded content-fit. The picker component already has an
expand/collapse height animation and a minimize→restore state, so this extends existing
behavior rather than introducing a new mechanism. Because the picker is shared/generic
AskReevo, the fix benefits every user and any future long-content case, not just workflows.

## Open questions
- **Creator intent on the ~half-panel cap:** why was the picker's height capped where it is?
  Confirm with the component's author that a content-driven, bounded height doesn't defeat an
  intentional constraint (e.g. deliberately keeping the conversation visible above the sheet).
- **Upper bound + overflow behavior:** how tall should the sheet be allowed to grow before it
  starts scrolling internally instead of growing? It must not cover the chat input/composer or
  the active turn. mt-plan to settle the exact bound and the grow-vs-scroll threshold.
- **Confirm breadcrumb is out of scope** (see below) with the reporter/creator — that the "…"
  on the tab strip is acceptable and not part of the complaint.

## Out of scope
- **Breadcrumb "…" truncation on the prior-question tab strip.** Those are equal-width
  horizontal tabs; their cutoff is a *width*-axis issue that a vertical stretch won't (and
  shouldn't) change. Treated as acceptable compact-nav behavior. If it later needs addressing,
  it's a separate treatment (tooltip on truncated tabs, or a vertical list) — not this fix.
- **Any change to the shared panel width or the question UI's internal layout.**
- **Backend/agent-side shaping of the question text length.** The fix is on the container, not
  on what the workflow flow emits.
