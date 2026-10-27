---
name: handoff-session
description: Write a session's working state into one self-contained handoff file so nothing is lost — the question, what was found (file:line / links / data), what was agreed, what's built or decided, the rules I set (verbatim), the environment and its restart recipe, what's open or blocked on me, and the ordered next steps. By default it's a living handoff for a session that carries on, refreshed in place, so the session survives `/compact` — a SessionStart hook points the compacted session back at it. `defer` mode instead parks the session so a fresh one can pick it up later cold; `list` shows handoffs and parked sessions, `resume <fuzzy>` reads one back in and picks up at its next step. Not a tooling chore (that's `claude-task`) and not durable knowledge (that's `author-knowledge-base`). Triggers on "write a handoff", "handoff this session", "save state before compacting", "checkpoint this session", "defer this session", "park this", "save this session for later", "resume the <x> session", "/handoff-session".
---

# handoff-session — hand a session's working state on, to itself or to a new session

A session holds context no file does: what was researched, what the user pushed back on, the
rules they set, what got agreed, where it stopped. Compaction summarises most of that away;
closing the session throws all of it away. This skill writes it down so the reader — the same
session after `/compact`, or a new session with zero context — continues as if nothing happened.

Not `claude-task` (a harness chore to do later) and not `author-knowledge-base` (durable facts
for every future session). A handoff is **one conversation's working state**.

## Router

- **`handoff`** (default — "write a handoff", "checkpoint this", "save state before compacting")
  → **§ Handoff**. The session carries on.
- **`defer`** ("park this", "save this session for later") → **§ Defer**. The session ends.
- **`list`** → **§ List**.
- **`resume <fuzzy>`** ("pick up the skills-in-workflows session") → **§ Resume**.

## Store

- `~/.claude/tmp/handoffs/<slug>.md` — living handoffs, plus a pointer per session at
  `~/.claude/tmp/handoffs/.sessions/<session id>` holding the handoff's path.
- `~/.claude/tmp/deferred/<slug>.md` — parked sessions.

`~/.claude/tmp/` exists in every session and subagent and needs no permission prompt
(`scratch-files.md`). Both get their own directory because `/done` deletes
`~/.claude/tmp/<idea-slug>/` on teardown, and a handoff must outlive whatever worktree it was
written in.

---

## The handoff file

Shared by both modes.

### 1. Name it
A short kebab-case slug from the topic (`skills-in-workflows`), not the session or the branch. If
`<slug>.md` already exists it's the same topic again: **update it in place** and bump the date,
rather than making `-2`.

### 2. Rebuild from the conversation — don't re-research
Everything goes in from what the session already established. No new subagents, queries, or
reads just to fill the file. A fact the session never checked goes under **Caveats** as
unverified; it doesn't get looked up now.

### 3. Write it — fixed sections, in this order

```markdown
# <Handoff | Deferred session> — <topic>

- **<Handoff: <date time> — living, refreshed in place | Deferred: <date>>** (session started <date>)
- **Mode:** <brainstorm / investigation / build — and anything the user said about it, e.g. "nothing to implement">
- **Resume by:** reading this file, then picking up at §10.
- **Style:** <preferences the user expressed this session, e.g. "short turns">

## 1. The original question        — the ask, in the user's framing, incl. their starting hypothesis
## 2. Findings                     — what was verified: file:line, PR/thread links, data + method
## 3. Conclusions reached          — what was agreed, and the reasoning that got there
## 4. <The subject's inventory>    — use cases / options / components — whatever the session iterated over
## 5. Status                       — decided / built / confirmed vs dropped (with the user's reason)
## 6. User-set rules               — verbatim, each with when it was set; they still bind
## 7. Environment                  — ports, ids, branches, running processes, the restart recipe for anything that dies
## 8. Blocked on the user          — what waits on them, or "nothing"
## 9. Open questions               — numbered, not yet discussed or decided
## 10. Next steps                  — ordered; what the reader does first
## 11. Caveats / unverified        — judgment calls, sampling limits, anything not checked
```

Rules that make it resumable:

- **Self-contained.** No "as discussed above" and no "the earlier table". Restate it. The reader
  has none of this context.
- **Keep the evidence.** File paths with line numbers, PR and Slack links, query method and
  counts. A conclusion without its evidence gets re-derived, which is the waste this skill
  exists to prevent.
- **Record reversals.** If the user dropped or overrode something, say what and why, so the
  reader doesn't propose it again.
- **Findings and conclusions stay separate.** §2 is what was true, §3 is what was decided.
- **Rules are verbatim.** "Only touch [Testing Party] prospects in Outreach" — a paraphrase is
  how a rule gets broken after compaction.
- **Point, don't copy.** If the session keeps a todo list (`todo-list`), name its file.
- **Optional sections:** §4 when the session had no natural inventory; §7 when nothing runs.

---

## § Handoff

For a session that **keeps running** — before `/compact`, or whenever I ask.

1. **Write or refresh** `~/.claude/tmp/handoffs/<slug>.md` per **The handoff file**.
2. **Register the pointer** so the compacted session finds it. Read the id with
   `echo $CLAUDE_CODE_SESSION_ID`, then write the literal (`bash-literal-paths.md`):
   `mkdir -p ~/.claude/tmp/handoffs/.sessions && echo <handoff path> > ~/.claude/tmp/handoffs/.sessions/<id>`.
   Compaction keeps the session id, so `compact_handoff_hook.py` (SessionStart, matcher
   `compact`) finds the pointer and tells the compacted session to read the handoff first.
3. **Report** the path in one line, and that `/compact` is safe now.

Refresh it — same file, same pointer — whenever the state moves enough that the last version
would mislead. When the session ends, delete the file and its pointer, or convert it with
§ Defer if the topic is being parked.

## § Defer

For a session that **ends** and gets picked up cold by a new one.

1. Write `~/.claude/tmp/deferred/<slug>.md` per **The handoff file**. A living handoff for the
   same topic is moved here rather than rewritten, and its pointer deleted.
2. **Report** the path, the one-line resume command (`/handoff-session resume <slug>`), and a
   two-line summary of where it stopped. Don't paste the file back.

---

## § List

`ls -t ~/.claude/tmp/handoffs/*.md ~/.claude/tmp/deferred/*.md`. Two lists — **Living handoffs**
and **Parked** — each file with its slug, its date line, and the first §10 next step. None → say so.

## § Resume

1. Fuzzy-match `<fuzzy>` against both stores. Ambiguous → run List and ask.
2. Read the whole file.
3. **Check what may have gone stale.** For each PR, ticket, or branch named in §2/§5, spend one
   cheap check on its current state (`gh pr view <n> --json state`). Report only what changed.
   Don't re-verify the findings wholesale.
4. Adopt the file's **Style** line and its **User-set rules**, then open with a short recap:
   where it stopped, and the first §10 step as a question or proposal. Then continue normally.
5. The file stays. When the topic is finished, or the user parks it again, **update or delete
   it**. A stale handoff that reads as current is worse than none.
