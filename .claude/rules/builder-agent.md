# Builder agent — what it is

## When to Apply
Whenever "builder agent" comes up — its name in a Slack thread, or its comments on a PR.

## What it is

The **Reevo Builder Agent**: a standalone coding agent, not a chat assistant. Given a written
task it investigates from a cold start and carries the work as far as a pull request.

- **In Slack** it is `@builderagent`, mentioned in whatever thread the discussion already lives
  in — it is not confined to `#builder-agent-feedback` or `#ask-builder-agent-anything`.
- **On GitHub** it is `reevo-builder-agent[bot]` (`author:app/reevo-builder-agent` in search).
  It has opened thousands of PRs across `salestech-be` and `frontend-monorepo`, and reviews PRs
  in both. Its approvals carry merge weight through a separate `eng-automation-user` account,
  on human-authored PRs only.
- **Every reply ends with a footer** naming the model, the effort, and a task page at
  `https://reevo-builder-agent.vercel.app/tasks/<id>`. Answers cite `file:line` and the commit
  they were verified against.

Its claims are a model reading code, so they get verified like any other bot's —
`address-comments` tiers it under **AI review bot**.

This applies across all sessions working in this workspace.
