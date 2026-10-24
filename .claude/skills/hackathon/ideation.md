# Hackathon ideation — what I like, what I drop, and why

Read before pitching. Append to it whenever I react to a pitch; the dated entries are the record
of my taste, and a dropped idea stays dropped unless I bring it back.

## Principles

- **Ask Reevo and workflows are complementary — never one consolidated agent builder.** Ask Reevo
  excels at random, unstructured asks. Workflows excel at consistency, accuracy, reliability and
  cheapness. An idea that merges them into one medium has them contradicting each other.
- **No full agents inside workflows** — that defeats the point of a workflow. Agentic *nodes* and
  more AI nodes (AI Data Transform-style) are fine.
- **No customer-facing agent building** — too much complexity for a customer.
- **AI does the config; the app shows the outcome.** Like using a tool where AI does everything
  and you never dig into settings. Users shouldn't have to open a workflow to get value.
- **Cutting edge means agent + internal workflows.** The direction Anthropic is pushing: agents
  that spin up subagents and run internal workflows, nobody editing how the agent triggers them.
  Pure-agent systems are expensive and uncustomizable; repeated patterns belong in workflows.
- **Moving away from manual work.** An idea that makes manual CRM work faster is the wrong
  direction.
- **Sheets is the one workspace capability Reevo doesn't cover**, which is why customers keep
  Sheets beside the CRM. Moving them off it is a real goal — a Sheets integration or a
  sheet-triggers-workflow node is not (it's already a roadmap item).

## 2026-10-23 — first session

**Liked (in the database):** Workflows system view (4; absorbed "one instruction edits every
workflow"), Workflow time machine (4), Agentic AI in workflows (4; absorbed "workflow hands an
exception record off to Ask Reevo"), Ask Reevo mini workflows (5; absorbed "compile" — save a
repeated ask's flow definition to the DB with a way to retrieve it), Self-healing workflows (3;
agent debugs a failed workflow, one approve/deny Slack message fixes and re-launches it), Workflow
replay & rewind (3), AI-native spreadsheets (3), Workflow analytics (2; liked but won't pursue).

**Dropped:**

| Idea | Why |
|---|---|
| Workflow-by-example spreadsheet | Missed the point — the Sheets goal is moving customers off Sheets |
| Fork the CRM (branch + merge CRM data) | Speeds up manual work, which we're moving away from |
| Adopt a sheet into the CRM | That's what imports already does |
| Mine rep behavior into workflow suggestions | Already explored in the past; not interesting |
| Goal / intent workflows | That's what the AI workflow builder is meant to be |
| Agent node with skills, loops until done | Roughly what we have; full agents in workflows defeat the purpose |
| Bring any API (agent-built integrations) | The integration platform covers it; a vibe-coded mess |
| Workflows as an MCP server for outside agents | We already have MCP; outside agents running workflows isn't wanted |
| Triggers on meaning (semantic triggers) | Not technically feasible; the AI builder covers natural language |
| Org-wide workflow policies | Restrictive, not innovative |
| Canary publishing | Just rollout control |
| Workflows that ask a human | Roadmap item — it's approval |
| "Why did this happen?" per record | Field history already covers it |
