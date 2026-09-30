---
name: merged-prs-digest
description: DM me on Slack a list of my PRs that merged in the last 24 hours across salestech-be and frontend-monorepo — one `- <title>: <link>` line per PR. Reads GitHub with `gh`, posts to my own Slack DM only. Triggers on "merged PRs digest", "DM me my merged PRs", "what did I merge today", "/merged-prs-digest".
---

# merged-prs-digest — DM me what merged

> Personal harness skill, self-contained. Standalone.

My own DM is the only destination. This is not the "never message people" boundary in
`github.md` — nobody else receives anything.

## 1. Find the PRs

Two separate commands — a worktree-isolated session refuses a `gh` call with an inline
`$(...)`. First the cutoff, then the search with it pasted in literally:

```bash
date -u -v-24H +%Y-%m-%dT%H:%M:%SZ
gh search prs --author=@me --merged --merged-at=">=<cutoff>" \
  --repo ReevoAI/salestech-be --repo ReevoAI/frontend-monorepo \
  --json title,url,closedAt --limit 100 \
  --jq 'sort_by(.closedAt)[] | "- \(.title): \(.url)"'
```

"Mine" means PRs I authored — I merge my own, so author and merger are the same person.

## 2. Draft the message

```
PRs merged in the last 24 hours:
- <PR TITLE>: <PR LINK>
- ...
```

Title and URL verbatim from the search — no repo prefix, no rewording.

**None merged ⇒ send nothing.** Tell me there were none and stop.

## 3. Send it to my DM

`mcp__slack__conversations_add_message` with `channel_id: D09CJ1Z7201` (my self-DM; I'm
`U09CJ1XJLEM`), `content_type: text/plain`, and the drafted message as `text`.

**`missing_scope`?** The `xoxp` user token in `~/.claude.json` lacks `chat:write`. Tell me
to add it under User Token Scopes in the Slack app, reinstall, and swap the new token in.

**Tool missing?** `slack-mcp-server` hides it unless `SLACK_MCP_ADD_MESSAGE_TOOL` is set.
Don't work around it (no `curl` with the token). Tell me to add
`"SLACK_MCP_ADD_MESSAGE_TOOL": "D09CJ1Z7201"` to the `slack` server's `env` in
`~/.claude.json` and restart Claude Code. The channel-ID value allows posting only to
that DM.

## 4. Report

Say it was sent and how many PRs, and give me the same list.
