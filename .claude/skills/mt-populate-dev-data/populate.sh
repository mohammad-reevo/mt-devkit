#!/usr/bin/env bash
set -euo pipefail

# mt-populate-dev-data — personal rebuild of devkit's populate-dev-data. mt- prefix temporary.
# Runs ONLY the destructive local-DB refresh from cloud DEV: Docker volume wipe + deps restart +
# the ~30-min DEV→local copy. Backend lifecycle (kill/run) and FalkorDB indexing are driven from
# SKILL.md via env-manager + a direct uv command — NOT here — so this script stays free of devkit's
# start-backend scripts and of interactive zsh aliases.
#
# The local Docker DB is singular (shared across worktrees), so this always targets the main
# salestech-be checkout. Override with SALESTECH_BE_ROOT if yours lives elsewhere.

SALESTECH_BE_ROOT="${SALESTECH_BE_ROOT:-$HOME/Desktop/code/devkit/salestech-be}"

if [[ ! -f "$SALESTECH_BE_ROOT/Makefile" ]]; then
  echo "Error: no salestech-be Makefile at $SALESTECH_BE_ROOT" >&2
  echo "Set SALESTECH_BE_ROOT to your salestech-be checkout and retry." >&2
  exit 1
fi

cd "$SALESTECH_BE_ROOT"

echo "=== Phase 1: clean up Docker volumes (wipes the local DB) ==="
make docker-cleanup-dep

echo "=== Phase 2: start Docker containers ==="
make docker-start-dep

echo "=== Phase 3: copy DEV database → local (this takes ~30 minutes; do NOT interrupt) ==="
make refresh-docker-db-from-cloud-dev-db

echo "=== DB refresh done ==="
echo "Next (driven from the mt-populate-dev-data SKILL.md):"
echo "  1. Start the backend via env-manager ('run be') — applies migrations + starts workers."
echo "  2. Trigger FalkorDB re-indexing (uv run ... trigger_specific_organization_indexing)."
echo "  3. Reconcile admin user + onboarding, then verify — both via mt-db."
