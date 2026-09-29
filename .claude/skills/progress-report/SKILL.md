---
name: progress-report
description: Write a concise, lead-facing progress report for a project into a Notion page — what's done, the next demo-able deliverable, and when it lands. Fans out research subagents across Notion (PRD / eng doc / plan), Linear, GitHub PRs, and the code on main; keeps everything in a reusable per-project context store so the next report starts from the last snapshot instead of from scratch; aligns on the actual progress with me before any outline; then outline gate → one-pass draft → I review. Standalone. Triggers on "progress report", "write a status update for <project>", "update the progress report", "/progress-report".
---

# progress-report — a lead-facing progress report

Turn a project's scattered state (Notion docs, Linear, PRs, code) into a short Notion report a
team lead can read in two minutes: **what's done, the next thing you can demo, and when.** Same
rhythm as `create-eng-doc` — research, one approval gate on the outline, a full draft in one
pass, then I drive edits — with one extra step up front: **align on the progress itself** before
any doc structure is discussed. A report built on unaligned numbers gets rewritten.

Keep the main thread lean: research lives in subagents and in the context store; only findings
come back.

## The context store — reuse is the point

`~/.claude/tmp/<project-slug>-progress-report/` (per `scratch-files.md`):

```
README.md               target page, workspace, format examples, how to refresh
context/<source>.md     raw research, one file per source, dated at the top
snapshots/<date>.md     the synthesized state as of that report + decisions from the discussion
outline-<date>.md       the approved outline
```

**On a repeat run, read `README.md` and the newest snapshot first.** The research then refreshes
`context/` and reports the *delta* since that snapshot — what merged, what moved, what dates
changed. The previous snapshot's decisions (dates promised, scope cuts, what isn't a risk) carry
forward unless the new research contradicts them; say so when it does.

Also read the project's `knowledge-base/projects/<project>/` entries if the index has them —
they carry the precedence rules and the progress board. Don't write to the KB from this skill;
KB writes happen at `/done` or on my explicit ask, through `author-knowledge-base`.

## 1. Gather inputs

Infer what you can; ask only for what you can't find:
- **Project** — name, Linear project, Notion workspace page.
- **Target page** — the Notion page to write. Often it already exists (maybe blank) under the
  workspace; find it there before asking.
- **The deadline anchor** — the milestone dates, and what was promised to whom (Slack finds this).

## 2. Research — four parallel subagents

Dispatch in one message, each writing its files into `context/` (an `Explore` agent can't write —
save its returned report yourself). Each returns ≤25 lines.

| Agent | Covers | Writes |
|---|---|---|
| Notion (`general-purpose`) | every page under the workspace; PRD, eng doc, implementation plan (every ticket, deps, dates); the target page's current structure verbatim; 1–2 sibling progress reports/trackers for format | `notion-pages.md`, `prd-summary.md`, `eng-doc-summary.md`, `impl-plan-summary.md`, `progress-report-template.md` |
| Linear + Slack (`general-purpose`) | project metadata, milestones + dates, status updates, cycles; every issue (paginate) with status/assignee/cycle/milestone/blockers/PRs; external blocker tickets; Slack for commitments and dates promised | `linear-project.md`, `linear-issues.md`, `slack-signals.md` |
| GitHub (`general-purpose`) | every related PR in each repo — merged / open (review + CI state) / closed; dependency-team PRs; which base branch they target | `github-prs.md` |
| Code on main (`Explore`) | what actually exists and is **wired** on `origin/main` (fetch; read via `git grep`/`git show`, never check out in a primary); what's missing; the **shortest path to a UI demo**, in dependency order | `code-on-main.md` |

All read-only: no Linear edits, no PR comments, no Notion writes.

Then write `snapshots/<today>.md`: counts by status, merged/open PRs, what exists vs. what's
missing, dependency status, critical path, candidate next deliverables. And `README.md` if new.

## 3. Align on the progress — before any outline

Report the findings briefly, then resolve with me, one point at a time:

- **The next deliverable.** Candidates are the shortest paths to something *visible in the UI*
  that exercises the real thing — not a stand-in (a demo against the native/fake path isn't worth
  showing). If two paths converge on the same ticket, offer them as one deliverable in beats.
- **Its date.** Estimate from the remaining chain, measured against velocity **since full-speed
  work began** (not since the project was created — early calendar time understates pace), and
  against how fast a merge reaches a demo env. Ask me the deploy cadence if unknown. Say what the
  estimate absorbs and what would break it.
- **"Functioning" means it works unattended.** A hand-wired shortcut (seeded data, a manually
  registered webhook) is a fallback to name, not the delivery path to date.
- **Risk framing.** A dependency is a risk only to the milestone it actually gates — a blocker on
  a UAT-only ticket is not a risk to initial testing. State dependencies on other teams neutrally.
- **Code-level surprises.** Check the load-bearing assumption behind the headline date (e.g. can
  the adapter actually make a live call?) before putting the date in writing.

Append every decision to the snapshot as it's made.

## 4. Outline → my approval

Default shape (adapt to the project; the team's trackers are the format reference):

1. **Masthead** — `Updated <date>` · Linear · PRD · eng doc · plan links.
2. **TL;DR** — 3 bullets: progress framed by velocity, the next deliverable + date, milestone status.
3. **Done so far** — grouped **by capability**, not ticket section; ✅ merged · 🟡 in review; one
   closing line on what is/isn't UI-visible yet.
4. **Next deliverable** — each beat: what the demo shows, date, the remaining ticket chain.
5. **Milestones** — table: milestone | date | ✅/🟡/⬜ | scope.
6. **Dependencies** — other teams' pieces: landed vs. pending, and what each gates.

Style: tickets by the project's own numbering (e.g. "4.1"), not tracker ids, for our own tickets;
external dependencies by their ids. No addressing the audience. Save to `outline-<date>.md`;
**wait for a yes.**

## 5. Draft in one pass

Write the whole report into the target page with `notion-update-page`. **Fetch the page first:**
blank → `replace_content`; has content (a previous report, or my edits) → ask whether this run
updates it in place or starts a new dated page, and never overwrite what I wrote. Fetch it back
afterwards to confirm it rendered (tables especially).

## 6. Revisions

Date or scope changes after the draft: patch the page with `update_content` (targeted
search-replace, not a rewrite), append the decision to the snapshot, and mention that the KB
progress entry has drifted if it has — the write itself goes through `author-knowledge-base`.

## Guardrails

- **Align before outlining; outline before drafting.** Two gates, in that order.
- **Every date is an estimate with its basis stated** — the chain, the velocity, the deploy speed.
- **Code is truth over tickets and docs** (`shipped-work-code-is-truth.md`) — a merged ticket's
  capability is confirmed in `code-on-main.md`, not assumed from its status.
- **Never post outward** — no Linear status updates, no Slack. Publishing the report to others
  is mine.
- **Response altitude** when relaying research — lead with the verdict; the detail lives in the store.
