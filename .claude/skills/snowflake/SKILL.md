---
name: snowflake
description: Query Reevo's Snowflake account (a copy of production data) from my personal harness — both the reporting warehouse (`REPORTING_DB_*`, per-org CRM object model) and the CDC replica of the app Postgres (`POSTGRES_DB_*`, raw application tables). Self-contained `snow` CLI wrapper, read-only by default. Use for reporting/analytics investigation, checking warehouse state, verifying what the reporting pipeline landed, or reading prod application tables that `db` can't reach — including the workflow/flow-engine tables (`user_flow`, `flow_definition`, `flow_run`, `user_flow_folder`). Distinct from `db`, which queries live Postgres (local/dev only). Triggers on "query snowflake", "check the warehouse", "look up X in snowflake", "query the reporting data", "how many flows/flow runs", "query user_flow / flow_definition / flow_run".
---

# snowflake — query the reporting warehouse + app-Postgres replica

> Personal harness tool, self-contained. Wraps the official `snow` CLI the same way `db` wraps
> `psql`. Auth lives in the CLI's own config (`~/Library/Application Support/snowflake/config.toml`
> on macOS); no credentials in this repo.

## Target

One Snowflake account, **two databases that hold different things** — pick by what you're after:

| Database | What it is | Shape |
|---|---|---|
| `REPORTING_DB_PROD` / `_DEV` | The **reporting warehouse** — the modeled CRM object model. | One schema per organization (`ORG_<uuid>`). |
| `POSTGRES_DB_PROD` / `_DEV` | A **CDC replica of the app Postgres** — raw application tables, incl. the workflow/flow tables. | One flat `PUBLIC` schema; org-scoped by an `organization_id` column. |

Both hold a **copy of production data**. There is no local Snowflake. Treat every query as
touching real prod-shaped data.

The **`db`** skill queries *live* Postgres — local Docker or shared Dev Aurora — and **cannot
reach prod**. So `POSTGRES_DB_PROD` here is the only read path to prod application tables.

## How to run

```
bash $HOME/Desktop/code/mt-devkit/.claude/skills/snowflake/snowquery.sh [--csv|--json] [--write] "SQL"
```

- **Default:** `bash $HOME/Desktop/code/mt-devkit/.claude/skills/snowflake/snowquery.sh "SELECT current_account(), current_role();"`
- `--csv` / `--json` for machine-readable rows (default is a human table).
- `-c <name>` to target a different named connection (default `reevo`, override with
  `$SNOWFLAKE_CONNECTION`).

The script resolves the connection itself — never construct a raw `snow sql` command or pass
credentials on the command line.

## Finding your way around — reporting warehouse

**Data is scoped per organization, so an unqualified table name finds nothing.** `SELECT * FROM
account` fails or returns an empty set — there is no shared `account` table. Always fully qualify
as `<database>.<schema>.<table>`.

| Layer | Value |
|---|---|
| Database | `REPORTING_DB_PROD` for prod. `REPORTING_DB_DEV` is shared by dev / staging / local / pytest — none of those have their own warehouse. |
| Schema | One per organization: `ORG_<organization_id>`, uppercased with dashes replaced by underscores. Org `a1b2c3d4-…-9f8e` → schema `ORG_A1B2C3D4_…_9F8E`. |
| Table | The object's `api_name` — `account`, `contact`, `user`, `select_list_value`, plus each org's custom objects. |

So a real query looks like:

```sql
SELECT count(*) FROM REPORTING_DB_PROD.ORG_A1B2C3D4_5E6F_7890_ABCD_EF1234567890.account
```

**Discovery ladder** when you don't know the target — each step is a read, so all are allowed by
default:

```sql
SHOW SCHEMAS IN DATABASE REPORTING_DB_PROD;          -- find the ORG_<uuid> schema
SHOW TABLES IN SCHEMA REPORTING_DB_PROD.ORG_<uuid>;  -- what objects that org has
DESCRIBE TABLE REPORTING_DB_PROD.ORG_<uuid>.account; -- column names and types
```

For a column-level search, `REPORTING_DB_PROD.INFORMATION_SCHEMA.COLUMNS` is queryable like any
table.

**Getting the org id:** it's a Postgres value, not a Snowflake one. Look it up with the **`db`**
skill (e.g. `SELECT id, name FROM organization`), then build the schema name from it. The two
skills are complementary — the dataset *catalog* (`reporting_dataset_v2`) lives in Postgres while
the *rows* live in Snowflake.

## Workflow / flow-engine tables — `POSTGRES_DB_PROD.PUBLIC`

**The flow tables are not in the reporting warehouse.** A `%flow%` search across every
`ORG_<uuid>` schema in `REPORTING_DB_PROD` returns nothing — the reporting warehouse carries only
the CRM object model. Reach for the CDC replica instead:

| Table | What it holds | Notable columns |
|---|---|---|
| `POSTGRES_DB_PROD.PUBLIC.USER_FLOW` | The flow *record* — the thing you build in the UI. Points at its versions. | `deployed_flow_definition_id`, `draft_flow_definition_id`, `is_active`, `folder_id`, `consecutive_failures`, `auto_disabled_at`, `auto_disabled_reason`, `node_state`, `last_run` |
| `POSTGRES_DB_PROD.PUBLIC.FLOW_DEFINITION` | A **versioned snapshot of the graph** for one `user_flow_id`. | `nodes`, `edges`, `variables`, `start_node_id`, `incoming_event_type`, `event_configuration`, `version_number`, `parent_flow_definition_id`, `management_type`, `deployed_at` |
| `POSTGRES_DB_PROD.PUBLIC.FLOW_RUN` | One execution. The interesting table for failure analysis. | `status`, `run_type`, `triggered_by_event_type`, `entity_id`/`entity_type`, `current_node_id`, `completed_node_ids`, `failed_node_ids`, `node_executions`, `runtime_state`, `input_data`/`output_data`, `error_msg`/`error_category`/`error_node_type`, `parent_run_id` |
| `POSTGRES_DB_PROD.PUBLIC.USER_FLOW_FOLDER` | Folder tree organizing flows. | `parent_id`, `owner_user_id` |

All four also carry `id`, `organization_id`, the audit set (`created_at` / `updated_at` /
`deleted_at` + matching `*_by_user_id`), and a CDC tail (`_deleted`, `_synced_at`, `_event_lsn`,
`_kafka_offset`). `DESCRIBE TABLE` for the full list rather than trusting this to stay complete.

**Types are not what you'd expect** — the replica lands almost everything as `TEXT`:

- **Ids and timestamps are `TEXT`**, not `UUID` / `TIMESTAMP`. `id`, `organization_id`,
  `user_flow_id`, `created_at`, `updated_at`, `deleted_at`, `completed_at` — all text. ISO-8601
  sorts correctly, so `min` / `max` / `>` comparisons work as-is, but **any date math needs a
  cast**: `created_at::timestamp_tz` (or `try_to_timestamp_tz(...)`) before `date_trunc`,
  `dateadd`, `datediff`.
- **`_synced_at` is a real `TIMESTAMP_TZ`** — the one exception, and the freshness check. This is a
  live CDC stream, so confirm `max(_synced_at)` before trusting a count off any of these tables.
- **JSON columns are `VARIANT`** — `nodes`, `edges`, `variables`, `node_executions`,
  `runtime_state`, `input_data`, `output_data`. Use `:` path syntax (`node_executions:foo`),
  `lateral flatten` to expand.

**Filter soft deletes — this one changes answers.** `deleted_at IS NOT NULL` marks a deleted row
and it stays in the table: **522 of 1,788 `user_flow` rows (29%) and 731 of 3,447
`flow_definition` rows are deleted**. Counting flows without the filter overstates the real number
by ~41%. `flow_run` currently has zero soft-deletes, and `_deleted` (the CDC hard-delete flag) is
`FALSE` across all four — so `deleted_at IS NULL` is the filter that matters:

```sql
WHERE deleted_at IS NULL AND _deleted = FALSE
```

**Filter internal orgs yourself.** `organization_id` is a plain column, so nothing scopes it for
you — ids are in the `reevo-internal-orgs` rule.

**`FLOW_RUN` is large** (~940k rows in prod). Always aggregate or `LIMIT`.

**Enum casing is inconsistent between columns — check before you filter.** On `FLOW_RUN`,
`status` is **lowercase** but `run_type` is **UPPERCASE**:

| Column | Values (prod) |
|---|---|
| `status` | `completed` (794k), `failed` (80k), `canceled` (68k — one `l`), `running` |
| `run_type` | `TRIGGER` (≈all), `MANUAL` (13) |

So `status = 'FAILED'` silently matches **nothing** while `run_type = 'TRIGGER'` matches
everything. When in doubt, `GROUP BY` the column first, or compare with `ilike`.

`POSTGRES_DB_DEV.PUBLIC` mirrors the same four tables at dev scale (~200 flows, ~9.6k runs).

A starter query with every convention above applied — customer flow-run volume and failure rate by
month:

```sql
SELECT date_trunc('month', created_at::timestamp_tz) AS mo,
       count(*)                                      AS runs,
       count_if(status = 'failed')                    AS failed
FROM POSTGRES_DB_PROD.PUBLIC.FLOW_RUN
WHERE deleted_at IS NULL
  AND _deleted = FALSE
  AND created_at::timestamp_tz >= dateadd('month', -3, current_timestamp())
  AND organization_id NOT IN (
        '4d29f892-7e25-4efa-ad0b-f348bd0fc0fc',  -- Reevo.ai - GTM
        'b3c5bc5d-1eae-4586-b9bd-db8486e6b689',  -- Reevo.ai (EPD)
        'a288b04b-7b77-4499-b907-6aa1764c92d1'   -- zvtest org
      )
GROUP BY 1 ORDER BY 1;
```

**Deprecated:** `WORKFLOW_TRIGGER_EVENT` sits in the same schema but is dead — last synced
2026-07-23, newest row created 2025-11-13. Don't build on it.

## Guardrails

- **Read-only by default.** The script checks the leading keyword of *every* `;`-separated
  statement and refuses anything that isn't `SELECT` / `WITH` / `SHOW` / `DESCRIBE` / `EXPLAIN` /
  `USE`. Pass `--write` to override deliberately.
- That check is a **seatbelt against typos, not a security boundary** — a `;` inside a string
  literal can trip a false refusal, and it is trivially bypassed with `--write`. The real
  protection is connecting with a **read-only Snowflake role**.
- **Prefer `LIMIT`.** Warehouse tables are large and every query burns warehouse credits.

## Prereqs

| | |
|---|---|
| CLI | `brew install snowflake-cli` (provides `snow`) |
| Connection | `reevo` — account `VOB45637`, warehouse `REPORTING_PROD_WH`, database `REPORTING_DB_PROD`, `externalbrowser` auth. Recreate with `snow connection add -n reevo -a VOB45637 -u <you> -w REPORTING_PROD_WH -d REPORTING_DB_PROD -A externalbrowser`. |
| Role | Not pinned on the connection — the session uses your Snowflake default role. `REPORTING_PROD_ROLE` is the backend *service* role; don't assume it's granted to a human user. Check with `SELECT current_role()`. |
| Auth | SSO via browser. Needs a browser reachable from the terminal — **the first login must happen in an interactive session**, not a background job. |
| Re-auth | The cached token covers roughly a working session; when it expires the script surfaces the CLI's auth error and you re-run the login. |

## Failure hints

- `snow: command not found` → `brew install snowflake-cli`.
- `no Snowflake connection named 'reevo'` → run the `snow connection add` line above. The script
  asks `snow connection list` rather than probing a config path, since that path is
  platform-dependent.
- Auth / token errors → re-run the browser login interactively; a background session cannot
  complete SSO.
- `refusing to run a non-read statement` → intended. Re-read the SQL; add `--write` only if the
  mutation is genuinely what you want.
