# Local env

## When to Apply
Working with my local backend or frontend.

## Rules

- **Don't restart for a code change.** Backend and frontend auto-restart. Restart
  only if I ask, or if something is actually wedged.
- **Don't set up local feature flags.** All local testing — backend and
  webapp — uses the **dev** PostHog project's key, so flags already resolve
  from dev (118909) automatically — there is nothing to set up. Just name the
  flag and stop.
- **Don't use `salestech-be/.ff_overrides.local.json`.** The backend runs with
  `SALESTECH_BE_ENVIRONMENT="local"`, so `_local_flag_override()` does read it
  and it beats PostHog — for that backend only, not the webapp. Leave it absent
  so local runs always match dev PostHog; if one exists, say so before
  reporting any local verification.

This applies across all sessions working in this workspace.
