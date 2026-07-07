# Fix Ask Reevo workflow toggle contrast (CRMF-1740) — Plan

> Scope: crmf-1740-scope.md
> Repo: /Users/mohammad/Desktop/code/devkit/frontend-monorepo

## Goals
The floating "Ask Reevo" toggle on the workflow canvas conforms to the shared `Toggle`
primitive, so its ON state renders the standard `bg-accent` / `text-accent-foreground`
treatment (readable in both light and dark theme) instead of the inverted `default` Button
variant, and its icon uses the semantic `text-ai-accent` token instead of hardcoded
`text-violet-500`. Toggling still opens/closes the floating chat.

## Non-goals
- Other Ask Reevo entry points (chat `AskReevoButton`, `WorkflowImproveInstructionsButton`).
- The shared `Toggle` primitive itself or the semantic token definitions.
- Adding a `bg-ai-accent` background token (none exists; not needed).

## Decisions
- Keep the bordered-pill wrapper `<div>` — it's the resting chrome; `Toggle` default variant
  is transparent-at-rest, no conflict (same pattern as `WorkflowGraphTab`).
- Icon stays `text-ai-accent` in both on/off states (matches sibling Ask Reevo triggers).
- Behavior wiring moves from `onClick` → Radix `onPressedChange(pressed)`, which also gives
  free `aria-pressed`.

## Tasks
- [x] 2. Convert to launcher (hide-when-open) mirroring sibling `AskReevoButton` — files:
      apps/reevo-webapp/src/modules/workflow/client/components/WorkflowAskReevoButton.tsx (+ .test.tsx).
      > amended: user asked mid-implement for the standard Ask Reevo launcher behavior.
      The button now `return null` when `isChatVisible` (chat's own X/Escape re-shows it),
      uses `Button variant='outline'` + `text-ai-accent` icon (dropped Toggle and the
      wrapper's redundant chrome — outline variant is self-contained pill), and the handler
      is open-only (`setIsChatVisible(true)`, analytics `active:true`). Test gains a
      "hides while chat is open" case. Supersedes task 1's Toggle approach.
      Done when: 3 unit tests pass, lint:colors/type-check/biome green, button hides on open
      and reappears on close.

- [x] 1. Swap Button → shared Toggle in `WorkflowAskReevoButton.tsx` — files:
      apps/reevo-webapp/src/modules/workflow/client/components/WorkflowAskReevoButton.tsx.
      - Replace the `Button` import with `import { Toggle } from '@/components/ui/toggle'`.
      - Replace `<Button variant={isChatVisible ? 'default' : 'ghost'} size='sm' onClick={handleToggle} …>`
        with `<Toggle pressed={isChatVisible} onPressedChange={handleToggle} size='sm'
        data-testid='ask-reevo-toggle' aria-label={…} className='gap-1.5'>` (drop
        `h-8 px-2 text-sm font-medium` — `size='sm'` + toggle base already supply them).
      - Refactor `handleToggle` to take the next pressed value:
        `useCallback((pressed: boolean) => { reportEvent('ask_reevo_toolbar_button', 'clicked',
        { source: 'workflow_editor', active: pressed }); setIsChatVisible(pressed); },
        [setIsChatVisible])`.
      - Change the icon to `<MessageSquare className='h-4 w-4 text-ai-accent' />`.
      - Leave the wrapper `<div>`, `Tooltip`, `useLeftOverlayPx`, and feature-flag gate untouched.
      Done when: file compiles; button renders inside the pill; ON = accent fill, OFF =
      transparent; icon is ai-accent; clicking toggles chat visibility.

## Verification
- **Coding checks** — from repo root:
  - `pnpm lint:colors` (must pass — proves `text-violet-500` is gone)
  - `pnpm type-check`
  - `pnpm lint:fix`
- **Manual checks** — on the workflow canvas with `ASK_REEVO_FLOATING_WINDOW_V_APR2026` on:
  confirm the bottom-left button is readable at rest and when active in **both light and dark
  theme**, clicking pulls out / hides the floating chat, and the tooltip flips text correctly.
  Screenshot both themes for the PR.
