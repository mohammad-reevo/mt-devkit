# Fix Ask Reevo workflow toggle contrast (CRMF-1740) — Scope

## Idea
The floating "Ask Reevo" toggle in the bottom-left of the CRM Workflows AI node
builder renders with poor contrast (reads as black-on-dark, unreadable in dark
theme). Root cause is that this button never adopted the shared toggle-button
convention: its ON state uses the solid *inverted* Button `default` variant
(`bg-button-default-default` / `text-text-inverse`, which flips to light-bg +
black-text in dark theme), and its icon color is hardcoded `text-violet-500`
(a raw palette color the color linter bans) instead of the semantic `text-ai-accent`
that every other Ask Reevo entry point uses. Fix = make it conform to the common
toggle pattern.

## Approaches considered

### A — Conform to the shared `Toggle` primitive (CHOSEN)
Rebuild the button on the canonical shared `Toggle` component so its ON/OFF
states come from the standard `bg-accent` / `text-accent-foreground` treatment
for free, and swap the icon to `text-ai-accent`. Matches both the app-wide
primitive and every same-page workflow toggle. `Toggle` is controlled
(`pressed` + `onPressedChange`), so it preserves the current open/close-the-chat
behavior. Smallest conceptual surface, self-documents as a toggle, low blast
radius, reversible.

### B — Keep the current Button, fix only the two colors (rejected)
Leave the hand-rolled Button; change the ON state off the inverted `default`
variant to the accent treatment and swap the icon to `text-ai-accent`. Most
surgical diff, but re-implements the toggle convention inline and leaves the
button a snowflake — fixes the symptom, not the "never adopted the convention"
root. Kept as fallback if wrapping the primitive in the existing chrome is fiddly.

### C — Mirror the sibling chat `AskReevoButton` (`outline` + `text-ai-accent`) (rejected)
Maximizes cross-surface Ask-Reevo visual consistency, but the siblings are
one-shot *open* actions, not toggles; this floating button genuinely toggles the
chat open/closed, so an `outline` non-toggle style loses the pressed-state
affordance. Its `text-ai-accent` icon choice is the right detail to borrow into A.

## Chosen direction
> Revised mid-implementation (user request): make the button a **launcher**, not a
> persistent toggle. Codebase dig confirmed every other Ask Reevo entry point already
> hides its trigger while the chat is open (`AskReevoButton.tsx` `if (isVisible) return null`),
> so the workflow toggle was the lone outlier.

The floating workflow Ask Reevo button hides itself while the chat is open (the chat
window's own X / Escape re-shows it via the same `useParallelChatStore` visibility),
matching the sibling Ask Reevo triggers. As an open-only launcher it's no longer a
toggle, so it uses the shared `Button` `variant='outline'` (self-contained floating-pill
chrome) with the semantic `text-ai-accent` icon — mirroring `chat/AskReevoButton.tsx`
(this is scoping approach C, now correct because the control is open-only). This also
resolves the original contrast bug at the root: the inverted pressed/on state that
rendered black-on-dark never renders, because the button is gone whenever the chat is
open. Verify readability in both themes and that `lint:colors` passes.

## Open questions
- Does the existing bordered-pill chrome (background + border + shadow wrapper)
  wrap cleanly around the shared `Toggle`, or does the toggle's own background
  fight the wrapper? (mt-plan to confirm; falls back to B if it conflicts.)
- Should the icon `text-ai-accent` persist in BOTH on and off states, or only
  when active? (Sibling triggers keep it always-on; assume always-on.)

## Out of scope
- The other Ask Reevo entry points (chat `AskReevoButton`, `WorkflowImproveInstructionsButton`)
  — they already use the right tokens; no change.
- Any change to the shared `Toggle` primitive itself or to the semantic token
  definitions.
- Adding a `bg-ai-accent` background token (none exists today; not needed).
