---
name: posthog
description: Read Reevo's PostHog through the PostHog MCP without reading the wrong environment — resolve and switch the project explicitly (DEV 118909 vs PROD 68803) before any call, and name the project in every answer. Owns the feature-flag recipe — read a flag's release conditions, then evaluate it for a real user + organization the way the app does — plus which app reads which project, the headless-browser flags trap, and the rule that flag writes never land on PROD unless I named prod. Triggers on "is flag X on in dev/prod", "why is the feature hidden", "check the flag", "what's the rollout of X", "look in posthog", "/posthog".
---

# posthog — read the right project, then read the flag

> Personal harness tool. Runs through the **PostHog MCP** (`mcp__posthog__exec`) — self-refreshing
> auth, works in a background session. Every call goes `exec` → `call <tool> <json>`; run
> `info <tool>` once before a tool's first call.

## Resolve the project first — every session, every answer

**The MCP has no fixed default project.** The active project is account-level state — whatever
the last `switch-project` (from any session, or the PostHog UI) left behind. It has been observed
on PROD and on DEV. Reading a flag in the wrong one gives a confident wrong answer, and a flag
*write* lands wherever the session happens to point.

1. Decide the target from the question: deployed dev / localhost → **DEV**; real customers,
   app.reevo.ai, adoption numbers → **PROD**. Not stated and it matters → ask.
2. `call project-get {}` — read `id` + `name` of the active project.
3. Wrong one → `call switch-project {"projectId": <id>}`, then `project-get` again to confirm.
4. **Name the project in the answer** — "on DEV (118909), the flag is …". An answer without it
   is incomplete.

| Project | id | Read by |
|---|---|---|
| `app-ng-dev.reevo.ai (DEV)` | **118909** | deployed dev (app-ng-dev), and **all local testing** — see below |
| `app.reevo.ai (PROD)` | **68803** | app.reevo.ai; the prod webapp build's key `phc_wowp…` is this project's token |

The other projects in the org (marketing site, mobile, desktop, ops-central dev/prod, cal-dev,
builder-agent) are not the webapp. Don't map the dev webapp's `.build-env.public.dev-start` key
to a project by token — on 2026-10-21 it matched no project's current token; go by the table.

### Local testing reads DEV flags — automatically

Anything run on this laptop — the default stack, a `local-stack`, a test browser on localhost —
evaluates flags against **DEV (118909)** with nothing to set up: the local backend's `.env` key is
118909's token, and the local webapp uses the dev build's key. So "is X on for my local run" is
a read on 118909 with the pool / seed org as the group. Never flip a flag for local testing on
PROD, and don't ask which environment a local run uses.

## Read a flag

1. **Definition** — `call feature-flag-get-definition-by-key {"key": "<flag-key>"}`. Read:
   - `active` / `archived` / `deleted` — inactive means off for everyone, whatever the conditions.
   - `filters.aggregation_group_type_index` — **`1` = rolled out per organization** (group type
     `organization` is index 1 in both projects); absent = per person.
   - `filters.groups[]` — each condition set: `rollout_percentage` and `properties` (the targeting).
     Sets are OR-ed; a set with no properties and 100% = everyone (every org, if group-aggregated).
   - `filters.multivariate` / `payloads` — variant flags and payload-driven knobs.
   - `last_called_at` proves nothing either way (see the `posthog-local-eval-silent-false` memory).
2. **Evaluate it for a real subject** — the definition says what the rules are; this says what a
   given user in a given org actually gets:
   ```
   call feature-flags-evaluation-reasons-retrieve {"distinct_id": "<reevo user id>",
     "flag_keys": ["<flag-key>"], "groups": "{\"organization\": \"<org id>\"}"}
   ```
   Both apps identify that way — `distinct_id` = Reevo user id, group `organization` = org id
   (FE `posthogIdentity.ts`, BE `core/ff/feature_flag_service.py`). For an org-aggregated flag the
   `distinct_id` barely matters; the group does. Always pass `flag_keys` — omitting it returns
   every flag in the project. `reason` reads `condition_match` / `no_condition_match` / `disabled`.
3. Report: project, flag state, who it's on for, and the reason for the subject you checked.

## A flag that's on but the UI still hides the feature

- **Headless browser.** Dev's `/flags` endpoint (`ev.reevo.ai`, the webapp's `api_host`) answers
  a `HeadlessChrome` user agent with `200` and `flags: {}` — every flag reads off. Give Playwright
  a normal desktop Chrome UA; the server still evaluates flags normally.
- **FE gate, not the flag.** A node or trigger can be hidden by the FE constants regardless of
  PostHog — see the `node-and-trigger-availability` knowledge-base entry.
- **A local backend override.** The backend runs with `SALESTECH_BE_ENVIRONMENT="local"`, so a
  gitignored `salestech-be/.ff_overrides.local.json` (if present) beats PostHog for that backend
  only — check for the file before trusting a DEV read for a local run.

## Writes

Flag changes (`update-feature-flag`, `feature-flag-enable` / `-disable` / `-roll-out-to-everyone`,
`create-feature-flag`, `delete-feature-flag`) are mine to ask for, never a side effect of a read.
Before any write, `project-get` and state the project in the confirmation. **Never write on PROD
(68803) unless I named prod for that write** — "turn it on" alone means DEV.

## Analytics queries

Event and usage questions follow the MCP's own guidance (`metric-list`, `read-data-schema`
first). Prod numbers exclude internal orgs and impersonators — `reevo-internal-orgs.md`; the
event conventions are in the `product-analytics` knowledge-base entry.
