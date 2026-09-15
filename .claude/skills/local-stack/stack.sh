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
Usage: stack.sh up|down|list [--name <worktree>] [-- <passthrough flags>]

  up     allocate a slot, preflight its ports, bring the stack up
  down   tear this worktree's stack down and free its slot
  list   show every allocated instance and its ports

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
  up|down|list) ;;
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

# --- list ---------------------------------------------------------------------
if [ "$MODE" = "list" ]; then
  ( cd "$BE_DIR" && uv run python -m scripts.local_dev.cli list )
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
port_holder() { lsof -nP -iTCP:"$1" -sTCP:LISTEN 2>/dev/null | awk 'NR==2 {print $1" (pid "$2")"}'; }

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

The slot is a hash of the instance name, so re-running under '$INSTANCE' lands on
slot $INDEX again. Free the port, or run the stack from a differently-named worktree.
Release this slot first:  stack.sh down --name $(basename "$WT")
EOF
  exit 1
fi

echo "slot $INDEX — backend :$BE_PORT  frontend :$FE_PORT  realtime :$RT_PORT"
# shellcheck disable=SC2086
( cd "$BE_DIR" && bash "$STACK_SCRIPTS/stack_up.sh" \
    --name "$INSTANCE" --fe-repo "$FE_DIR" --realtime-repo "$RT_DIR" $PASSTHRU )
