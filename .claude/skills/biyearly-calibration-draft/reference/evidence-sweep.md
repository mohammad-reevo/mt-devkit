# Evidence Sweep — the concrete tools and queries

The sweep is what makes a calibration honest and complete. The **best evidence often lives outside git** —
the headline E4 signal (delegating work to other engineers) came from **Linear**, not commits; reliability
came from Slack + Datadog; and the honest *gaps* (no incident command) came from Rootly/Sentry. Sweep every
connected source, not just code.

**Pattern:** the orchestrator dispatches **one read-only subagent per source/angle, in parallel**. Each
returns lean *cited* findings — permalinks, PR numbers, issue IDs — never raw dumps. Run **Wave 1** broad,
then **Wave 2** to deepen the thin/high-value bullets and to confirm-or-kill the strongest claims.

Window: **H1 = Jan 1 – Jun 30**, **H2 = Jul 1 – Dec 31**. `git --until` and `gh --created` upper bounds are
exclusive — use the 1st of the next month.

---

## Git & GitHub (`git`, `gh`)

- **Resolve identity FIRST — name ≠ email.**
  `git -C <repo> log --since=START --until=END --pretty='%an <%ae>' | sort | uniq -c`
  → pick the **email**; filter everything on it. A wrong filter silently returns zero.
- **Authored PRs (shipped work):**
  `gh search prs --repo OWNER/REPO --author LOGIN --created "START..END" --json number,title,state,createdAt,url`
- **Review footprint (mentoring + reach):**
  `gh search prs --repo OWNER/REPO --reviewed-by LOGIN --created "START..END" --json number,author`
  → group by author, exclude self. **High counts on a few people = mentees; a long tail = cross-team reach.**
- **Review SUBSTANCE — this is what proves mentoring, not the count:**
  `gh api repos/OWNER/REPO/pulls/N/comments` and `/reviews`, filtered to the user → read the actual comment
  text. Categorize: architecture guidance / real pre-merge bug catch / design pushback vs. nits. Sample a
  handful of the highest-signal ones; "329 reviews" alone means nothing.
- **Flagship PRs by churn:** aggregate add+del per PR from `git log --author=EMAIL --numstat` (exclude
  generated files / lockfiles / baked JSON), then `gh pr view N --json title,body,additions,deletions,author`
  on the top ~20. **Check `author`** — a big PR you reviewed but didn't author is not "built by you."

## Linear — ownership AND delegation (the E4 signal)

- Find the user's team and projects (`list_projects`, `get_project`), and whether they are **project lead**
  (a headline signal — but distinguish project-lead from team-lead/initiative-lead, which roll up to others).
- `list_issues` for issues **assigned + completed** in-window — the personal delivery.
- **THE key query: issues the user AUTHORED and ASSIGNED TO OTHERS.** Directing non-reports = influence-based
  leadership = the clearest level-up signal. Count them; name who they directed and on what track.
- Milestones hit, sub-issue trees under flagship parents — shows scope and sequencing.

## Slack (`conversations_search_messages`, `conversations_replies`)

- Search the user's messages in-window (`filter_users_from`, `filter_in_channel`, date filters). Look for:
  **leadership/decisions, design discussions, mentoring, incident response, roadmap, "why" questions,
  critical feedback on systems/process, rollout announcements.**
- **Permalink verification (KEY trick):** to get a canonical, correct permalink for a specific message,
  pass the **full message URL as `search_query`** → returns the single message with the canonical permalink
  **including `?thread_ts=...`** plus author and text. **Thread replies 404 without the `thread_ts`.** Always
  confirm the resolved author is the user and the text supports the claim.
- **Public channels only for citations** — never cite DMs or private channels; the user can't reference them.

## Notion (`notion-search`, `notion-fetch`)

- `notion-search` with a `created_by` filter is **loose** — it over-returns. Always `notion-fetch` each
  candidate and check the **Author(s) / Owner / created_by** field before citing authorship.
- **The trap:** a flagship "PRD" is often **PM-authored** (Author+Owner = PM). The user's own *scoping doc*
  content inside a PM-created roadmap page is theirs — but the page authorship is the PM's. Cite precisely
  ("drafted the scoping doc," not "authored the PRD").
- Plain pages may lack a hard created-date — infer in-window from edit date + content, and note the caveat.

## Datadog — reliability ownership (and honest absence)

- Search monitors / notebooks / dashboards by owner (`search_datadog_monitors`, etc.) → what the user
  actually owns for their domain's reliability. **Absence is a finding too** — "owns 1 monitor, the rest are
  a teammate's" is the honest picture.

## Rootly & Sentry — usually an honest gap

- **Rootly:** search incidents for the user as started / mitigated / resolved / closed. Often **empty** —
  which means reliability rests on bug-fix turnaround + monitoring, **not** incident command. Say so; don't
  claim incident leadership without a responder record.
- **Sentry:** assigned / resolved issues — frequently empty; note it honestly.

## "Whatever else is connected"

Don't hard-code away the rest. If another MCP is connected (Langfuse, a data warehouse, Hex, Google
Sheets/Docs, etc.), sweep it for relevant authored artifacts. **Degrade gracefully** — a missing or
disconnected source is a note in the dossier, never a hard failure. Load unfamiliar tool schemas via
ToolSearch before calling them.

---

## What each source tends to prove (map to rubric sections)

| Source | Strongest for |
|---|---|
| Git/GitHub authored PRs | Technical craftsmanship, scope, complexity of shipped work |
| GitHub review substance | Collaboration & influence, mentoring depth |
| Linear delegation | Leading-through-others, scope & impact (the level-up spine) |
| Slack | Design leadership, mentoring, "why" questions, critical feedback, rollout |
| Notion authored docs | Product/business judgement, design leadership |
| Datadog / Rootly / Sentry | Reliability ownership — and honest gaps in incident command |
