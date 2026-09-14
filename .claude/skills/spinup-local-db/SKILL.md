---
name: spinup-local-db
description: Seed the local Postgres DB from scratch with synthetic data, provision a subscription granting every quota resource, index FalkorDB for the seeded org, and surface the auth identity values for the frontend .env. The only way to set up a local DB — local data is always synthetic. Use when the local DB is empty/wrong and you want a working local env fast.
---

# Spin Up Local DB

Fast local environment from scratch, entirely synthetic.

**Local data is always synthetic.** Real customer data is never copied onto the laptop — this
skill is the only way in. One caveat worth knowing rather than rediscovering: the seeded
email/calendar accounts are inserted directly as `type=CONNECTED, vendor=NYLAS` rows without
going through real OAuth provisioning, so local email works via GreenMail IMAP but anything
needing a genuine Nylas account object does not work locally.

**Prereqs:** Docker deps up (postgres, falkordb, temporal). Backend does not need to be running for seeding/indexing.

All commands anchor cwd at the devkit root first (ACL hook rejects a cwd inside a sub-repo). Replace `<devkit-root>` with the workspace root (the dir containing `salestech-be/` and `frontend-monorepo/`).

## Step 1 — Seed the DB

```bash
cd <devkit-root> && cd salestech-be && make seed-dev-data
```

Creates the Acme org + 5 users + ~30 contacts / 15 accounts. Idempotent (skips if already seeded).
To wipe and reseed fresh instead: `make seed-dev-data-reset`.

## Step 2 — Get the auth identity values

```bash
cd <devkit-root> && cd salestech-be && make seed-dev-token
```

Capture these three lines from the output (needed for the frontend `.env` in Step 4):

- `LOCAL_SESSION_OVERRIDE_USER_EMAIL`
- `LOCAL_SESSION_OVERRIDE_USER_ID`
- `LOCAL_SESSION_OVERRIDE_ORGANIZATION_ID`

`ORGANIZATION_ID` is stable (`00000000-0000-4000-a000-000000000001`). `USER_ID` can change after a `--reset`, so always re-read it here. Ignore the printed `ACCESS_TOKEN` — the frontend generates a fresh one itself (see Step 5).

## Step 3 — Provision the subscription + every quota resource

`make seed-dev-data` creates NO billing rows at all, and a quota-gated feature with no
subscription behind it resolves to `DENIED_BY_PLAN` rather than failing open — so without this
step flows fail with `Feature FLOW_NODE_EXECUTIONS is not available`, Ask Reevo 403s, and
dozens of other features are silently switched off. Fix it with the script beside this file
(reuses the backend's own idempotent bootstrap helper for the subscription skeleton, then grants
the plan every resource in the backend's `RESOURCE_GROUP_TO_RESOURCES` mapping):

```bash
cd <devkit-root> && cd salestech-be && uv run python $HOME/Desktop/code/mt-devkit/.claude/skills/spinup-local-db/provision_billing.py
```

Defaults to the seeded org and auto-resolves the user — no IDs to pass. Idempotent: an existing
active subscription is reused, and a resource the plan already grants is left alone. Verify:

```bash
bash $HOME/Desktop/code/mt-devkit/.claude/skills/db/dbquery.sh "SELECT count(*) FROM organization_subscription WHERE organization_id='00000000-0000-4000-a000-000000000001' AND status='ACTIVE'; SELECT count(*) FROM subscription_plan_quota_policy_item_association a JOIN organization_subscription s ON s.subscription_plan_id = a.subscription_plan_id WHERE s.organization_id='00000000-0000-4000-a000-000000000001' AND s.status='ACTIVE';"
```

Expect 1 active subscription, and an association count matching the total the script printed
(every resource in `RESOURCE_GROUP_TO_RESOURCES`). The script's own output is the clearer check —
it reports how many resources the plan grants, how many it added, and how many were already there.

## Step 4 — Index FalkorDB for the seeded org

```bash
cd <devkit-root> && cd salestech-be && uv run python salestech_be/temporal/local_test_helpers/trigger_specific_organization_indexing.py --organization-id 00000000-0000-4000-a000-000000000001
```

Pass the org id explicitly — the script's default is an old, dead org. Verify the graph appears:

```bash
docker exec salestech-be-salestech_be-falkordb-1 redis-cli GRAPH.LIST
# expect: org_0000000000004000a000000000000001  (~570 nodes)
```

If the graph never appears, the falkor temporal workers aren't running (the backend run alias does not start them). Start them in the background, then re-run the trigger above:

```bash
cd <devkit-root> && cd salestech-be && zsh -ic 'uv run python -m salestech_be.temporal.workers.falkor --worker workflow > logs/falkor_workflow_logs.txt 2>&1 &!'
cd <devkit-root> && cd salestech-be && zsh -ic 'uv run python -m salestech_be.temporal.workers.falkor --worker activity > logs/falkor_activity_logs.txt 2>&1 &!'
```

CDC consumers (started by the backend run alias) keep new data changes flowing into Falkor automatically after this initial backfill.

## Step 5 — Populate the frontend .env (user does this manually)

Instruct the user to edit `frontend-monorepo/apps/reevo-webapp/.env`:

- Set the three `LOCAL_SESSION_OVERRIDE_*` vars to the values from Step 2.
- **Leave `LOCAL_SESSION_OVERRIDE_ACCESS_TOKEN` blank/commented** — `pnpm dev` auto-generates a fresh token on every start. Pasting one makes it go stale and skips auto-generation.
- Ensure `BASE_API_URL="http://localhost:8000"` and `REEVO_BACKEND_PATH` points at the real backend checkout.

## Done

Run backend, then `pnpm dev` on the frontend → logged in as the seeded admin with data, and Falkor-backed features working.
