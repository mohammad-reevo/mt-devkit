---
name: session-deferral
description: Park the current session so a fresh session can pick it up later with nothing lost — writes one self-contained handoff file (the question, what was found with file:line / links / data, what was agreed, what's built or decided, what's still open, and the ordered next steps) to `~/.claude/tmp/deferred/<slug>.md`. Three subcommands — `defer` (default) writes it, `list` shows parked sessions, `resume <fuzzy>` reads one back in and picks up at its next step. For a paused discussion or investigation, not a tooling chore (that's `claude-task`) and not durable knowledge (that's `author-knowledge-base`). Triggers on "defer this session", "park this", "save this session for later", "write this down so I can pick it up later", "resume the <x> session", "/session-deferral".
---

# session-deferral — park a session, resume it cold

A session holds context no file does: what was researched, what the user pushed back on, what
got agreed, where the discussion stopped. Closing it throws that away. This skill writes it
down so a **new session with zero context** can continue as if it never stopped.

Not `claude-task` (a harness chore to do later) and not `author-knowledge-base` (durable facts
for every future session). A deferral is **one conversation's working state**, read once on
resume and then thrown away.

## Router

- **`defer`** (default, "park this", "save this session") → **§ Defer**.
- **`list`** → **§ List**.
- **`resume <fuzzy>`** ("pick up the skills-in-workflows session") → **§ Resume**.

## Store

`~/.claude/tmp/deferred/<slug>.md` — one file per parked session. `~/.claude/tmp/` exists in
every session and every subagent and needs no permission prompt (`scratch-files.md`). It gets its
own `deferred/` directory because `/done` deletes `~/.claude/tmp/<idea-slug>/` on teardown, and a
parked discussion must outlive whatever worktree it happened in.

---

## § Defer

### 1. Name it
Derive a short kebab-case slug from the topic (`skills-in-workflows`), not the session or the
branch. If `<slug>.md` already exists, it's the same topic parked again: **update it in place**
and bump the date, rather than making `-2`.

### 2. Rebuild from the conversation — don't re-research
Everything goes in from what the session already established. No new subagents, queries, or
reads just to fill the file. A fact the session never checked goes under **Caveats** as
unverified. It doesn't get looked up now.

### 3. Write it — fixed sections, in this order

```markdown
# Deferred session — <topic>

- **Deferred:** <date> (session started <date>)
- **Mode:** <brainstorm / investigation / build — and anything the user said about it, e.g. "nothing to implement">
- **Resume by:** reading this file, then picking up at §7.
- **Style for the resumed session:** <preferences the user expressed this session, e.g. "short turns">

## 1. The original question        — the ask, in the user's framing, incl. their starting hypothesis
## 2. Findings                     — what was verified: file:line, PR/thread links, data + method
## 3. Conclusions reached          — what was agreed, and the reasoning that got there
## 4. <The subject's inventory>    — use cases / options / components — whatever the session iterated over
## 5. Status                       — decided / built / confirmed vs dropped (with the user's reason)
## 6. Open questions               — numbered, not yet discussed or decided
## 7. Next steps to resume         — ordered; what the next session does first
## 8. Caveats / unverified         — judgment calls, sampling limits, anything not checked
```

Rules that make it resumable:

- **Self-contained.** No "as discussed above" and no "the earlier table". Restate it. The reader
  has none of this context.
- **Keep the evidence.** File paths with line numbers, PR and Slack links, query method and
  counts. A conclusion without its evidence gets re-derived, which is the waste this skill
  exists to prevent.
- **Record reversals.** If the user dropped or overrode something, say what and why, so the
  resumed session doesn't propose it again.
- **Findings and conclusions stay separate.** §2 is what was true, §3 is what was decided.
- **Section 4 is optional.** Drop it when the session had no natural inventory.

### 4. Report
Give the path, the one-line resume command (`/session-deferral resume <slug>`), and a two-line
summary of where it stopped. Don't paste the file back.

---

## § List

`ls -t ~/.claude/tmp/deferred/`. For each file show the slug, its `Deferred:` date, and the first
§7 next step. None → say so.

## § Resume

1. Fuzzy-match `<fuzzy>` against `~/.claude/tmp/deferred/*.md`. Ambiguous → run List and ask.
2. Read the whole file.
3. **Check what may have gone stale.** For each PR, ticket, or branch named in §2/§5, spend one
   cheap check on its current state (`gh pr view <n> --json state`). Report only what changed.
   Don't re-verify the findings wholesale.
4. Adopt the file's **Style** line, then open with a short recap: where it stopped, and the first
   §7 step as a question or proposal. Then continue the conversation normally.
5. The file stays. When the topic is finished, or the user parks it again, **update or delete
   it**. A stale deferral that reads as current is worse than none.
