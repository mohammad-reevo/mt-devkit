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
# never depends on local setup state. Comments are stripped and newlines folded to spaces
# BEFORE ';' becomes the separator, so a statement is a whole statement rather than one
# physical line — a multi-line SELECT is a single statement, and a trailing write still
# can't ride along behind a leading SELECT. A ';' inside a string literal can trip this into
# a false refusal — use --write when that happens.
if [[ "$ALLOW_WRITE" -eq 0 ]]; then
  # /* */ blocks go first (they may span lines), then -- line comments, and only then are
  # newlines folded. Order matters: folding first would let one -- comment swallow the rest
  # of the query, and leaving comments in would let one hide a statement from the check.
  while IFS= read -r statement; do
    trimmed=$(printf '%s' "$statement" | sed -E 's/^[[:space:](]+//; s/[[:space:]]+$//')
    [[ -z "$trimmed" ]] && continue
    keyword=$(printf '%s' "$trimmed" | awk '{print tolower($1)}')
    case "$keyword" in
      select|with|show|describe|desc|explain|use) ;;
      *)
        excerpt="$trimmed"
        [[ ${#excerpt} -gt 80 ]] && excerpt="${excerpt:0:80}..."
        echo "Error: refusing to run a non-read statement without --write:" >&2
        echo "  $excerpt" >&2
        echo "This warehouse holds a copy of production data. Re-run with --write if you meant it." >&2
        exit 1
        ;;
    esac
    # The here-string's trailing newline is load-bearing: `read` returns non-zero on a final
    # line without one, which would silently skip the check for a query with no trailing ';'.
  done <<< "$(printf '%s' "$SQL" | perl -0777 -pe 's{/\*.*?\*/}{ }gs' | sed -E 's/--.*$//' | tr '\n' ' ' | tr ';' '\n')"
fi

if ! command -v snow &>/dev/null; then
  echo "Error: the Snowflake CLI is not installed." >&2
  echo "Install it with: brew install snowflake-cli" >&2
  exit 1
fi

# Ask `snow` whether the connection exists rather than probing a config path: the CLI stores
# config at ~/Library/Application Support/snowflake/config.toml on macOS and
# ~/.snowflake/config.toml elsewhere, so any hardcoded path is wrong on some platform.
if ! snow connection list --format JSON 2>/dev/null | grep -q "\"connection_name\": \"$CONNECTION\""; then
  echo "Error: no Snowflake connection named '$CONNECTION' is configured." >&2
  echo "Create one with:" >&2
  echo "  snow connection add -n $CONNECTION -a <account> -u <user> -A externalbrowser" >&2
  echo "Existing connections: $(snow connection list --format JSON 2>/dev/null | grep '"connection_name"' | sed 's/.*: "//; s/".*//' | tr '\n' ' ')" >&2
  exit 1
fi

exec snow sql -c "$CONNECTION" --format "$FORMAT" -q "$SQL"
