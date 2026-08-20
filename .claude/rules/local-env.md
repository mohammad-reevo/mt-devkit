# Local env

## When to Apply
Working with my local backend or frontend.

## Rules

- **Don't restart for a code change.** Backend and frontend auto-restart. Restart
  only if I ask, or if something is actually wedged.
- **Don't set up local feature flags.** I reuse the dev flags — just name the flag
  and stop. `.ff_overrides.local.json` is yours to use for your own verification,
  not a step to hand me.

This applies across all sessions working in this workspace.
