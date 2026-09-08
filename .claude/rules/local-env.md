# Local env

## When to Apply
Working with my local backend or frontend.

## Rules

- **Don't restart for a code change.** Backend and frontend auto-restart. Restart
  only if I ask, or if something is actually wedged.
- **Don't set up local feature flags.** The local backend runs with
  `SALESTECH_BE_ENVIRONMENT="dev"` and a real PostHog key, so flags already
  resolve from the **dev** PostHog project — there is nothing to set up. Just
  name the flag and stop.
- **`.ff_overrides.local.json` is inert here — don't reach for it.**
  `_local_flag_override()` is gated on `is_local_env()`
  (`settings.environment == "local"`), which is `False` in this setup, so the
  file is never read. Writing `true` *or* `false` into it changes nothing, with
  no warning and no log, and forcing a flag **off** locally is not possible. A
  flag you believe you forced is still whatever PostHog says — never report a
  verification run as if the override took.

This applies across all sessions working in this workspace.
