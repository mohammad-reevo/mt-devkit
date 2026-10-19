#!/usr/bin/env bash
# mt-devkit local-stack — one port-isolated stack per worktree.
#
# Thin wrapper over salestech-be's reevo-local-stack scripts. It does the three
# things that skill cannot do from here, then delegates:
#   1. derives all three repo paths from the worktree name
#   2. derives the instance id from the worktree name (the BE default is unusable
#      in this layout — see resolve_instance below)
#   3. preflights the derived ports before anything launches
#
# Targets bash 3.2 (macOS system bash): no associative arrays, no `;;&`.
set -euo pipefail

MAIN_DEFAULT="$HOME/Desktop/code/mt-devkit"
MODE=""
WT_NAME=""
PASSTHRU=""

usage() {
  cat <<'EOF'
Usage: stack.sh up|down|list|down-all|seed-pool [--name <worktree>] [-- <passthrough flags>]

  up         take the lowest free pool slot (1-5), preflight its ports, bring the stack up
  down       tear this worktree's stack down and free its slot
  list       show every allocated instance, its ports, and which ports are listening
  down-all   tear down every allocated instance (env-manager's `kill stacks`)
  seed-pool  seed + bootstrap the pool orgs (slots 1-5) once; re-running is safe

  --name <worktree>   worktree under <main>/worktrees/ (default: the one cwd sits in)

Anything after `--` is passed straight to the underlying script:
  up    --workers <groups> | --askreevo | --no-fe | --skip-org-setup
  down  --restore-env

Examples:
  stack.sh up
  stack.sh up --name planner-inline-first -- --askreevo --skip-org-setup
  stack.sh down --name planner-inline-first
EOF
}

# --- argument parsing ---------------------------------------------------------
[ $# -gt 0 ] || { usage; exit 2; }
MODE="$1"; shift
case "$MODE" in
  up|down|list|down-all|seed-pool) ;;
  -h|--help) usage; exit 0 ;;
  *) echo "error: unknown mode '$MODE'" >&2; usage; exit 2 ;;
esac

while [ $# -gt 0 ]; do
  case "$1" in
    --name) WT_NAME="$2"; shift 2 ;;
    --) shift; PASSTHRU="$*"; break ;;
    -h|--help) usage; exit 0 ;;
    *) echo "error: unknown option '$1' (put script flags after \`--\`)" >&2; exit 2 ;;
  esac
done

# --- resolve the worktree -----------------------------------------------------
# A worktree is the dir holding salestech-be/ and frontend-monorepo/ as siblings —
# the same shape env-manager resolves, so both skills agree on what a worktree is.
is_worktree_root() { [ -d "$1/salestech-be" ] && [ -d "$1/frontend-monorepo" ]; }

resolve_worktree() {
  local main dir
  if [ -n "$WT_NAME" ]; then
    main="$(git -C "$MAIN_DEFAULT" worktree list 2>/dev/null | head -1 | awk '{print $1}')"
    [ -n "$main" ] || main="$MAIN_DEFAULT"
    printf '%s' "$main/worktrees/$WT_NAME"
    return
  fi
  dir="$(pwd -P)"
  while [ "$dir" != "/" ]; do
    if is_worktree_root "$dir"; then printf '%s' "$dir"; return; fi
    dir="$(dirname "$dir")"
  done
  echo "error: not inside a worktree — pass --name <worktree>" >&2
  exit 1
}

WT="$(resolve_worktree)"
is_worktree_root "$WT" || { echo "error: no worktree at $WT" >&2; exit 1; }

BE_DIR="$WT/salestech-be"
FE_DIR="$WT/frontend-monorepo"
RT_DIR="$WT/reevo-realtime"
for d in "$BE_DIR" "$FE_DIR" "$RT_DIR"; do
  [ -d "$d" ] || { echo "error: missing sub-repo worktree: $d" >&2; exit 1; }
done

STACK_SCRIPTS="$BE_DIR/.claude/skills/reevo-local-stack/scripts"
[ -d "$STACK_SCRIPTS" ] || {
  echo "error: reevo-local-stack scripts not found at $STACK_SCRIPTS" >&2
  echo "       (this worktree's salestech-be branch may predate them)" >&2
  exit 1
}

# --- instance id --------------------------------------------------------------
# Always derived from the PARENT worktree dir name, and always passed explicitly.
# The BE scripts' own default is `default_instance_id()`, which normalizes the
# basename of `git rev-parse --show-toplevel` run inside the BE checkout. In this
# layout that is always literally "salestech-be" -> "salestech_be", identical for
# every worktree — so the second stack would hit InstanceIdConflict (same id, a
# different workspace_path). Passing --name is not a convenience here; it is what
# makes more than one stack possible at all.
normalize_instance_id() {
  local out
  out="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9_]/_/g')"
  case "$out" in [a-z]*) ;; *) out="s$out" ;; esac
  printf '%s' "$(printf '%s' "$out" | cut -c1-30)"
}

INSTANCE="$(normalize_instance_id "$(basename "$WT")")"

# --- pool ---------------------------------------------------------------------
# Every stack draws from a fixed pool of POOL_SIZE orgs, seeded once by `seed-pool`:
# REEVO_SLOT_POOL makes the allocator hand out the lowest free slot, and the org is
# derived from the slot, so the Nth concurrent stack runs on pool org N. A pool org
# is never created per stack and never removed, so connections added to it by hand
# (Outreach OAuth) survive every down/up.
POOL_SIZE=5
# A salestech-be branch cut before the pool landed has neither the allocator's
# REEVO_SLOT_POOL nor stack_up.sh's --org-token-only. Legit business flow: such a
# stack runs exactly as before (hashed slot, its own per-slot org), not an error.
if grep -q -- '--org-token-only' "$STACK_SCRIPTS/stack_up.sh"; then
  POOL=1
  export REEVO_SLOT_POOL="$POOL_SIZE"
else
  POOL=0
  echo "note: this worktree's salestech-be predates the org pool — hashed slot, per-slot org" >&2
fi

# Every registry record as "<index> <instance id> <salestech-be path>", one per line.
registry_records() {
  ( cd "$BE_DIR" && uv run python - <<'PY'
from scripts.local_dev.instance_isolation import InstanceRegistry

for record in InstanceRegistry().list_all():
    print(record.index, record.instance_id, record.workspace_path)
PY
  )
}

port_state() { lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1 && echo "up" || echo "down"; }

# --- list ---------------------------------------------------------------------
# The registry says which slots are claimed, not whether anything still runs on
# them, so each port is probed the way env-manager's `check` rows do.
if [ "$MODE" = "list" ]; then
  records="$(registry_records)"
  [ -n "$records" ] || { echo "no stacks allocated"; exit 0; }
  printf '%s\n' "$records" | while read -r index id path; do
    be=$((8000 + index)); fe=$((3000 + index)); rt=$((8787 + index))
    printf '  [%2s] %-24s backend :%s %s · frontend :%s %s · realtime :%s %s   %s\n' \
      "$index" "$id" "$be" "$(port_state "$be")" "$fe" "$(port_state "$fe")" \
      "$rt" "$(port_state "$rt")" "$(dirname "$path")"
  done
  exit 0
fi

# --- down-all -----------------------------------------------------------------
# Each stack is torn down by its own worktree's stack_down.sh, so a stack on an older
# salestech-be branch is stopped by the scripts it was started with.
if [ "$MODE" = "down-all" ]; then
  records="$(registry_records)"
  [ -n "$records" ] || { echo "no stacks allocated"; exit 0; }
  printf '%s\n' "$records" | while read -r index id path; do
    wt="$(dirname "$path")"
    if ! is_worktree_root "$wt"; then
      # Legit business flow: a stack started outside the mt-devkit layout has no
      # sibling frontend/realtime to derive; it is named in the output, left running,
      # and the caller reports it.
      echo "left running: '$id' (slot $index) — $path is not an mt-devkit worktree; stop it with \`reevo-local down $id\`"
      continue
    fi
    echo "tearing down '$id' (slot $index, worktree: $wt)"
    ( cd "$path" && bash "$path/.claude/skills/reevo-local-stack/scripts/stack_down.sh" \
        --name "$id" --fe-repo "$wt/frontend-monorepo" --realtime-repo "$wt/reevo-realtime" ) </dev/null
  done
  exit 0
fi

# --- seed-pool ----------------------------------------------------------------
if [ "$MODE" = "seed-pool" ]; then
  [ "$POOL" -eq 1 ] || { echo "error: seed-pool needs a salestech-be with the org pool (run it from main)" >&2; exit 1; }
  for slot in $(seq 1 "$POOL_SIZE"); do
    echo "seeding pool org for slot $slot…"
    ( cd "$BE_DIR" && uv run python -m scripts.local_dev.cli org-setup --slot "$slot" )
  done
  echo "pool seeded: slots 1-$POOL_SIZE. Add per-org integrations (e.g. Outreach) by hand, once."
  exit 0
fi

# --- down ---------------------------------------------------------------------
if [ "$MODE" = "down" ]; then
  echo "tearing down '$INSTANCE' (worktree: $WT)"
  # shellcheck disable=SC2086
  ( cd "$BE_DIR" && bash "$STACK_SCRIPTS/stack_down.sh" \
      --name "$INSTANCE" --fe-repo "$FE_DIR" --realtime-repo "$RT_DIR" $PASSTHRU )
  exit 0
fi

# --- up -----------------------------------------------------------------------
# Allocate the slot first so the ports are knowable before anything launches.
# `registry.allocate` is idempotent for the same workspace, and stack_up.sh runs
# the same `up --no-launch` itself, so this costs a repeat of a step that was
# already going to happen rather than adding a new side effect.
echo "allocating slot for '$INSTANCE' (worktree: $WT)"
( cd "$BE_DIR" && uv run python -m scripts.local_dev.cli up "$INSTANCE" --no-launch >/dev/null )

INDEX="$(cd "$BE_DIR" && uv run python - "$INSTANCE" <<'PY'
import sys
from scripts.local_dev.instance_isolation import InstanceRegistry

record = InstanceRegistry().lookup(instance_id=sys.argv[1])
if record is None:
    raise SystemExit(f"instance {sys.argv[1]!r} missing from the registry")
print(record.index)
PY
)"

BE_PORT=$((8000 + INDEX))
FE_PORT=$((3000 + INDEX))
RT_PORT=$((8787 + INDEX))

# Preflight. Nothing in the BE scripts or the allocator checks whether a derived
# port is actually free — the allocator only avoids indices already in its own
# registry. That is how slot 10 (frontend 3010, which the dep stack publishes as
# FalkorDB's browser UI) gets handed out: the frontend then dies, or Next quietly
# moves to 3011 while every env var still says 3010, and neither failure mentions
# FalkorDB. Catch it here instead, before any env file is rewritten.
# lsof exits 1 when nothing listens; under pipefail + -e that would end the script
# on exactly the free port we want, so a free port must read as empty output.
port_holder() { lsof -nP -iTCP:"$1" -sTCP:LISTEN 2>/dev/null | awk 'NR==2 {print $1" (pid "$2")"}' || true; }

BUSY=""
for pair in "backend:$BE_PORT" "frontend:$FE_PORT" "realtime:$RT_PORT"; do
  label="${pair%%:*}"; port="${pair##*:}"
  holder="$(port_holder "$port")"
  [ -n "$holder" ] && BUSY="$BUSY  $label port $port — held by $holder"$'\n'
done

if [ -n "$BUSY" ]; then
  echo "error: slot $INDEX derives a port that is already in use:" >&2
  printf '%s' "$BUSY" >&2
  cat >&2 <<EOF

Free the port, then re-run. The slot stays claimed until you release it:
  stack.sh down --name $(basename "$WT")
EOF
  exit 1
fi

# A pool org is already seeded, so the slow org-setup (migrate + seed + bootstrap)
# is skipped and only the frontend's session token is written for this slot's org —
# which can differ from this worktree's last run, so the token is never reused.
if [ "$POOL" -eq 1 ]; then
  case " $PASSTHRU " in
    *" --skip-org-setup "*) ;;
    *) PASSTHRU="$PASSTHRU --org-token-only" ;;
  esac
fi

echo "slot $INDEX — backend :$BE_PORT  frontend :$FE_PORT  realtime :$RT_PORT"
# shellcheck disable=SC2086
( cd "$BE_DIR" && bash "$STACK_SCRIPTS/stack_up.sh" \
    --name "$INSTANCE" --fe-repo "$FE_DIR" --realtime-repo "$RT_DIR" $PASSTHRU )
