#!/usr/bin/env bash
# worktree_teardown.sh — remove a worktree and its local feature branches.
#
# Usage: worktree_teardown.sh <name> <main-repo-abs-path>
#
# Removes the sub-repo worktrees + the parent worktree, and deletes the local feature
# branches — both `mohammad/<name>` and whatever each tree actually had checked out.
# REMOTE branches are NEVER touched — they back open PRs and GitHub deletes them on merge.
# Run from OUTSIDE the target worktree (all git ops use -C).
set -euo pipefail

name="${1:?Usage: worktree_teardown.sh <name> <main-repo-path>}"
main="${2:?main repo path required}"
wt="${main}/worktrees/${name}"
branch="mohammad/${name}"

# Delete a LOCAL branch, never a remote. Restricted to the `mohammad/` namespace so a tree
# left sitting on `main`, or on a teammate's branch, can never be deleted out from under the
# primary checkout. Empty input — a detached review tree — is a no-op.
delete_local_branch() {
    local repo="$1" br="$2"
    [[ -n "$br" && "$br" == mohammad/* ]] || return 0
    git -C "$repo" branch -D "$br" 2>/dev/null || true
}

# Sub-repo worktrees + local branches
for subrepo in salestech-be frontend-monorepo reevo-realtime; do
    src="${main}/${subrepo}"
    dst="${wt}/${subrepo}"
    [[ -d "$src" ]] || continue
    # Read what is ACTUALLY checked out, before the worktree goes away and the path with it.
    # A sub-repo does not always sit on `mohammad/<name>`: a session that splits its work
    # into two PRs switches one sub-repo to a differently-named branch, and that branch is
    # just as much this session's to clean up. Deleting only the name-derived one strands it
    # in the primary checkout, where nothing later has any reason to look for it.
    checked_out="$(git -C "$dst" branch --show-current 2>/dev/null || true)"
    git -C "$src" worktree remove --force "$dst" 2>/dev/null || true
    git -C "$src" worktree prune 2>/dev/null || true
    delete_local_branch "$src" "$branch"
    delete_local_branch "$src" "$checked_out"
done

# Parent-workspace worktree + local branches
parent_checked_out="$(git -C "$wt" branch --show-current 2>/dev/null || true)"
git -C "$main" worktree remove --force "$wt" 2>/dev/null || true
git -C "$main" worktree prune 2>/dev/null || true
delete_local_branch "$main" "$branch"
delete_local_branch "$main" "$parent_checked_out"

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
