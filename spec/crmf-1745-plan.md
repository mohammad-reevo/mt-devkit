# AskReevo question picker cut off in chat panel — Plan

> Scope: crmf-1745-scope.md
> Repo: frontend-monorepo

## Goals
The AskReevo `ask_user_input` picker (`ExternalToolRequestSheet.tsx`) grows to fit its
content up to the **chat panel's height**, then scrolls internally — instead of being clipped
by a fixed `max-h-[50vh]` (viewport-height) cap. Achieved by bringing the sheet onto the
**panel-bounded flex-height pattern its sibling `ToolApprovalSheet.tsx` already uses**. The
question UI, the breadcrumb tab strip, the minimize/restore behavior, and the panel width are
all unchanged.

## Non-goals
- Breadcrumb "…" truncation on the prior-question tab strip (a width-axis issue; acceptable
  compact-nav behavior — user-confirmed out of scope).
- Any change to the shared chat panel width or the question UI's internal layout.
- Backend/agent-side shaping of the question text length.
- A new unit test asserting height/flex classNames (not meaningfully assertable in jsdom;
  see Verification).

## Decisions
- **Why the ~50vh cap exists →** Not an intentional constraint. Both sheets share the
  `ToolApproval.tsx` card renderer, which has two height paths (`fillHeight ? 'min-h-0 flex-1'
  : 'max-h-[50vh]'`). `ToolApprovalSheet` passes `fillHeight` and gets panel-bounded growth;
  `ExternalToolRequestSheet` never adopted it and is stuck on the `max-h-[50vh]` fallback.
  `50vh` is viewport height, not panel-relative, so it isn't even bounded to the panel today.
  Resolved by code — no creator ask needed.
- **Growth bound / composer overlap →** Bound to panel height via `max-h-full` on the sheet
  root + internal `flex-1 min-h-0 overflow-y-auto` scroll region, mirroring `ToolApprovalSheet`.
  The composer is hidden whenever a pending `ask_user_input` sheet is up (gated by
  `hasActionRequired` in `use-deferred-tools.ts`), so a taller sheet overlays only the message
  thread, never the input. No arbitrary pixel bound needed.
- **Breadcrumb strip →** Left exactly as-is (user-confirmed out of scope).

## Tasks
- [x] 1. Adopt panel-bounded flex height in the picker sheet — files:
      `apps/reevo-webapp/src/modules/chat/client/components/shared/tool-calls/external/ExternalToolRequestSheet.tsx`.
      Mirror the `ToolApprovalSheet.tsx` height pattern:
      - Root sheet `motion.div` (~:254–262): add `flex max-h-full flex-col` (keep existing
        `absolute bottom-0 z-10`, the sidebar/full-width horizontal insets, and `overflow-hidden`).
      - Collapsible body `motion.div` (~:266–272): className → `cn('flex min-h-0 flex-col
        overflow-hidden', !isMinimized && 'flex-1')`. Keep the framer-motion
        `animate={{ height: isMinimized ? 0 : 'auto', opacity: … }}` as-is — the `!isMinimized`
        guard on `flex-1` is what lets the height:0 collapse still work (the trick the sibling uses).
      - Content wrapper `div` (~:318): make it the flex-fill region — add `flex min-h-0 flex-col
        flex-1` (keep its existing padding/background classes).
      - Scroll region `div` (~:319): replace `max-h-[50vh]` with `min-h-0 flex-1`; keep
        `overflow-y-auto`.
      Header (~:274–288) and tab bar (~:291–315) stay fixed-height siblings — no change.
      Done when: `pnpm type-check` + `pnpm lint:fix` clean, and in Storybook the sheet grows to
      the container height with an internal scroll on tall content, stays compact on short
      content, and minimize/restore still animates.

- [x] 2. Visual verification of the height behavior — files:
      `apps/reevo-webapp/src/modules/chat/client/components/shared/tool-calls/external/ExternalToolRequestSheet.stories.tsx`.
      Add a `LongContent` story (long `question_text` + many options, multi-question so the tab
      bar shows) rendered in the existing `h-[680px]` decorator, to reproduce the pre-fix clip
      and confirm post-fix growth-to-container + internal scroll. Reuse the existing story
      scaffolding/args; do not alter the component.
      Done when: the story renders the full question with an internal scrollbar (no clip) in the
      680px container, and `MultiQuestion`/`SingleQuestion`/`Minimal` stories still render.

## Verification
- **Coding checks** (run in `frontend-monorepo`):
  - `pnpm type-check`
  - `pnpm lint:fix`
  - No unit test added — height/flex layout is not assertable in jsdom, and a className-assertion
    test would be brittle (test-economy). Storybook is this module's convention and the
    verification surface.
- **Manual checks** (mt-verify close-out):
  - Storybook: the new `LongContent` story shows full content + internal scroll, no clip.
  - In-app: trigger the workflow "clean & transform → Improve instructions" flow so the agent
    emits a long-question `ask_user_input`; confirm the full question + options are visible
    (sheet grows/scrolls) and the composer is not overlapped.
