# Local feature flags come from dev — don't set up a local override

## When to Apply
Whenever a local test needs a feature flag on, and you're about to tell me to
create or edit `salestech-be/.ff_overrides.local.json`.

## Rule
**Don't.** I reuse the dev feature flags — the flag is enabled for my org in dev
and my local backend reads that. There is nothing for me to set up locally.

So when handing me something to test, just name the flag. Don't include override
JSON, don't ask me to add a file, and don't list "enable the flag locally" as a
step I have to do first.

`.ff_overrides.local.json` still exists and is still the right tool for *your*
own verification — exercising both branches of a flag without touching dev, or
proving a flag key resolves at all before it exists in PostHog. Use it there;
just don't route me through it.

## Why
It's a step I don't need. The flag is already on for my org in dev, so telling me
to create a local override file adds setup, and a stale override file silently
overrides the real value later.

This applies across all sessions working in this workspace.
