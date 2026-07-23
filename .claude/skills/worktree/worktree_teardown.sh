#!/usr/bin/env bash
# worktree_teardown.sh — remove a worktree and its local feature branches.
#
# Usage: worktree_teardown.sh <name> <main-repo-abs-path>
#
# Removes the sub-repo worktrees + the parent worktree, and deletes the local
# `mohammad/<name>` branches. REMOTE branches are NEVER touched — they back open PRs and
# GitHub deletes them on merge. Run from OUTSIDE the target worktree (all git ops use -C).
set -euo pipefail

name="${1:?Usage: worktree_teardown.sh <name> <main-repo-path>}"
main="${2:?main repo path required}"
wt="${main}/worktrees/${name}"
branch="mohammad/${name}"

# Sub-repo worktrees + local branches
for subrepo in salestech-be frontend-monorepo reevo-realtime; do
    src="${main}/${subrepo}"
    dst="${wt}/${subrepo}"
    [[ -d "$src" ]] || continue
    git -C "$src" worktree remove --force "$dst" 2>/dev/null || true
    git -C "$src" worktree prune 2>/dev/null || true
    git -C "$src" branch -D "$branch" 2>/dev/null || true   # local only; remote left intact
done

# Parent-workspace worktree + local branch
git -C "$main" worktree remove --force "$wt" 2>/dev/null || true
git -C "$main" worktree prune 2>/dev/null || true
git -C "$main" branch -D "$branch" 2>/dev/null || true

# `git worktree remove` deregisters and deletes tracked content, but leaves GITIGNORED files
# behind (.next, node_modules, .venv, logs/). Those keep the parent directory alive, and every
# git call above is `|| true`, so a partial teardown used to report success. That matters
# because worktree_setup.sh skips creating the parent worktree when the directory already
# exists — a stale dir silently yields a half-built worktree.
if [[ -d "$wt" ]]; then
    rm -r "$wt"
fi

if [[ -d "$wt" ]]; then
    echo "worktree teardown INCOMPLETE: ${wt} still exists" >&2
    exit 1
fi

echo "worktree removed: ${name}" >&2
