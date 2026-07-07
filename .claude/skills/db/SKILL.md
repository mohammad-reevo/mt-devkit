---
name: db
description: Query Postgres from my personal harness — the LOCAL Docker DB by default, or the shared Dev Aurora writer when I say "dev". Self-contained psql wrapper (personal rebuild of devkit's local-db + dev-db, no devkit dependency). Use for data investigation, debugging, verifying migrations, or checking state after backend ops. Full SQL (SELECT/INSERT/UPDATE/DELETE). Assume LOCAL unless I explicitly mention dev. Triggers on "query the db", "check the local db", "query the dev db", "look up X in postgres", "run this SQL".
---

# db — query Postgres (local by default, dev on request)

> Personal rebuild — self-contained. Consolidates devkit's `local-db` + `dev-db` into one
> skill. Self-contained: no devkit paths, scripts, or hooks.

## Target: assume local unless I say dev

**Default to the LOCAL Docker DB.** Only target dev when I explicitly say "dev" (or "dev db",
"on dev", "the shared dev database"). When in doubt it's local — never hit dev on a guess.

## How to run

```
bash $CLAUDE_PROJECT_DIR/.claude/skills/db/dbquery.sh [--dev] [--csv|--expanded|--tuples-only] "SQL"
```

- **Local (default):** `bash $CLAUDE_PROJECT_DIR/.claude/skills/db/dbquery.sh "SELECT count(*) FROM contact;"`
- **Dev:** add `--dev`: `bash $CLAUDE_PROJECT_DIR/.claude/skills/db/dbquery.sh --dev "SELECT count(*) FROM contact;"`
- `--csv` for machine-readable rows, `--expanded` for one-record vertical output, `--tuples-only`
  to drop headers/footers. psql meta-commands work too (`\dt`, `\d contact`).

The script resolves connection + credentials itself — never construct a raw `psql` command or
hardcode credentials.

## Targets

| | local (default) | dev (`--dev`) |
|---|---|---|
| host | `localhost:5432` | Aurora **writer** endpoint |
| db / user | `salestech_be` / `salestech_be` | `reevo_main` / `reevo_db_user` |
| password | trivial local Docker creds (baked in) | `DB_PASSWORD` env, else `chamber read reevo-be-dev salestech_be_db_pass` |
| prereqs | Docker + local backend up | **Tailscale VPN** + **chamber** + AWS SSO |

## Guardrails

- **Writes work on both targets** — SELECT/INSERT/UPDATE/DELETE all run. Review write SQL before
  running it, especially on dev (it's real shared data).
- **Dev always targets the writer** — the Dev RO replica is unreliable / out of sync. There is no
  read-only dev path here by design.
- **Preflight** — the script runs `pg_isready` first and gives a targeted hint on failure:
  - local unreachable → start the backend/Docker via env-manager (`run be`).
  - dev unreachable → connect Tailscale; if the chamber read fails with `UnrecognizedClientException`,
    run `aws sso login` and retry.

## Notes

- This is the personal replacement for devkit's `local-db`/`dev-db` skills and the `local-db.md`
  rule. Once stable, repoint any personal skill that still calls devkit's `local-db/dbquery.sh`
  (e.g. `spinup-local-db`'s verify step) at this script.
