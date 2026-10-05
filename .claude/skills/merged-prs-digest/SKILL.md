---
name: merged-prs-digest
description: DM me on Slack a list of my PRs that merged across salestech-be and frontend-monorepo — the last 24 hours by default, or an optional date range split into one message per day. One `• <title> - <repo>#<number>` line per PR, the `<repo>#<number>` a clickable link. Reads GitHub with `gh`, skips any PR I already linked in #team-crm-workflow-reviews (checked with a paginated search, never a capped history read), and posts to my own Slack DM only. Triggers on "merged PRs digest", "DM me my merged PRs", "what did I merge today", "what did I merge this week", "/merged-prs-digest".
---

# merged-prs-digest — DM me what merged

> Personal harness skill, self-contained. Standalone.

My own DM is the only destination. This is not the "never message people" boundary in
`github.md` — nobody else receives anything.

## 0. Pick the mode

- **No argument → last 24 hours.** One rolling window, one message.
- **A date range → one message per day.** Anything that names days counts: "past 7 days",
  "9/28–10/02", "since Monday", "yesterday". Resolve it to inclusive **local** calendar days
  `<START>`..`<END>` (`YYYY-MM-DD`, the machine's timezone); "past N days" is the last N days
  including today. Say the resolved range back in the report.

## 1. Find the PRs

Separate commands, values pasted in literally — a worktree-isolated session refuses a `gh` call
with an inline `$(...)`.

**Last 24 hours:**

```bash
date -u -v-24H +%Y-%m-%dT%H:%M:%SZ
gh search prs --author=@me --merged --merged-at=">=<cutoff>" \
  --repo ReevoAI/salestech-be --repo ReevoAI/frontend-monorepo \
  --json title,url,number,repository,closedAt --limit 200 \
  --jq 'sort_by(.closedAt)[] | "• \(.title | gsub("&";"&amp;") | gsub("<";"&lt;") | gsub(">";"&gt;")) - <\(.url)|\(.repository.name)#\(.number)>"'
```

**Date range:** GitHub's `--merged-at` dates are UTC, so search one day wider on each side
(`<START − 1 day>`..`<END + 1 day>`) and let `jq` keep only the local days you want and group
them. `strflocaltime` converts to local time; grouping on `%Y-%m-%d` keeps the days in date
order.

```bash
gh search prs --author=@me --merged --merged-at="<START-1>..<END+1>" \
  --repo ReevoAI/salestech-be --repo ReevoAI/frontend-monorepo \
  --json title,url,number,repository,closedAt --limit 200 \
  --jq 'map(. + {day: (.closedAt | fromdateiso8601 | strflocaltime("%Y-%m-%d"))})
    | map(select(.day >= "<START>" and .day <= "<END>")) | sort_by(.closedAt) | group_by(.day)[]
    | "## \(.[0].closedAt | fromdateiso8601 | strflocaltime("%a %m/%d"))",
      (.[] | "• \(.title | gsub("&";"&amp;") | gsub("<";"&lt;") | gsub(">";"&gt;")) - <\(.url)|\(.repository.name)#\(.number)>")'
```

"Mine" means PRs I authored — I merge my own, so author and merger are the same person.

## 2. Drop PRs I already announced

Any PR whose `github.com/ReevoAI/<repo>/pull/<number>` appears in a message of mine in
#team-crm-workflow-reviews is already sent — drop it. Compare case-insensitively on repo +
number; a message counts whatever its wording ("Merging …", a review ask, an earlier digest),
and so does a thread reply.

**Read the channel with `mcp__slack__conversations_search_messages`, never
`conversations_history`.** History silently stops at a message cap with no error and no usable
cursor: a 7-day read once came back ~12 hours short of its cutoff, and the 11 announcements in
the missing hours went out as "new". It also omits thread replies.

```
filter_in_channel: C0AQNQR0GV6     # #team-crm-workflow-reviews
filter_users_from: U09CJ1XJLEM     # me
search_query:      github.com
filter_date_after: <earliest merge day − 14 days>   # exclusive; I announce before merging
limit:             100
```

**Page until the last row's `Cursor` is empty**, passing it back as `cursor`. A page that ends
with a cursor is not the whole answer. If you can't get to an empty cursor (the tool errors, a
page fails), **stop and send nothing** — tell me the de-dupe couldn't be completed. Sending an
unchecked list is worse than sending none.

## 3. Draft the message(s)

**Last 24 hours** — one message:

```
PRs merged in the last 24 hours:
• <PR TITLE> - <PR LINK|repo#number>
• ...
```

**Date range** — one message per day that still has PRs after step 2, oldest day first:

```
PRs merged on Fri 10/02:
• <PR TITLE> - <PR LINK|repo#number>
• ...
```

A day left with nothing gets no message.

`<url|text>` is Slack's link syntax: the link shows as a short `salestech-be#36770` label rather
than the full URL. The `gsub`s escape `& < >` in the title, which Slack requires. Title otherwise
verbatim — no rewording.

**Nothing left ⇒ send nothing.** Tell me none merged, or that every one was already in the
channel, and stop.

## 4. Send it to my DM

`mcp__slack__conversations_add_message` with `channel_id: D09CJ1Z7201` (my self-DM; I'm
`U09CJ1XJLEM`), `content_type: text/plain`, and the drafted message as `text` — one call per
message, oldest day first.

**`missing_scope`?** The `xoxp` user token in `~/.claude.json` lacks `chat:write`. Tell me
to add it under User Token Scopes in the Slack app, reinstall, and swap the new token in.

**Tool missing?** `slack-mcp-server` hides it unless `SLACK_MCP_ADD_MESSAGE_TOOL` is set.
Don't work around it (no `curl` with the token). Tell me to add
`"SLACK_MCP_ADD_MESSAGE_TOOL": "D09CJ1Z7201"` to the `slack` server's `env` in
`~/.claude.json` and restart Claude Code. The channel-ID value allows posting only to
that DM.

## 5. Report

Say what was sent — the resolved window, how many messages, how many PRs — and give me the same
list, grouped by day for a range. Name any PRs dropped as already announced.
