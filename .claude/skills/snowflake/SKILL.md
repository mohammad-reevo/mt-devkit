---
name: snowflake
description: Query Reevo's Snowflake account (a copy of production data) from my personal harness — both the reporting warehouse (`REPORTING_DB_*`, per-org CRM object model) and the CDC replica of the app Postgres (`POSTGRES_DB_*`, raw application tables). Runs through the Snowflake MCP connector — no login, works in background sessions. Use for reporting/analytics investigation, checking warehouse state, verifying what the reporting pipeline landed, or reading prod application tables that `db` can't reach — including the workflow/flow-engine tables (`user_flow`, `flow_definition`, `flow_run`, `user_flow_folder`). Distinct from `db`, which queries live Postgres (local/dev only). Triggers on "query snowflake", "check the warehouse", "look up X in snowflake", "query the reporting data", "how many flows/flow runs", "query user_flow / flow_definition / flow_run".
---

# snowflake — query the reporting warehouse + app-Postgres replica

> Personal harness tool. Queries go through the **Snowflake MCP connector**, which authenticates
> with a self-refreshing OAuth token — no browser step, and it works in a background session.
> No credentials in this repo.

## Target

One Snowflake account, **two databases that hold different things** — pick by what you're after:

| Database | What it is | Shape |
|---|---|---|
| `REPORTING_DB_PROD` / `_DEV` | The **reporting warehouse** — the modeled CRM object model. | One schema per organization (`ORG_<uuid>`). |
| `POSTGRES_DB_PROD` / `_DEV` | A **CDC replica of the app Postgres** — raw application tables, incl. the workflow/flow tables. | One flat `PUBLIC` schema; org-scoped by an `organization_id` column. |

Both hold a **copy of production data**. There is no local Snowflake. Treat every query as
touching real prod-shaped data.

The **`db`** skill queries *live* Postgres — local Docker or shared Dev Aurora — and **cannot
reach prod**. So `POSTGRES_DB_PROD` here is the only prod read path I can reach on my own — but it
is a lagging copy, so for anything time-sensitive ask the user instead (see below).

## How to run

Call **`mcp__claude_ai_Snowflake__sql_exec_tool`** with a single SQL statement. That is the whole
interface — there is no wrapper script and no `snow` CLI.

```
mcp__claude_ai_Snowflake__sql_exec_tool(sql: "SELECT current_account(), current_role()")
```

The session runs as your own user with role `ACCOUNT_READONLY`, on warehouse `COMPUTE_WH`.

**If the tool isn't there**, the connector isn't set up or Claude Code hasn't restarted since it
was — see [Prereqs](#prereqs).

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

## Snowflake lags prod — don't use it for fresh incidents

Snowflake is a **synced copy**, not the live database. Rows arrive after a delay, so anything that
happened very recently may be missing or stale here.

**When recency matters — a live incident, a bug reported minutes ago, "did this just change?" —
say so and ask me to run the query against the prod Postgres directly.** Don't present
possibly-stale Snowflake numbers as the current state of prod. The `db` skill only reaches
local/dev, so I am the only path to live prod.

For `POSTGRES_DB_*` tables, `max(_synced_at)` shows how current the replica is — check it before
trusting a count.

## Guardrails

- **Nothing screens your SQL.** There is no client-side read-only check — whatever you send is
  what runs. The only thing standing between a typo and production is the `ACCOUNT_READONLY` role.
  Read the statement before you send it.
- **This is a copy of production data.** Treat every query as touching real customer rows.
- **Prefer `LIMIT`.** Warehouse tables are large and every query burns warehouse credits.

## Prereqs

| | |
|---|---|
| Setup | Add the Snowflake connector in **Claude Desktop** → Connectors → Add → Browse connectors → Snowflake. Fill Server URL / Client ID / Client Secret from the 1Password item *"Snowflake MCP OAuth client ID / secret"*. It then propagates to Claude Code. Steps live in the team SOP, *"[SOP] Snowflake MCP — Personal Pro Max Setup"*. |
| Server URL | `https://rfykuqb-okb87613.snowflakecomputing.com/api/v2/databases/FIVETRAN_DATABASE/schemas/MCP/mcp-servers/CLAUDE_MCP_SERVER` |
| Auth | OAuth, self-refreshing. No browser step after the one-time setup, so it works in a background session. |
| Role | `ACCOUNT_READONLY` — reaches `REPORTING_DB_*`, `POSTGRES_DB_*`, `FIVETRAN_DATABASE`, `AI_TRACES` and the rest. Confirm with `SELECT current_role()`. |
| Don't use `claude mcp add` | The CLI flow's `localhost` callback is not in the integration's allowed redirect URIs, so authorization fails with *"There is a mismatch in the given redirect uri with the one in the registered OAuth client integration."* Desktop's callback is registered; the CLI's is not. |

## Failure hints

- **Tool not available** → the connector isn't set up, or Claude Code hasn't been restarted since
  it was. The MCP list is read at session start.
- **Redirect-uri mismatch during authorization** → you registered the server via `claude mcp add`
  instead of the Desktop connector. Remove it (`claude mcp remove snowflake -s user`) and set it
  up in Desktop.
- **Empty result from an unqualified table name** → reporting data is per-org; fully qualify as
  `<database>.<schema>.<table>`.
