---
name: testing-party-triage
description: Triage a testing party's Linear tickets in one ask — read the party's Slack channel over a date range, collect every issue the Linear bot or harvey filed from it, then gather them under one new "Testing Party" parent on CRM Workflow (CRMF), each moved to Todo, assigned to me, labels cleared, in the project + milestone I name. Project and milestone are the only things it asks for. Uses linear-tickets for the Linear writes. Triggers on "triage the testing party tickets", "gather up the testing party bugs", "/testing-party-triage".
argument-hint: <slack-channel> [<from-date> <to-date>]
---

# testing-party-triage — one parent for a testing party's bugs

After a testing party, the bugs raised in its Slack channel land in Linear via the Linear bot or
harvey — on the REEVO team, some in Triage, with whatever project, assignee and labels the bot
guessed. This skill gathers them under one parent on my board. `create-testing-party-doc` is the
other half of a party (the Notion doc); `linear-tickets` owns every Linear write here, including
its baseline (me, Todo, current cycle) — follow it, don't restate it.

## Inputs

- **Channel** — required.
- **Date range** — optional; default is the channel's whole history (a party channel usually
  holds one party).

## 1. Collect the issues from Slack

Read the channel over the range (`conversations_history`, paginating to the start of the range).
A tracked message carries a `track-with-linear` reaction, and its thread
(`conversations_replies`) holds the Linear bot's reply with the issue URL — harvey replies
"Linear issue created: …" instead. Collect every issue id, deduplicated. Also note the party's
Notion doc link if one was posted in the channel.

A tracked message whose thread has no issue link is not silently dropped — list it in the report
as "tracked, no issue found".

## 2. Ask for project and milestone — the only question

Resolve both live (`linear-tickets` §2): list projects for the choice, then
`get_project includeMilestones` for that project's milestones. Milestone names take forms like
"M2 · UAT / Pilot Org", so offer the real names rather than matching a typed string. Ask in one
message with the issue count and titles, so I can see what's about to move.

## 3. Create the parent

One issue, "Testing Party" (prefix the feature if the channel name gives it, e.g. "Sequences
Integration — Testing Party"), on CRMF with the `linear-tickets` baseline plus the chosen project
and milestone. Description: the channel link and the Notion doc link, if found.

## 4. Move each ticket — two calls, in this order

The Linear MCP's `save_issue` refuses a label change combined with a team change, so:

1. `save_issue(id, labels: [])` — clear every label.
2. `save_issue(id, team: CRMF, state: "Todo", assignee: "me", cycle: <current>, project,
   milestone, parentId: <parent>)`.

The current cycle comes from `list_cycles(teamId, type: current)`, which takes the team's UUID,
not its key. Resolve it once and reuse it.

## 5. Report under the new ids

The team move renames each identifier (REEVO-29824 → CRMF-2957), so every id in the report is
the new one, with the old id beside it once: `CRMF-2957 (was REEVO-29824) — <title>`. Lead with
the parent's link. Then `get_issue includeRelations` on one child to confirm the parent landed
(`linear-tickets` §5). Anything in this session that referenced an old id gets the new one.

## Guardrails

- **Project and milestone are the only questions.** Team, status, assignee and labels are fixed
  above; the cycle is resolved live.
- **Never past Todo, never close or delete** — `linear-tickets`' guardrails apply.
- **Reference run** (2026-10-19, Sequences Integration): parent CRMF-2956;
  REEVO-29824/26/28/29/31/32 → CRMF-2957..2962.
