#!/usr/bin/env bash
# split.sh — Create N worktrees + briefs from a plan-split manifest, then print launch commands.
# Usage: split.sh <manifest-json-path>
set -euo pipefail

manifest="${1:?Usage: split.sh <manifest-json-path>}"

if [[ ! -f "$manifest" ]]; then
  echo "Error: manifest not found: $manifest" >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "Error: jq is required but not found in PATH" >&2
  exit 1
fi

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$repo_root" ]]; then
  echo "Error: not inside a git repository" >&2
  exit 1
fi

setup_script="$repo_root/.claude/skills/worktree/worktree_setup.sh"
use_setup_script=false
if [[ -x "$setup_script" || -f "$setup_script" ]]; then
  use_setup_script=true
fi

# Validate manifest structure
if ! jq -e '.parts | type == "array" and length > 0' "$manifest" >/dev/null; then
  echo "Error: manifest must contain a non-empty 'parts' array" >&2
  exit 1
fi

shared_context="$(jq -r '.shared_context // ""' "$manifest")"
n_parts="$(jq -r '.parts | length' "$manifest")"

# Pre-flight: validate every part and check for collisions before doing anything destructive
for i in $(seq 0 $((n_parts - 1))); do
  name="$(jq -r ".parts[$i].name // \"\"" "$manifest")"
  branch="$(jq -r ".parts[$i].branch // \"\"" "$manifest")"
  brief="$(jq -r ".parts[$i].brief // \"\"" "$manifest")"

  if [[ -z "$name" || -z "$branch" || -z "$brief" ]]; then
    echo "Error: part[$i] is missing name/branch/brief" >&2
    exit 1
  fi

  if [[ ! "$name" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    echo "Error: invalid part name '$name' (must be alphanumeric, _, or -)" >&2
    exit 1
  fi

  wt_path="$repo_root/worktrees/$name"
  if [[ -e "$wt_path" ]]; then
    echo "Error: worktree path already exists: $wt_path" >&2
    echo "       Remove it manually or rename the part, then retry." >&2
    exit 1
  fi
done

# Check for duplicate names
duplicate="$(jq -r '.parts | map(.name) | group_by(.) | map(select(length > 1) | .[0]) | .[]' "$manifest")"
if [[ -n "$duplicate" ]]; then
  echo "Error: duplicate part name(s): $duplicate" >&2
  exit 1
fi

mkdir -p "$repo_root/worktrees"

declare -a launch_lines

for i in $(seq 0 $((n_parts - 1))); do
  name="$(jq -r ".parts[$i].name" "$manifest")"
  branch="$(jq -r ".parts[$i].branch" "$manifest")"
  base="$(jq -r ".parts[$i].base // \"main\"" "$manifest")"
  brief="$(jq -r ".parts[$i].brief" "$manifest")"

  wt_path="$repo_root/worktrees/$name"

  echo "[$((i + 1))/$n_parts] Creating worktree '$name' at $wt_path (branch: $branch, base: $base)" >&2
  git -C "$repo_root" worktree add "$wt_path" -b "$branch" "$base" >&2

  if $use_setup_script; then
    echo "         Running worktree_setup.sh for '$name'..." >&2
    bash "$setup_script" "$wt_path" >&2 || {
      echo "         Warning: worktree_setup.sh exited non-zero for '$name' (continuing)" >&2
    }
  fi

  mkdir -p "$wt_path/.claude"
  brief_path="$wt_path/.claude/brief.md"

  jq -n \
    --arg name "$name" \
    --arg n "$n_parts" \
    --arg shared "$shared_context" \
    --arg brief "$brief" \
    --arg path "$wt_path" \
    --arg branch "$branch" \
    --arg base "$base" \
    -r '
"# \($name)

You are working on **\($name)**, one of \($n) parallel parts of a larger change. Other parts are being handled by sibling Claude sessions in sibling worktrees. Stay in your lane — coordinate through merged code, not by trying to talk to the other sessions.

## Shared context

\($shared)

## Your part

\($brief)

## Where you are

- Worktree: `\($path)`
- Branch: `\($branch)` (based on `\($base)`)
"
' > "$brief_path"

  echo "         Wrote brief: $brief_path" >&2

  launch_lines+=("# Part: $name")
  launch_lines+=("cd \"$wt_path\" && claude -n $name \"Read .claude/brief.md and start working on it.\"")
  launch_lines+=("")
done

echo "" >&2
echo "Done. Open $n_parts new VSCode terminals (Ctrl+Shift+\`) and paste one block per terminal:" >&2
echo "" >&2

for line in "${launch_lines[@]}"; do
  printf '%s\n' "$line"
done
