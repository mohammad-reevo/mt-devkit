#!/usr/bin/env bash
# worktree_setup.sh — sync the primary checkouts to fresh main, create a worktree of the
# parent workspace + its sub-repos on a logical feature branch, copy env/settings, fix the
# frontend→backend path for THIS worktree, and install backend deps.
#
# Usage: worktree_setup.sh <name> <main-repo-abs-path>
#        worktree_setup.sh <name> <main-repo-abs-path> --review <subrepo> <ref>
#
# Personal rebuild of devkit's worktree_setup.sh — self-contained. Self-contained:
# no devkit hooks. Idempotent-ish: skips sub-repos/env files that already exist.
#
# Secrets: env files are copied and path-fixed ON DISK. The one path key is rewritten with a
# line-scoped in-place sed; the file's contents (API keys, etc.) are never read into context.
#
# --review builds a READ-ONLY review tree instead of a feature tree: the parent worktree plus
# ONE sub-repo checked out DETACHED at <ref> (someone else's PR head), with no env copy and no
# `uv sync`. Three deliberate differences from a feature worktree:
#   * One sub-repo, not three — a review reads one repo; the other two would be dead weight.
#   * No env / no deps — nothing is executed in a review tree, so a 3.6G `.venv` buys nothing.
#     This is the whole point: a review tree is ~380M instead of ~4-5G.
#   * DETACHED, never a local branch — `done` resolves each sub-repo's checked-out branch and
#     gates the open PR for it. On a named branch tracking the author's ref that resolves
#     THEIR PR, so tearing down my own review tree would block on their CI and their unresolved
#     threads. Detached makes `git branch --show-current` empty, so no PR resolves and the gate
#     is a no-op. Do not "improve" this into a named branch.
# The parent worktree is still a real worktree on `mohammad/<name>` (EnterWorktree needs one),
# and teardown is unchanged — worktree_teardown.sh already skips absent sub-repos.
set -euo pipefail

name="${1:?Usage: worktree_setup.sh <name> <main-repo-path> [--review <subrepo> <ref>]}"
main="${2:?main repo path required}"
wt="${main}/worktrees/${name}"
branch="mohammad/${name}"

review_subrepo=""
review_ref=""
if [[ "${3:-}" == "--review" ]]; then
    review_subrepo="${4:?--review requires <subrepo>}"
    review_ref="${5:?--review requires <ref>}"
fi

# --- 0. Sync every primary checkout to fresh main -------------------------------------------
# Two problems, one fix. The worktrees below branch off `origin/main`, so that ref has to be
# current or every new branch starts behind. And the primary checkouts are never developed in,
# so nothing else ever advances their local `main` — which `branch_from_main_guard_hook` reads
# to decide whether a branch may be created at all. Fetch, then fast-forward `main` where safe.
#
# Best-effort by design: this script runs under `set -e`, and an unreachable origin (offline,
# VPN down) must degrade to "slightly stale base", never "no worktree at all".
sync_primary() {
    local repo="$1" label="$2"
    [[ -d "${repo}/.git" ]] || return 0

    git -C "$repo" fetch origin --prune --quiet || {
        echo "  ${label}: fetch failed — continuing with last-known origin/main" >&2
        return 0
    }

    # Fast-forwarding is only safe on a clean checkout that is actually on main; a primary that
    # is mid-something keeps the fresh origin/main (which is what the branch base needs anyway).
    local cur
    cur="$(git -C "$repo" branch --show-current 2>/dev/null || true)"
    if [[ "$cur" != "main" ]]; then
        echo "  ${label}: fetched; skipped fast-forward (on '${cur:-detached HEAD}')" >&2
        return 0
    fi
    if ! git -C "$repo" diff --quiet || ! git -C "$repo" diff --cached --quiet; then
        echo "  ${label}: fetched; skipped fast-forward (uncommitted changes)" >&2
        return 0
    fi

    local behind
    behind="$(git -C "$repo" rev-list --count main..origin/main 2>/dev/null || echo 0)"
    if [[ "$behind" == "0" ]]; then
        echo "  ${label}: up to date" >&2
    elif git -C "$repo" merge --ff-only --quiet origin/main; then
        echo "  ${label}: main fast-forwarded +${behind}" >&2
    else
        echo "  ${label}: fast-forward failed — left as-is" >&2
    fi
}

echo "syncing primary checkouts to fresh main:" >&2
sync_primary "$main" "$(basename "$main")"
for subrepo in salestech-be frontend-monorepo reevo-realtime; do
    sync_primary "${main}/${subrepo}" "$subrepo"
done

# --- 1. Parent-workspace worktree (container: holds the sub-repo worktrees) -----------------
# A directory that exists but is NOT a registered worktree is a stale leftover from a partial
# teardown. The `[[ ! -d ]]` guard below would silently skip creating the parent worktree,
# yielding a half-built worktree (no parent branch, sub-repos layered onto nothing) that looks
# fine until something is missing — so fail loudly instead.
if [[ -d "$wt" ]] && ! git -C "$main" worktree list --porcelain | grep -qxF "worktree ${wt}"; then
    echo "error: ${wt} exists but is not a registered worktree — stale leftover from a failed teardown." >&2
    echo "       Remove it and retry:  rm -r \"${wt}\"" >&2
    exit 1
fi

if [[ ! -d "$wt" ]]; then
    git -C "$main" branch -D "$branch" 2>/dev/null || true   # clear a stale branch from a failed teardown
    git -C "$main" worktree add -b "$branch" "$wt" origin/main >&2
fi

# Point REEVO_BACKEND_PATH in a frontend env file at this worktree's own backend.
# Line-scoped: only that key is touched; no secret line is read, printed, or altered. The
# grep is a pattern test, so nothing from the file reaches stdout either way. BSD sed (macOS).
#
# Rewrite OR append: a bare `sed s/^KEY=.*/.../` silently no-ops when the key is absent, which
# leaves the worktree's frontend with no backend path at all — it then resolves against whatever
# default applies (in practice the main checkout), and the only symptom is `run-fe-2`'s token-gen
# hitting the wrong backend so :3000 never comes up. Appending when the key is missing makes this
# hold regardless of what the copied env happened to contain.
fix_backend_path() {
    local f="$1"
    [[ -f "$f" ]] || return 0
    if grep -q '^REEVO_BACKEND_PATH=' "$f"; then
        sed -i '' -E "s#^REEVO_BACKEND_PATH=.*#REEVO_BACKEND_PATH=${wt}/salestech-be#" "$f"
    else
        # Guard the newline: appending to a file whose last line lacks one would otherwise
        # concatenate onto it and corrupt both keys.
        [[ -s "$f" && -n "$(tail -c 1 "$f")" ]] && printf '\n' >> "$f"
        printf 'REEVO_BACKEND_PATH=%s/salestech-be\n' "${wt}" >> "$f"
    fi
}

# --- 2. Sub-repo worktrees + env + fix + deps ----------------------------------------------
# Review mode narrows this to the single repo being reviewed; everything else is unchanged.
subrepos=(salestech-be frontend-monorepo reevo-realtime)
if [[ -n "$review_subrepo" ]]; then
    subrepos=("$review_subrepo")
fi

for subrepo in "${subrepos[@]}"; do
    src="${main}/${subrepo}"
    dst="${wt}/${subrepo}"
    [[ -d "$src" ]] || continue
    [[ -d "$dst" ]] && continue

    if [[ -n "$review_ref" ]]; then
        # Detached at the author's head — see the --review note at the top for why this must
        # not become a local branch. No env copy, no deps: nothing runs in a review tree.
        git -C "$src" worktree add --detach "$dst" "$review_ref" >&2
        continue
    fi

    git -C "$src" branch -D "$branch" 2>/dev/null || true
    git -C "$src" worktree add -b "$branch" "$dst" origin/main >&2

    # Copy env files verbatim (secrets stay on disk).
    for envfile in .env .env.local .env.test; do
        [[ -f "${src}/${envfile}" ]] && cp "${src}/${envfile}" "${dst}/${envfile}"
    done

    if [[ "$subrepo" == "frontend-monorepo" ]]; then
        # frontend-monorepo's real env lives under apps/reevo-webapp/, not the repo root.
        nested_src="${src}/apps/reevo-webapp"
        nested_dst="${dst}/apps/reevo-webapp"
        for envfile in .env .env.local .env.test; do
            if [[ -f "${nested_src}/${envfile}" && ! -f "${nested_dst}/${envfile}" ]]; then
                mkdir -p "$nested_dst"
                cp "${nested_src}/${envfile}" "${nested_dst}/${envfile}"
            fi
        done
        # THE FIX: point this worktree's frontend at this worktree's backend (root + nested).
        for envfile in .env .env.local; do
            fix_backend_path "${dst}/${envfile}"
            fix_backend_path "${nested_dst}/${envfile}"
        done
    fi
done

# --- 3. Local Claude tool config + scaffold + backend deps ----------------------------------
settings_src="${main}/.claude/settings.local.json"
if [[ -f "$settings_src" ]]; then
    mkdir -p "${wt}/.claude"
    cp "$settings_src" "${wt}/.claude/settings.local.json"
fi

mkdir -p "${wt}/tmp"

# Knowledge base: ONE store, symlinked in rather than copied.
#
# CLAUDE.md imports @knowledge-base/INDEX.md, and the store is gitignored, so a
# fresh worktree has no such file -- a missing import target in every worktree,
# which is every funnel session. A copy would be worse than the break: the store
# would fork per worktree, and whichever half got written to would win by accident.
# So link, and let the primary checkout hold the only copy.
mkdir -p "${main}/knowledge-base"
if [[ ! -e "${wt}/knowledge-base" ]]; then
    ln -s "${main}/knowledge-base" "${wt}/knowledge-base"
fi

be_wt="${wt}/salestech-be"
if [[ -z "$review_ref" && -f "${be_wt}/pyproject.toml" ]]; then
    (cd "$be_wt" && uv sync --quiet)
fi

if [[ -n "$review_ref" ]]; then
    echo "review worktree ready: ${wt} (${review_subrepo} detached at ${review_ref})" >&2
else
    echo "worktree setup complete: ${wt}" >&2
fi
