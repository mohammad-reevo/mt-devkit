#!/usr/bin/env bash
set -euo pipefail

# mt-db — personal rebuild of devkit's local-db + dev-db, consolidated. mt- prefix temporary.
# Self-contained: no devkit paths, scripts, or hooks. Queries Postgres via psql.
#   default target: local Docker DB.   --dev: shared Dev Aurora WRITER (Tailscale + chamber).

TARGET="local"
PSQL_FLAGS=()
SQL=""

usage() {
  cat <<EOF
Usage: dbquery.sh [--dev] [OPTIONS] "SQL"

Query Postgres. Default target is the local Docker DB; pass --dev for the shared
Dev Aurora writer (requires Tailscale VPN + chamber).

Target:
  (default)       Local Docker Postgres (localhost:5432)
  --dev           Dev Aurora WRITER (reevo_main) — writes hit real dev data; review first
  --local         Force local (the default; here for explicitness)

Options:
  --csv           CSV output
  --expanded      Vertical (expanded) output
  --tuples-only   No headers / row-count footer
  -h, --help      Show this help

Examples:
  dbquery.sh "SELECT count(*) FROM contact;"
  dbquery.sh --csv "SELECT id, name FROM contact LIMIT 5;"
  dbquery.sh --dev --expanded "SELECT * FROM oauth_provider LIMIT 1;"
EOF
  exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dev)         TARGET="dev";        shift ;;
    --local)       TARGET="local";      shift ;;
    --csv)         PSQL_FLAGS+=(--csv); shift ;;
    --expanded)    PSQL_FLAGS+=(-x);    shift ;;
    --tuples-only) PSQL_FLAGS+=(-t);    shift ;;
    -h|--help)     usage ;;
    *)             SQL="$1";            shift ;;
  esac
done

if [[ -z "$SQL" ]]; then
  echo "Error: no SQL query provided." >&2
  usage 1
fi

if [[ "$TARGET" == "dev" ]]; then
  # Dev RO replica is unreliable / out of sync — always target the writer on Dev.
  DB_HOST="reevo-dev-v2-aurora-rds.cluster-cjg208q4q0s8.us-west-2.rds.amazonaws.com"
  DB_PORT="5432"
  DB_NAME="reevo_main"
  DB_USER="reevo_db_user"
  export PGPASSWORD
  if [[ -n "${DB_PASSWORD:-}" ]]; then
    PGPASSWORD="$DB_PASSWORD"
  elif command -v chamber &>/dev/null; then
    # Stale SSO surfaces here as UnrecognizedClientException — run `aws sso login` and retry.
    PGPASSWORD=$(chamber read "reevo-be-dev" "salestech_be_db_pass" -q)
  else
    echo "Error: dev target needs DB_PASSWORD set, or chamber installed (brew install chamber)." >&2
    exit 1
  fi
  if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -q 2>/dev/null; then
    echo "Error: cannot reach the Dev writer at $DB_HOST:$DB_PORT" >&2
    echo "Make sure Tailscale VPN is connected (and 'aws sso login' if the token is stale)." >&2
    exit 1
  fi
else
  DB_HOST="${DB_HOST:-localhost}"
  DB_PORT="${DB_PORT:-5432}"
  DB_NAME="${DB_NAME:-salestech_be}"
  DB_USER="${DB_USER:-salestech_be}"
  export PGPASSWORD="${DB_PASS:-salestech_be}"
  if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -q 2>/dev/null; then
    echo "Error: local PostgreSQL is not reachable at $DB_HOST:$DB_PORT" >&2
    echo "Make sure Docker + the local backend are up (run the backend via env-manager: 'run be')." >&2
    exit 1
  fi
fi

exec psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" ${PSQL_FLAGS[@]+"${PSQL_FLAGS[@]}"} -c "$SQL"
