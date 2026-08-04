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
