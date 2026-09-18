# Show a doc diff when I ask for one

## When to Apply
When I ask to see a change **before** it lands — "show me the diff", "what would you change",
"before/after" — on an existing **technical document**: a PRD, an eng design, a Notion page, a
README.

**Only then.** An edit I asked for directly just gets made. Don't volunteer a red/green diff, and
don't reach for this on `spec/` scope/plan files, task files, or code — those are edited in place
(code gets reviewed as a git diff in its PR). The `author-knowledge-base` skill carries its own diff-and-approve
sequence for `knowledge-base/` entries; it doesn't need this rule.

## The Rule

Present the change as a fenced `diff` block, then apply only what was agreed.

````
```diff
- The sync runs every 15 minutes and retries twice on failure.
+ The sync runs every 5 minutes. Failures surface in the Sync Errors panel
+ rather than retrying silently.
```
````

- **`-` is the author's original line, `+` is the replacement.** The fenced `diff` tag renders
  red/green in the Claude Code UI; HTML colour does not.
- **Surgical, not a rewrite.** Work from the author's original as the base — unchanged prose stays
  byte-for-byte and must not appear in the diff at all.
- **Section by section for a large doc**, in document order. One 400-line diff is a wall, not a
  review.
- **No change is a valid outcome.** If the doc already says it correctly, say so.

## Why
A doc edit leaves no trace to review afterwards — code has a PR, a Notion page has nothing. When I
ask to see the change first, that preview is the only review there will ever be, so it has to be
an honest diff of the author's text rather than a rewrite that happens to preserve the meaning.

This applies across all repositories and projects.
