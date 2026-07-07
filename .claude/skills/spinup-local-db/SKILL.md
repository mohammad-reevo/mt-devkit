---
name: spinup-local-db
description: Seed the local Postgres DB from scratch (no dev dump), index FalkorDB for the seeded org, and surface the auth identity values for the frontend .env. Use when the local DB is empty/wrong and you want a working local env fast.
---

# Spin Up Local DB

Fast local environment from scratch — no slow/unreliable dev dump.

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

## Step 3 — Provision the subscription + flow quota

`make seed-dev-data` does NOT create a billing subscription or any quota policy items, so running a flow fails the quota gate with `Feature FLOW_NODE_EXECUTIONS is not available`. Fix it with the script beside this file (reuses the backend's own idempotent bootstrap helper):

```bash
cd <devkit-root> && cd salestech-be && uv run python $CLAUDE_PROJECT_DIR/.claude/skills/spinup-local-db/provision_billing.py
```

Defaults to the seeded org and auto-resolves the user — no IDs to pass. Idempotent (skips if an active subscription already exists). Verify:

```bash
bash $CLAUDE_PROJECT_DIR/.claude/skills/db/dbquery.sh "SELECT count(*) FROM organization_subscription WHERE organization_id='00000000-0000-4000-a000-000000000001' AND status='ACTIVE'; SELECT resource_name FROM quota_policy_item WHERE resource_name ILIKE '%FLOW_NODE%';"
```

Expect 1 active subscription + a `FLOW_NODE_EXECUTIONS` row. Scope is flow execution only — `USER_SEAT` is intentionally not provisioned (it only causes a non-fatal warning on the billing overview page, not flows).

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
