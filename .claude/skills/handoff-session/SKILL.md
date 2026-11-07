---
name: handoff-session
description: Write a session's working state into the knowledge base as one rich, disposable handoff — `knowledge-base/projects/<project>/handoff.md` — so nothing is lost if the session, its worktree, or `~/.claude/tmp` goes away. It retains a LOT — the question, every id / link / query / verified fact with its source, decisions with their reasons, mid-session corrections, file:line touchpoints, the rules I set (verbatim), the environment and its restart recipe, loose ends, what's blocked on me, and the ordered next steps — and folds in the session's scratch files. By default it's a living handoff for a session that carries on, refreshed in place, so the session survives `/compact` — a SessionStart hook points the compacted session back at it. `defer` mode instead parks it so a fresh session can pick it up later cold; `list` shows handoffs, `resume <fuzzy>` reads one back in and picks up at its next step. Not a tooling chore (that's `claude-task`). Triggers on "write a handoff", "handoff this session", "save state before compacting", "checkpoint this session", "defer this session", "park this", "save this session for later", "resume the <x> session", "/handoff-session".
---

# handoff-session — hand a session's working state on, to itself or to a new session

A session holds context no file does: what was researched, what the user pushed back on, the
rules they set, what got agreed, where it stopped. Compaction summarises most of that away;
closing the session throws all of it away. This skill writes it down so the reader — the same
session after `/compact`, or a new session with zero context — continues as if nothing happened.

Not `claude-task` (a harness chore to do later). It is a `knowledge-base/projects/` entry, but an
unusual one: **one conversation's working state**, deliberately exhaustive and disposable, sitting
next to the project's curated entries rather than replacing them.

## Router

- **`handoff`** (default — "write a handoff", "checkpoint this", "save state before compacting")
  → **§ Handoff**. The session carries on.
- **`defer`** ("park this", "save this session for later") → **§ Defer**. The session ends.
- **`list`** → **§ List**.
- **`resume <fuzzy>`** ("pick up the skills-in-workflows session") → **§ Resume**.

## Store

- `knowledge-base/projects/<project>/handoff.md` — the handoff, living or parked; its
  frontmatter `status:` says which.
- `~/.claude/tmp/handoffs/.sessions/<session id>` — a pointer holding the handoff's path, so the
  compacted session finds it.

**The unit is the project.** `<project>` is the `projects/` entry the session's work belongs to
(re-read `knowledge-base/INDEX.md` from disk to find it). A session that belongs to no project —
a one-PR fix, a standalone investigation — becomes its own small project: `projects/<slug>/`
with just the handoff in it. One handoff per project; a second session on the same project
updates it in place.

The knowledge base, not `~/.claude/tmp/`, because a handoff exists so work can resume cold:
scratch can be lost, and it sits outside where project context is actually looked for.

### Writing it

`knowledge-base/` is the store `author-knowledge-base` owns, so its write rules hold:

- **Through Bash, never `Edit`/`Write`**, with the `MT_KB_WRITE=1` marker — the store is
  symlinked to the primary checkout and the guards refuse a tool write. `projects/` writes skip
  the yes: write first, then show what was written.
  ```
  MT_KB_WRITE=1 cat > knowledge-base/projects/<project>/handoff.md <<'KB_EOF'
  <the handoff>
  KB_EOF
  ```
- **A single-file project becomes a folder first:** `projects/<project>.md` →
  `projects/<project>/overview.md` (a plain `mv` with the marker — the store is gitignored),
  fixing its index line's link.
- **Index line:** add one under `## Projects` in `INDEX.md` for a new handoff —
  `- [<Project> handoff](projects/<project>/handoff.md) — disposable session dump to resume
  from: <the ids, error strings, and terms a resuming session will have on screen>`. Refresh it
  when the handoff's subject moves.
- **The one-page cap does not apply.** A handoff is marked disposable and exempt; thin is its
  failure mode, not length.

---

## The handoff file

Shared by both modes.

### 1. Rebuild from the conversation — don't re-research
Everything goes in from what the session already established. No new subagents, queries, or
reads just to fill the file. A fact the session never checked goes under **Caveats** as
unverified; it doesn't get looked up now.

**Fold in the session's scratch files.** Anything the session wrote under `~/.claude/tmp/<slug>/`
(implementation notes, query outputs, drafts) goes into the handoff — its content, not a path to
it. Nothing in the handoff may depend on tmp surviving.

### 2. Retain a lot
The handoff's job is to make re-deriving unnecessary, so the bar is "would the reader have to go
find this again?" — if yes, it goes in. In particular:

- **Every identifier:** record ids, org / user ids, PR / ticket / Slack-thread links, flow ids,
  branch names, trace ids.
- **Every verified fact with its source:** the doc URL, `file:line`, or query that proved it, and
  for a number, the query behind it.
- **Every decision with its reason**, and **every reversal** — what was dropped or overridden,
  by whom, and why, so the reader doesn't propose it again.
- **Corrections made mid-session** — "X turned out to be Y, not Z".
- **Code touchpoints** as `file:line` with what each does.
- **Loose ends**, and for each open claim, how to confirm it.

Organise the body by topic, in whatever shape the session's material takes — an unstructured dump
that keeps everything beats a tidy summary that drops it. Restate rather than refer: no "as
discussed above", no "the earlier table". Keep findings (what was true) apart from conclusions
(what was decided).

### 3. Required frame
Around that body, these always appear:

```markdown
---
name: <project>-handoff
title: Session handoff (<start date> → <date>) — <topic>, disposable
kind: project
area: <area>
status: living | deferred
updated: <date>
---

# Handoff — <topic> (disposable)

- **Status:** living, refreshed in place | deferred <date> — picked up cold by a new session
- **Mode:** <brainstorm / investigation / build — and anything the user said about it>
- **Resume by:** reading this file (and `overview.md` if the project has one), then picking up at Next steps.
- **Style:** <preferences the user expressed this session, e.g. "short turns">
- Delete this once the work it hands off is finished or dropped.

<the body — by topic>

## User-set rules        — verbatim, each with when it was set; they still bind
## Environment           — ports, ids, branches, running processes, the restart recipe (omit if nothing runs)
## Blocked on the user   — what waits on them, or "nothing"
## Next steps            — ordered; what the reader does first
## Caveats / unverified  — judgment calls, sampling limits, anything not checked
```

- **Rules are verbatim.** "Only touch [Testing Party] prospects in Outreach" — a paraphrase is
  how a rule gets broken after compaction.
- **Point, don't copy, for live files.** If the session keeps a todo list (`todo-list`), name its
  file; the project's `overview.md` / `progress.md` are named, not restated.

---

## § Handoff

For a session that **keeps running** — before `/compact`, or whenever I ask.

1. **Write or refresh** `knowledge-base/projects/<project>/handoff.md` per **The handoff file**
   (`status: living`), through § Store's write path.
2. **Register the pointer** so the compacted session finds it. The path is the **primary
   checkout's** (`git worktree list | head -1` gives its root) — a worktree's `knowledge-base/` is
   a symlink that dies with the worktree. Read the id with `echo $CLAUDE_CODE_SESSION_ID`, then
   write both as literals (`bash-literal-paths.md`):
   `mkdir -p ~/.claude/tmp/handoffs/.sessions && echo <primary>/knowledge-base/projects/<project>/handoff.md > ~/.claude/tmp/handoffs/.sessions/<id>`.
   Compaction keeps the session id, so `compact_handoff_hook.py` (SessionStart, matcher
   `compact`) finds the pointer and tells the compacted session to read the handoff first.
3. **Report** the path, the index line, and that `/compact` is safe now.

Refresh it — same file, same pointer — whenever the state moves enough that the last version
would mislead. `/done` deletes the pointer at close-out; the handoff stays in the project.

## § Defer

For a session that **ends** and gets picked up cold by a new one.

1. Write or refresh the handoff per **The handoff file**, with `status: deferred` and the
   deferred date on its Status line. Delete this session's pointer if it has one.
2. **Report** the path, the one-line resume command (`/handoff-session resume <project>`), and a
   two-line summary of where it stopped. Don't paste the file back.

---

## § List

`ls -t knowledge-base/projects/*/handoff.md`, plus anything left in `~/.claude/tmp/deferred/`
from before handoffs moved into the knowledge base. Two lists — **Living** and **Deferred** (by
`status:`; the legacy files are deferred) — each with its project, its `updated:` date, and the
first Next step. None → say so.

## § Resume

1. Fuzzy-match `<fuzzy>` against the handoffs (and the legacy `~/.claude/tmp/deferred/`).
   Ambiguous → run List and ask.
2. Read the whole file, and the project's `overview.md` if there is one.
3. **Check what may have gone stale.** For each PR, ticket, or branch the handoff names as
   in flight, spend one cheap check on its current state (`gh pr view <n> --json state`). Report
   only what changed. Don't re-verify the findings wholesale.
4. Adopt the file's **Style** line and its **User-set rules**, then open with a short recap:
   where it stopped, and the first Next step as a question or proposal. Then continue normally —
   a session that keeps running sets `status: living` and registers its pointer (§ Handoff
   step 2).
5. The file stays. When the work is finished, or the user parks it again, **update or delete
   it** (and its index line). A stale handoff that reads as current is worse than none. A legacy
   `~/.claude/tmp/deferred/` file that gets resumed moves into the knowledge base on its first
   refresh.
