---
name: snowflake
description: Query the Reevo Snowflake reporting warehouse (a copy of production data) from my personal harness. Self-contained `snow` CLI wrapper, read-only by default. Use for reporting/analytics investigation, checking warehouse state, or verifying what the reporting pipeline landed. Distinct from `db`, which queries Postgres (local/dev). Triggers on "query snowflake", "check the warehouse", "look up X in snowflake", "query the reporting data".
---

# snowflake — query the reporting warehouse

> Personal harness tool, self-contained. Wraps the official `snow` CLI the same way `db` wraps
> `psql`. Auth lives in `~/.snowflake/connections.toml`; no credentials in this repo.

## Target

One target: the **Reevo Snowflake reporting warehouse**, which holds a **copy of production
data**. There is no local Snowflake. Treat every query as touching real prod-shaped data.

For Postgres (local Docker or shared Dev Aurora) use the **`db`** skill instead — the two are
unrelated stores.

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

## Finding your way around

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
| Connection | `snow connection add --connection-name reevo --authenticator externalbrowser` |
| Auth | SSO via browser. Needs a browser reachable from the terminal — **the first login must happen in an interactive session**, not a background job. |
| Re-auth | The cached token covers roughly a working session; when it expires the script surfaces the CLI's auth error and you re-run the login. |

## Failure hints

- `snow: command not found` → `brew install snowflake-cli`.
- `~/.snowflake/connections.toml missing` → run the `snow connection add` line above.
- Auth / token errors → re-run the browser login interactively; a background session cannot
  complete SSO.
- `refusing to run a non-read statement` → intended. Re-read the SQL; add `--write` only if the
  mutation is genuinely what you want.
