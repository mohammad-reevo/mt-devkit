---
name: populate-dev-data
description: Restore an empty local Postgres from REAL cloud DEV data (~30 min) and re-index FalkorDB. Personal rebuild of devkit's populate-dev-data — self-contained (backend lifecycle via env-manager, DB via db; no devkit start-backend/local-db/backend-request deps). Use when the local DB is empty (onboarding screen, no contacts/accounts). Distinct from spinup-local-db, which seeds synthetic data fast. Triggers on "populate dev data", "restore local db from dev", "local db is empty".
---

# populate-dev-data — restore local DB from real cloud DEV data

> Personal rebuild — self-contained. Self-contained: backend lifecycle via **env-manager**
> (`run be` / `kill be`), DB queries via **db**. No devkit `start-backend` / `local-db` /
> `backend-request` dependency. **Destructive + slow (~30 min).**
>
> Not the same as `spinup-local-db` — that seeds *synthetic* data fast from scratch. This pulls the
> *real* DEV snapshot. Reach for this when you specifically need real dev data locally.

## Prerequisites
- **DEV access** (the copy pulls from cloud DEV, same access as `db --dev`): Tailscale VPN on,
  `chamber` installed, AWS SSO valid. If the copy can't authenticate, `aws sso login` and retry.
- **salestech-be checkout** resolvable — defaults to `~/Desktop/code/mt-devkit/salestech-be`; override
  with `SALESTECH_BE_ROOT`.

## Workflow

1. **Stop the backend** — env-manager: `kill be`. The restore drops & recreates the DB, so it must
   be free of connections first.
2. **Run the refresh (do NOT interrupt, ~30 min):**
   ```bash
   bash $HOME/Desktop/code/mt-devkit/.claude/skills/populate-dev-data/populate.sh
   ```
   Wipes Docker volumes, restarts Docker deps, copies DEV → local Postgres.
3. **Start the backend** — env-manager: `run be`. Applies migrations and starts the workers (needed
   for indexing next).
4. **Re-index FalkorDB:**
   ```bash
   cd "${SALESTECH_BE_ROOT:-$HOME/Desktop/code/mt-devkit/salestech-be}" && \
     uv run python -m salestech_be.temporal.local_test_helpers.trigger_specific_organization_indexing
   ```
   Mirrors devkit — indexes the trigger's default org. If the snapshot's admin org differs and
   search comes back empty, re-run with `--organization-id <org_id>` for the org you're testing.

## Reconcile admin user + onboarding (via db)

The DEV snapshot's admin user/org may need role + onboarding fix-ups. Resolve `<user_id>` / `<org_id>`
from the snapshot (the admin you'll log in as), then:

```bash
# verify role + status
bash $HOME/Desktop/code/mt-devkit/.claude/skills/db/dbquery.sh "SELECT roles, status FROM user_organization_association WHERE user_id='<user_id>' AND organization_id='<org_id>';"
# fix to ADMIN/ACTIVE if needed
bash $HOME/Desktop/code/mt-devkit/.claude/skills/db/dbquery.sh "UPDATE user_organization_association SET roles='{ADMIN}', status='ACTIVE' WHERE user_id='<user_id>' AND organization_id='<org_id>';"
# verify onboarding (need both user_onboarding and workspace_onboarding = COMPLETED)
bash $HOME/Desktop/code/mt-devkit/.claude/skills/db/dbquery.sh "SELECT type, state->>'workflow_completed' FROM onboarding_progress WHERE organization_id='<org_id>' AND (user_id='<user_id>' OR user_id IS NULL);"
# insert missing user_onboarding
bash $HOME/Desktop/code/mt-devkit/.claude/skills/db/dbquery.sh "INSERT INTO onboarding_progress(id,user_id,organization_id,type,state,created_at,updated_at) VALUES(gen_random_uuid(),'<user_id>','<org_id>','user_onboarding','{\"workflow_completed\":\"COMPLETED\"}',now(),now());"
# insert missing workspace_onboarding
bash $HOME/Desktop/code/mt-devkit/.claude/skills/db/dbquery.sh "INSERT INTO onboarding_progress(id,user_id,organization_id,type,state,created_at,updated_at) VALUES(gen_random_uuid(),NULL,'<org_id>','workspace_onboarding','{\"workflow_completed\":\"COMPLETED\"}',now(),now());"
```

## Verify (all must pass — via db)

```bash
bash $HOME/Desktop/code/mt-devkit/.claude/skills/db/dbquery.sh --tuples-only "SELECT count(*) FROM contact;"   # > 0
bash $HOME/Desktop/code/mt-devkit/.claude/skills/db/dbquery.sh --tuples-only "SELECT count(*) FROM account;"   # > 0
bash $HOME/Desktop/code/mt-devkit/.claude/skills/db/dbquery.sh --tuples-only "SELECT state->>'workflow_completed' FROM onboarding_progress WHERE type='workspace_onboarding' AND organization_id='<org_id>';"  # COMPLETED
```

On failure: **stop, report which check + actual vs expected**, fix the rows above, retry — never
skip or fake a check. (Devkit verified over HTTP via `backend-request`; we verify directly through
`db` — simpler and it sidesteps the auth-scoping gotcha on user-onboarding. If a future
`backend-request` lands, an HTTP smoke of `/contacts/_list` + `/accounts/_list` is a fine add.)
