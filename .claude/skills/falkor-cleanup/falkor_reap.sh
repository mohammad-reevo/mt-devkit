#!/usr/bin/env bash
# Reap every local FalkorDB org graph except an explicit keep-list.
#
# Each org graph is one Redis key (`org_<uuid-hex>`, type `graphdata`) carrying
# ~182 indexes — ~20 MB whether or not the org holds data. Integration tests mint
# one org per test, so the graphs, not the rows, are what fill the Docker VM.
# This deletes graphs only: Postgres and Kafka are never touched.
set -uo pipefail

CONTAINER="${FALKOR_CONTAINER:-salestech-be-salestech_be-falkordb-1}"
DEFAULT_KEEP="00000000-0000-4000-a000-000000000001"

DRY_RUN=0
KEEP_UUIDS=()

usage() {
  cat <<'USAGE'
Usage: falkor_reap.sh [--dry-run] [--keep <org-uuid>]...

  --dry-run        List what would be deleted; delete nothing.
  --keep <uuid>    Keep this org's graph. Repeatable. Defaults to the local
                   dev-seed org 00000000-0000-4000-a000-000000000001 when no
                   --keep is given; passing --keep replaces that default.

Env:
  FALKOR_CONTAINER  Override the container name.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --keep)    KEEP_UUIDS+=("${2:?--keep needs a uuid}"); shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

[[ ${#KEEP_UUIDS[@]} -eq 0 ]] && KEEP_UUIDS=("$DEFAULT_KEEP")

# Skip quietly rather than fail: this runs as a step of `run docker`, and a
# stopped daemon/container simply means there is nothing to reap yet.
if ! docker info >/dev/null 2>&1; then
  echo "falkor-reap: docker daemon not running — nothing to do."
  exit 0
fi
if [[ "$(docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null)" != "true" ]]; then
  echo "falkor-reap: $CONTAINER is not running — nothing to do."
  exit 0
fi

# Both graph-name forms: the default `org_<hex>` and the `org_v2:<uuid>` shape
# behind falkordb_use_updated_org_graph_name, so flipping that flag can never
# make the reaper delete the org it was told to keep.
KEEP_NAMES=""
for u in "${KEEP_UUIDS[@]}"; do
  hex="${u//-/}"
  KEEP_NAMES="$KEEP_NAMES org_${hex} org_v2:${u}"
done

read_state() {
  local graphs mem
  # No `|| echo 0` here: `grep -c` already prints 0 and exits 1 on no match,
  # so a fallback would append a second line and corrupt the count.
  graphs="$(docker exec "$CONTAINER" redis-cli GRAPH.LIST 2>/dev/null | grep -c .)"
  mem="$(docker exec "$CONTAINER" redis-cli INFO memory 2>/dev/null \
         | sed -n 's/^used_memory_human:\(.*\)$/\1/p' | tr -d '\r')"
  echo "${graphs}|${mem:-unknown}"
}

BEFORE="$(read_state)"
BEFORE_GRAPHS="${BEFORE%%|*}"
BEFORE_MEM="${BEFORE##*|}"

if [[ "$BEFORE_GRAPHS" == "0" ]]; then
  echo "falkor-reap: no graphs present (memory ${BEFORE_MEM}) — nothing to do."
  exit 0
fi

DOOMED="$(docker exec -e KEEP="$KEEP_NAMES" "$CONTAINER" sh -c '
  redis-cli GRAPH.LIST 2>/dev/null | tr -d "\r" | while IFS= read -r g; do
    [ -n "$g" ] || continue
    case " $KEEP " in *" $g "*) continue ;; esac
    printf "%s\n" "$g"
  done' 2>/dev/null)"

DOOMED_COUNT="$(printf '%s' "$DOOMED" | grep -c . || true)"

if [[ "$DOOMED_COUNT" == "0" ]]; then
  echo "falkor-reap: ${BEFORE_GRAPHS} graph(s), all on the keep-list — nothing to do (${BEFORE_MEM})."
  exit 0
fi

if [[ "$DRY_RUN" == "1" ]]; then
  echo "falkor-reap [dry-run]: would delete ${DOOMED_COUNT} of ${BEFORE_GRAPHS} graph(s), currently ${BEFORE_MEM}."
  echo "keeping:${KEEP_NAMES}"
  printf '%s\n' "$DOOMED" | head -10 | sed 's/^/  - /'
  [[ "$DOOMED_COUNT" -gt 10 ]] && echo "  … and $((DOOMED_COUNT - 10)) more"
  exit 0
fi

# Warn but proceed: deleting while the CDC consumers run risks a graph being
# implicitly recreated by an in-flight write. The intended window is after
# `d-up` and before `run-be`.
if lsof -ti:8000 >/dev/null 2>&1; then
  echo "falkor-reap: WARNING — something is listening on :8000 (backend up?)."
  echo "             Reaping is safest between 'd-up' and 'run-be'."
fi

# One exec for the whole loop: 200+ individual `docker exec` calls cost minutes.
docker exec -e KEEP="$KEEP_NAMES" "$CONTAINER" sh -c '
  redis-cli GRAPH.LIST 2>/dev/null | tr -d "\r" | while IFS= read -r g; do
    [ -n "$g" ] || continue
    case " $KEEP " in *" $g "*) continue ;; esac
    redis-cli GRAPH.DELETE "$g" >/dev/null 2>&1
  done' >/dev/null 2>&1

# Persist, so a restart reloads the reaped set rather than the old dump. The
# fork is cheap now that the dataset is small — the SIGBUS-on-BGSAVE failures
# in the old runbook were a symptom of size, not an independent fault.
docker exec "$CONTAINER" redis-cli BGSAVE >/dev/null 2>&1
for _ in $(seq 1 30); do
  status="$(docker exec "$CONTAINER" redis-cli INFO persistence 2>/dev/null \
            | sed -n 's/^rdb_bgsave_in_progress:\(.*\)$/\1/p' | tr -d '\r')"
  [[ "$status" == "0" ]] && break
  sleep 1
done
SAVE_STATUS="$(docker exec "$CONTAINER" redis-cli INFO persistence 2>/dev/null \
               | sed -n 's/^rdb_last_bgsave_status:\(.*\)$/\1/p' | tr -d '\r')"

AFTER="$(read_state)"
AFTER_GRAPHS="${AFTER%%|*}"
AFTER_MEM="${AFTER##*|}"

echo "falkor-reap: ${BEFORE_GRAPHS} → ${AFTER_GRAPHS} graph(s), ${BEFORE_MEM} → ${AFTER_MEM} (bgsave: ${SAVE_STATUS:-unknown})"

if [[ "${SAVE_STATUS}" != "ok" ]]; then
  echo "falkor-reap: bgsave did not report ok — the reap holds in memory but may not survive a restart." >&2
  exit 1
fi
