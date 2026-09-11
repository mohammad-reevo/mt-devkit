# Builder agent — a coding agent I send work to

## When to Apply
Whenever "builder agent" comes up: its name in a Slack thread, its comments on a PR, or an ask
to "send this to builder agent" / "write a prompt for builder agent".

## What it is

The **Reevo Builder Agent** — a standalone coding agent, not a chat assistant. Given a written
task it investigates from a cold start and carries the work as far as a pull request. It is a
**destination for work**, the way Linear is a destination for tickets.

- **In Slack** it is `@builderagent`. It gets mentioned in whatever thread the discussion
  already lives in — it is not confined to `#builder-agent-feedback` or
  `#ask-builder-agent-anything`. Inline flags select the model and effort
  (`--model=... --think=...`); Slack-initiated tasks otherwise run on the default.
- **On GitHub** it is `reevo-builder-agent[bot]` (`author:app/reevo-builder-agent` in search).
  It has opened thousands of PRs across `salestech-be` and `frontend-monorepo`, and it reviews
  PRs in both. Its approvals carry merge weight through a separate `eng-automation-user`
  account, on human-authored PRs only.
- **Every reply ends with a footer** naming the model, the effort, and a task page at
  `https://reevo-builder-agent.vercel.app/tasks/<id>`. Answers cite `file:line` and the commit
  they were verified against. A follow-up in the same thread reuses the same task.

## The boundary — you draft the prompt, I send it

A session **writes the prompt and stops**. It never sends one. Reaching builder agent means
@-mentioning it in Slack, and reaching out to anyone in Slack is mine (`github.md`). Hand me
the prompt as text I can paste.

## What a good prompt carries

- **Verified context up front** — the file paths and line numbers you already confirmed, marked
  as verified. Naming the repo is usually redundant once the paths are there.
- **The ask**, stated once, and the **output you want** (a written proposal, a diff, a PR).
- **Whether to write code, explicitly.** "Investigate and give context, don't code yet" versus
  "make the PR" is the line it will otherwise guess, and the two produce very different work.

## Its output is a hypothesis, not a verdict

An answer in a thread or a review comment on a PR is a model reading code. Verify the claim
before it earns an action item — `address-comments` already tiers it that way under **AI review
bot**, and nothing here softens that. It is wrong sometimes and revises under challenge, so
pushing back is a normal move rather than a rude one.

One failure worth recognizing on sight: its sandbox cannot always reach a running backend or a
browser, so a verification step can come back blocked or inconclusive. That is an environment
limit, not evidence about the code.

This applies across all sessions working in this workspace.
