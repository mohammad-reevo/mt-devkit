---
name: linear-tickets
description: Create and edit Linear issues via the Linear MCP — single issues or a full parent/sub-issue tree with blocking relations, assignees, cycles, and milestones. Two modes (create / edit) sharing one machinery. Resolves team, active cycle, and project milestones LIVE from Linear (no hardcoded IDs); edits with targeted patches so content added in the UI survives; never advances issue status past Todo. Carries Reevo defaults (Workflow team, cycle/milestone rules). The "plan → Linear" bridge builds on this. Triggers on "create Linear tickets", "add a Linear issue", "edit/update a Linear ticket", "set up Linear issues for X", "/linear-tickets".
---

# Create & Edit Linear Tickets

Operate Linear through its MCP — create issues (single, or a parent/sub-issue tree with
blocking relations) and edit existing ones (fields, relations, cycle, milestone, assignee,
description). One skill, two **modes** that share all the machinery:

- **Create** — new issue(s), optionally a dependency-wired tree under a project.
- **Edit** — update existing issue(s), preserving what's already there.

Guiding principle: **Linear is the source of truth.** Resolve team, active cycle, and
milestones *live* at run time — never hardcode IDs or assume a project's setup.

## 1. Load the Linear tools

The Linear MCP tools are **deferred** — load their schemas before calling, e.g.
`ToolSearch("select:mcp__linear__save_issue,mcp__linear__get_issue,mcp__linear__get_project,mcp__linear__list_cycles,mcp__linear__save_milestone")`
(add `list_teams` / `list_projects` / `save_project` as the task needs). Calling a Linear
tool before its schema is loaded fails.

## 2. Resolve context live

Never assume IDs. Before creating or editing, resolve from Linear:

- **Project → team.** `get_project` returns the project's team(s); use that rather than guessing. (Default team is the user's — **CRM Workflow / `CRMF`** — but confirm from the project, or ask.)
- **Active cycle.** Read the team's current cycle (`list_cycles`, the active one) and assign by its number/id live — don't hardcode a cycle number.
- **Milestones.** `get_project includeMilestones` — milestones differ per project; read them, don't assume a set, and leave the *choice* to the user unless they've named one.

## 3. Create mode

Create issues with `save_issue` (`title` + `team` required). For a **tree**, mind the ordering:

- **Parents before children** — a sub-issue needs its parent to exist (`parentId`).
- **Relations need both endpoints** — `blockedBy` / `blocks` reference issues that must already exist, so **create in dependency order** (roots first, then dependents) and set relations at creation; or create everything, then wire relations in a second pass. Relations are **append-only**.
- Set `project`, `assignee` (`"me"` / id / name / email), `cycle`, and `milestone` per §2 and the Reevo defaults below.
- A project **overview** is the project's description/summary — set it with `save_project`, not on an issue.

## 4. Edit mode

Update existing issues with `save_issue` (`id` + the fields to change).

- **Preserve UI-added content — use `patch`.** For description edits, prefer `patch` (append / replace / insert) over passing a full `description`, so anything the user added in the Linear UI survives. Full-body overwrite only when you explicitly intend to replace it.
- Add relations with `blockedBy` / `blocks` (append-only; use `removeBlockedBy` / `removeBlocks` to detach). Re-parent with `parentId`.
- The same live-resolution rules (§2) apply to cycle / milestone / assignee changes.

## 5. Verify

Create/update responses **don't echo relations**. After wiring a tree, confirm with
`get_issue includeRelations` (spot-check a blocked issue and a sub-issue) so the nesting and
`blockedBy` / `blocks` actually landed.

## Reevo defaults

- **Team:** default to the user's team — **CRM Workflow (`CRMF`)** — but resolve it from the project when one is given.
- **Cycle:** assign to the **current active cycle** when the issue is near-term (finishable this cycle). If it's **long-term** and won't finish within the cycle, leave it **cycle-less** (Backlog). Resolve the active cycle live.
- **Milestone:** read the project's milestones and leave the choice to the user; don't assume a fixed set (they vary per project).
- **Assignee:** use `"me"` when the user asks to assign to themselves; otherwise as directed.

## Guardrails

- **Status boundary — never past Todo.** Creating lands an issue in Backlog; adding it to the active cycle auto-moves it to Todo (fine). **Never manually advance status** to In Progress / In Review / Done / Canceled — Reevo automation owns those transitions.
- **No destructive changes without asking** — don't delete, cancel, or archive issues, or detach relations, unless the user asked.
- **Rely on Linear, not memory** — resolve team / cycle / milestone / project live; don't hardcode IDs or carry stale assumptions between runs.
- **Load tools first** — Linear MCP tools are deferred (`ToolSearch`).
- **Create + edit only** — no reporting/analytics reads beyond resolving IDs and verifying writes.
- **Composable** — the mechanic for any create/edit Linear work; the "plan → Linear" bridge builds on it to materialize an implementation plan as a project + tickets.
