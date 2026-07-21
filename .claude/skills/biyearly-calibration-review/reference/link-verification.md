# Link Verification — resolve every link with tools (Round 2)

Round 2's job is to **actually resolve every link in the draft**, not eyeball it. For each link, confirm
three things: **(1) it resolves**, **(2) it's attributed to the right person** (usually the user), and
**(3) the content supports the claim's wording.** Flag any failure with the exact fix.

## Per-source protocol

### Slack
- Pass the **full message URL as `search_query`** to `conversations_search_messages` → returns the single
  message with the **canonical permalink (incl. `?thread_ts=...`)**, author, and text.
- **Thread replies 404 without the `thread_ts`** — a bare `archives/CHANNEL/pTIMESTAMP` link to a reply is
  broken; the canonical permalink from search includes the `?thread_ts=` that fixes it.
- Confirm: author == the user (or the correct person), and the text supports the claim. Reject generic
  `app.slack.com/client/.../CHANNEL` deep-links — those aren't message permalinks.

### GitHub
- `gh pr view N --repo OWNER/REPO --json author,title,state` → confirm **author == the user** (catches a
  teammate's PR cited as "built by me") AND the title matches the claim's wording AND (if the claim implies
  shipped) `state == MERGED`.
- For a cited review/comment, confirm the `html_url` lands on the user's own comment.

### Notion
- `notion-fetch` the page → confirm it exists and check **Author / Owner / created_by**. Catches PM-authored
  docs and co-authored docs cited as sole authorship. Confirm the doc's substance matches the claim.

### Linear
- URL must be `https://linear.app/reevo/issue/CRMF-XXX` — reject `http://CRMF-XXX` (not a URL). Confirm the
  issue title matches the label used, and (if the claim implies delivery) the issue state.

### External (Datadog / Rootly / Hex / Google Sheets / YouTube / KB)
- These you can't fully resolve with the connected MCPs' read scope. Ask the user to confirm each **opens
  and is shareable** (not a private/expiring link), and that it shows what the claim says.

## What to flag (with the fix, not just the problem)

| Problem | Fix to propose |
|---|---|
| Broken/malformed URL (`http://CRMF-761`) | The canonical URL (`https://linear.app/reevo/issue/CRMF-761`) |
| Wrong attribution (teammate's PR as "built") | Reword to "contributed to / reviewed", or drop |
| Link lands on wrong message (thanks reply, bot) | Deep-link the user's own message (with `?thread_ts=`) |
| Generic Slack deep-link, not a permalink | The canonical permalink from `search_query` |
| Label ≠ linked content | Reword the claim to match, or swap the link |
| Unshipped work implied as delivered | Note the state; soften or drop the delivery claim |

Every flag comes with the **exact replacement** so the user can apply it directly.
