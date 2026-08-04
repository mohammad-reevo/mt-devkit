#!/usr/bin/env bash
set -euo pipefail

# snowflake — query the Reevo Snowflake reporting warehouse via the `snow` CLI.
# Self-contained: no devkit paths. Credentials live in ~/.snowflake/connections.toml
# (created by `snow connection add`) and are never read into this script or the conversation.

CONNECTION="${SNOWFLAKE_CONNECTION:-reevo}"
FORMAT="TABLE"
ALLOW_WRITE=0
SQL=""

usage() {
  cat <<EOF
Usage: snowquery.sh [OPTIONS] "SQL"

Query the Reevo Snowflake warehouse. Read-only by default.

Options:
  --csv               CSV output
  --json              JSON output
  --write             Allow mutating statements (see guardrail note below)
  -c, --connection N  Named connection to use (default: \$SNOWFLAKE_CONNECTION, else "reevo")
  -h, --help          Show this help

Examples:
  snowquery.sh "SELECT current_account(), current_role(), current_warehouse();"
  snowquery.sh --csv "SELECT table_schema, table_name FROM information_schema.tables LIMIT 20;"
  snowquery.sh --json "SELECT count(*) AS n FROM my_table;"

Guardrail: statements are checked client-side and anything that isn't a read is refused
unless --write is passed. That is a seatbelt against typos, not a security boundary — the
real protection is connecting with a read-only Snowflake role.
EOF
  exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --csv)             FORMAT="CSV";       shift ;;
    --json)            FORMAT="JSON";      shift ;;
    --write)           ALLOW_WRITE=1;      shift ;;
    -c|--connection)   CONNECTION="$2";    shift 2 ;;
    -h|--help)         usage ;;
    *)                 SQL="$1";           shift ;;
  esac
done

if [[ -z "$SQL" ]]; then
  echo "Error: no SQL query provided." >&2
  usage 1
fi

# Read-only guard runs before any connection checks so that refusing a dangerous statement
# never depends on local setup state. Splits on ';' and checks the leading keyword of every
# statement, so a trailing write can't ride along behind a leading SELECT. A ';' inside a
# string literal can trip this into a false refusal — use --write when that happens.
if [[ "$ALLOW_WRITE" -eq 0 ]]; then
  while IFS= read -r statement; do
    keyword=$(printf '%s' "$statement" | sed -E 's/^[[:space:](]+//' | awk '{print tolower($1)}')
    [[ -z "$keyword" ]] && continue
    case "$keyword" in
      select|with|show|describe|desc|explain|use) ;;
      *)
        echo "Error: refusing to run a non-read statement (\"$keyword\") without --write." >&2
        echo "This warehouse holds a copy of production data. Re-run with --write if you meant it." >&2
        exit 1
        ;;
    esac
    # The trailing newline is load-bearing: `read` returns non-zero on a final line without
    # one, which would silently skip the check for a query that has no trailing ';'.
  done < <(printf '%s\n' "$SQL" | tr ';' '\n')
fi

if ! command -v snow &>/dev/null; then
  echo "Error: the Snowflake CLI is not installed." >&2
  echo "Install it with: brew install snowflake-cli" >&2
  exit 1
fi

if [[ ! -f "$HOME/.snowflake/connections.toml" ]]; then
  echo "Error: no Snowflake connection is configured (~/.snowflake/connections.toml missing)." >&2
  echo "Create one with:" >&2
  echo "  snow connection add --connection-name $CONNECTION --authenticator externalbrowser" >&2
  exit 1
fi

exec snow sql -c "$CONNECTION" --format "$FORMAT" -q "$SQL"
