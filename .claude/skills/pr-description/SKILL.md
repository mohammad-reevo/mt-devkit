---
name: pr-description
description: Write a PR description for any Reevo sub-repo — or for mt-devkit itself — from an mt-devkit session. Routes to the target repo's own pr-description skill + pull_request_template.md (read live, never forked), layers my house rules on top, and runs that repo's deterministic validator before the PR is opened so a format miss costs seconds instead of a ~25-minute CI cycle. Use whenever a PR is created or its body edited — inside /verify or from a bare `gh pr create`. Triggers on "write the PR description", "open the PR", "update the PR body", "/pr-description".
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
| `mt-devkit` | `pull_request_template.md` at the repo root (2 `## ` sections) — no skill | ❌ none |

`.agents/skills/` is the canonical path in both repos; `.claude/skills/` mirrors it.

## Step 2 — read that repo's convention, then write

**Read** the repo's `SKILL.md` and `pull_request_template.md` from disk and follow them.
They are not auto-loaded in a funnel session (the session's project dir is the mt-devkit
workspace root), so read-and-follow is the normal path, not a fallback.

Use the template as the literal skeleton — its headers, its order, nothing renamed.

**`mt-devkit` has no sub-repo skill to read** — the root template is the whole convention.
Two required sections, and optional ones *only when they carry weight*: optional means usually
absent, and a template that invites filler is the failure to avoid. A harness PR is the least
self-explanatory kind — a hook's diff does not say what it now blocks — so `## Summary` carries
that, not a changelog. Nothing here deploys, so the backend's `## Post-deployment Verification`
and `## Verification Metrics` have no meaning and are deliberately absent.

**Read Overrides below before following the sub-repo skill.** A handful of its instructions
are wrong; those rules win over anything the sub-repo says.

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

## Overrides — where my rule beats the sub-repo's

Step 2 says to read the sub-repo's skill and follow it. These are the points where I don't.
On any conflict between a rule here and the sub-repo skill, **the rule here wins**.

**Each override is written as a standing rule, not as a rebuttal.** That is deliberate: a
rebuttal ("ignore the sentence that says X") dies the moment upstream edits the sentence,
leaving a dangling reference and no behaviour. A standing rule keeps working whatever
upstream does — if upstream comes to agree, the rule is merely redundant, never dangling.
So: state the behaviour I want, in the imperative, self-contained. Never phrase an override
as a pointer to upstream text.

The `supersedes:` line is **context, not the rule.** It is allowed to go stale and its
staleness is harmless. If it no longer matches what upstream says, that changes nothing
about whether the rule applies — do not treat upstream agreeing as a reason to re-derive
the opposite, and do not delete a rule because its `supersedes:` line no longer resolves.

Adding one: put it here if it changes **what I do** in the face of a sub-repo instruction.
A caveat about a *tool's output* rather than an instruction belongs in Known traps below.

### Never claim `N/A` in `## Verification Metrics` on a runtime-relevant diff

If the diff touches anything executable — any `.py` outside `tests/`, a migration,
`pyproject.toml` / `uv.lock`, `scripts/`, a Makefile, a Dockerfile — the section must carry
real `metric:` / `dashboard:` / `monitor:` checkbox lines. `N/A` is for a diff that deploys
no behaviour at all (docs-only, tests-only, repo-metadata-only).

If the work to find a metric turns up nothing, that is a signal to look harder at the
Temporal-workflow and route fallbacks, not a licence to write `N/A`.

> supersedes: `salestech-be` `.agents/skills/pr-description/SKILL.md` claims "the bot's
> parser treats absence of `- [ ]` checkbox lines as a no-op, so `N/A` lines are trivially
> ignored." The deterministic validator actively rejects a runtime-diff `N/A`, so following
> that sentence gets the PR denied — it was one of the three `salestech-be` PR #33134
> failures.

## What the preflight cannot catch

CI's validator is an LLM (`deepseek-v4-flash` via Fireworks) running **after** the
deterministic step, and the deterministic step is all that runs locally. It judges
subjective quality only — is the Summary impact-first, are the metrics proportional to the
runtime surface that changed, is the verification authentic. **No local check will ever
catch those.** Write the body properly; the preflight only guarantees you never lose a CI
cycle to *format*.

## Known traps — upstream output that misleads

Not overrides: these change nothing about what I write, only about how I read a tool's
output. Same durability rule applies — describe the behaviour to expect, so the entry stays
readable even after upstream fixes it.

### The validator's error message lies about casing

On any failure the validator lists the required headers rendered through Python's
`.title()`, printing `## Post-Deployment Verification` — while the template and the CI
prompt both say `## Post-deployment Verification`. Header matching is `.lower()`-normalized,
so **casing is never actually checked**. Do not "fix" casing in response to that message;
read the specific failure line instead, which names the real problem.

This cost a CI cycle on `salestech-be` PR #33134. It is an upstream cosmetic bug, not a
contract.
