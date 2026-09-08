---
name: pr-description
description: Write a PR description for any Reevo sub-repo from an mt-devkit session. Routes to the target repo's own pr-description skill + pull_request_template.md (read live, never forked), layers my house rules on top, and runs that repo's deterministic validator before the PR is opened so a format miss costs seconds instead of a ~25-minute CI cycle. Use whenever a PR is created or its body edited — inside /verify or from a bare `gh pr create`. Triggers on "write the PR description", "open the PR", "update the PR body", "/pr-description".
---

> Personal rebuild — self-contained, no devkit dependency.
> Standalone tool, and the PR-body step of the funnel's **verify** phase.

# pr-description — route, write, preflight

A wrapper, not a rulebook. The **content** rules belong to each sub-repo and are read live;
this skill owns **routing**, my **house rules**, and the **preflight** that stops a format
miss from reaching CI.

## Why a wrapper and not a copy

The obvious move — fork `salestech-be`'s `pr-description` skill into the harness so it can
be tweaked — is the wrong one. Its bulk is repo-specific knowledge: where `@workflow.defn`
and `@activity.defn` live across ~8 scattered directories, Datadog path-tag resolution, the
reverse import-graph lookup for service-layer changes, per-domain `CLAUDE.md` metric
defaults. That moves with the repo, and a stale fork does not fail loudly — it emits
**wrong verification metrics** that pass CI and mislead the post-deploy regression bot.
Silently wrong beats loudly broken only in the wrong direction.

So: read the sub-repo's skill at write time, and put harness-owned behaviour here, where
changing it changes one file.

## Step 1 — identify the target repo

From the branch you are opening a PR for. One PR per repo the change touches.

| Repo | Convention | Deterministic validator |
|---|---|---|
| `salestech-be` | `.agents/skills/pr-description/SKILL.md` + `pull_request_template.md` (5 `## ` sections) | ✅ `scripts/hooks/validate_pr_description.py` |
| `frontend-monorepo` | `.agents/skills/pr-description/SKILL.md` + `pull_request_template.md` (2 `# ` sections) | ❌ none |
| `reevo-realtime` | none — no skill, no template | ❌ none |

`.agents/skills/` is the canonical path in both repos; `.claude/skills/` mirrors it.

## Step 2 — read that repo's convention, then write

**Read** the repo's `SKILL.md` and `pull_request_template.md` from disk and follow them.
They are not auto-loaded in a funnel session (the session's project dir is the mt-devkit
workspace root), so read-and-follow is the normal path, not a fallback.

Use the template as the literal skeleton — its headers, its order, nothing renamed.

## Step 3 — house rules on top

These are mine and apply to every repo:

- **Ready for review, never `--draft`** (`github.md`).
- **Link related PRs; never dictate merge order** (`pr-description-no-merge-order.md`).
  Describe a cross-repo CI dependency as a mechanism, not an instruction.
- **Never fabricate verification.** Only describe what was actually run. If in-app
  verification is still pending, say it is pending and update the body once it passes.
- **Echo the PR URL** after `gh pr create` / `gh pr edit`.
- **Editing an existing PR: fetch the live body first** (`gh pr view <n> --json body -q .body`)
  and edit that text. Never rebuild it from a local draft — that silently wipes screenshots
  and videos I attached in the UI (`github.md`).

## Step 4 — preflight before the PR goes up

For a repo with a validator, run it yourself before `gh pr create`:

```bash
python3 <repo>/scripts/hooks/validate_pr_description.py --help   # body inline or via --body-file
```

It mirrors the mechanical subset of CI's `pr-description-validation` job: every template
`## ` header present and in order, no untouched HTML placeholders, no empty required
section, `## Verification Metrics` machine-parseable (`metric:` / `dashboard:` / `monitor:`
checkboxes) or a justified `N/A`, and no docs-only `N/A` claimed on a runtime diff.

**A hook is the backstop, not the mechanism.**
`.claude/hooks/pr_description_preflight_hook.py` (PreToolUse on Bash) intercepts
`gh pr create` / `gh pr edit`, resolves the target sub-repo, and delegates to that repo's
own `scripts/hooks/extract_pr_description.py`. It exists because the failure it prevents
happened *outside* `/verify`, on a bare `gh pr create` — a skill step is skippable and
skipping it is exactly the bug. It is fail-open: no validator, no resolvable repo, or any
crash allows the call.

## What the preflight cannot catch

CI's validator is an LLM (`deepseek-v4-flash` via Fireworks) running **after** the
deterministic step, and the deterministic step is all that runs locally. It judges
subjective quality only — is the Summary impact-first, are the metrics proportional to the
runtime surface that changed, is the verification authentic. **No local check will ever
catch those.** Write the body properly; the preflight only guarantees you never lose a CI
cycle to *format*.

## Known trap: the validator's error message lies about casing

On any failure the validator lists the required headers rendered through Python's
`.title()`, printing `## Post-Deployment Verification` — while the template and the CI
prompt both say `## Post-deployment Verification`. Header matching is `.lower()`-normalized,
so **casing is never actually checked**. Do not "fix" casing in response to that message;
read the specific failure line instead, which names the real problem.

This cost a CI cycle on `salestech-be` PR #33134. It is an upstream cosmetic bug, not a
contract.
