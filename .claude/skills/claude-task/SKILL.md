---
name: claude-task
description: Manage deferred tooling tasks in `tasks/` — "revisit later" chores against my own harness (personal `~/.claude/` or the mt-devkit repo). Not Linear (product work), not memory (facts). Three subcommands — `claude-task defer` captures a task, `claude-task list` shows all tasks, `claude-task open <fuzzy>` reads one out from zero context, checks it's still true, and proposes a plan it waits for my go on. Draining a finished task belongs to `/done`. Triggers on "claude task", "defer this", "note this for later", "list claude tasks", "open a claude task", "explain that task", "/claude-task".
---

# claude-task — capture, list, and open deferred tooling chores

Manage **tooling tasks** for later: fixes or improvements to my own harness —
personal `~/.claude/` config, or the mt-devkit repo. These are NOT product work
(that's Linear) and NOT facts (that's memory). They live as markdown files in
`tasks/`, one file per task, indexed by `TASKS.md`.

## Router — pick the subcommand

Dispatch on how the skill was invoked:

- **`defer`** (`claude-task defer`, "defer this", "note this for later") → go to
  **§ Defer**. Captures a new task.
- **`list`** (`claude-task list`, "list claude tasks") → go to **§ List**.
  Display-only; shows all tasks and stops.
- **`open <fuzzy>`** (`claude-task open <name>`, "explain the edit-guard one",
  "what's that task about") → go to **§ Open**. Reads one task out and
  plans it; the build is a normal conversation from there.
- **No/ambiguous subcommand** → if the intent reads as capture-a-new-thing, use
  Defer; if it reads as work-on-an-existing-thing, use Open; otherwise run
  List and ask what they want.

`tasks/TASKS.md` is the index, loaded on demand (when working with
tasks), not every session.

The store is **gitignored** — this skill is tracked and reviewable, the notes are
personal working state and are not — and it is symlinked into every worktree back
to the primary checkout, so there is one list rather than one per worktree.

**Write to it through Bash, never `Edit`/`Write`.** The symlink points at the primary
checkout, and the worktree gate resolves it and refuses the resolved path — so from a
worktree, which is where most sessions run, the Write tool fails with "Edit the worktree
copy of this file instead of the shared-checkout path". Creating the symlink does not
help; resolving it *is* the refusal. Same constraint `author-knowledge-base` has, and the
same escape: a Bash heredoc. Unlike `author-knowledge-base` there is no write gate on `tasks/`
and so **no marker to add** — its `MT_KB_WRITE=1` matches on `knowledge-base` only and means
nothing here.

---

## § Defer — capture a deferred chore

Creation only. Never lists, tracks status, or closes.

### 1. Source the task
- **From conversation** — usually something we just hit (a misbehaving hook, a
  skill gap, a rough edge). Infer it from recent context.
- **From a description** — the user hands you the task text directly.

If genuinely unclear (what's broken, or what the fix should be), ask 1–2 tight
questions. Don't manufacture questions when it's clear.

### 2. Derive the slug
Short kebab-case slug (e.g. "the 40-line edit cap starves subagents" →
`edit-guard-40line-cap`). This is the filename: `tasks/<slug>.md`.

**Dedup check first:** `ls tasks/` and scan slugs/titles. If a task
already covers this, update that file instead of creating a duplicate — say so.

### 3. Determine the target
- `personal-claude` — the fix touches `~/.claude/` (hooks, rules, skills, config).
- `mt-devkit` — the fix touches the mt-devkit repo (`.claude/` — skills, rules,
  hooks, agents, references — plus `spec/` and root files).

Infer from where the fix lands. If ambiguous, ask.

### 4. Write the task file
`tasks/<slug>.md` — via a Bash heredoc, per the write-path note above:

```
cat > tasks/<slug>.md <<'TASK_EOF'
<the file, as below>
TASK_EOF
```

```markdown
---
name: <slug>
title: <one-line, human-readable — what becomes true when this is done>
target: mt-devkit | personal-claude
created: <today's date, YYYY-MM-DD>
source: <where observed — PR #, session, ticket — optional>
---

## Problem
What's wrong / what's missing.

## Why it matters
Impact — why it's worth doing.

## Fix ideas
- Options, if more than one. It's fine to leave the choice open — Open will
  surface these and recommend one.

## Links
- [[other-slug]] for related tasks, memory names, PRs.
```

Required frontmatter: `name`, `title`, `target`, `created`. `source` optional.
Body is freeform — Problem / Why / Fix ideas / Links is a good default skeleton,
not enforced. Preserve concrete detail (file paths, symbols, denial messages) —
that's what makes the task actionable later.

### 5. Add the index line
Append to `tasks/TASKS.md` — Bash again, for the same reason:

```
cat >> tasks/TASKS.md <<'IDX_EOF'
- [<slug>](<slug>.md) — <target> — <short hook from the title>
IDX_EOF
```

### 6. Confirm
Tell the user the file path and one line on what was captured. Done.

---

## § List — show all deferred tasks

Read `tasks/TASKS.md`, show the tasks (slug — target — hook), and
**stop**. Display-only: do not select or execute anything.

---

## § Open — read a task out, and decide what to do about it

Put one task in front of me with enough context to decide. You do **not** own the
work that follows: once we agree what to do, it proceeds as ordinary work under
the ordinary rules — a worktree and a PR for the harness, a direct edit for
`~/.claude/`. This section ends at a plan I've approved.

### 1. Select the task
- **A task name given** (e.g. `claude-task open worktree`, "explain the edit-guard
  one") → **fuzzy-match** the argument against task slugs and titles in
  `tasks/`:
  - Exactly one clear match → use it.
  - Multiple plausible matches → show just those and ask which.
  - No match → say so, show the full list, and ask.
- **No name given** → read `TASKS.md`, show the list, and ask which one.

Read the selected `tasks/<slug>.md` in full.

### 2. Check the note is still true
A deferred note is a claim about the past, and the harness moved on without it.
Before explaining anything, verify: is the problem still live, or has it been
fixed since? Do the files, skills and line numbers it cites still exist? Say what
rotted — a dead link or a stale premise is part of the answer, not a footnote.

### 3. Brief me from zero context, briefly
**Assume I have not read the note.** Deferring it is what put it out of my head,
often months ago — so this is a standalone brief, not a delta against a file only
you can see. Never hand back the note's own internal labels or section names
(`contributor 1`, "§ Run the trio"); I can't see what they refer to. Translate them
into the thing itself.

What the task is, whether it still holds, and what you'd do about it —
recommendation first. Open choices in the note ("Fix ideas" with several options)
get surfaced as a choice with your pick named, not a menu.

**Budget it: ~10 lines.** The failure mode here is length, not missing detail — a
long read-out that I have to ask you to shorten costs more than it carried.

### 4. Propose a plan, then wait
Close with a short plan: the concrete changes you'd make, one line each, named by the
file they land in. Then **stop.** Nothing is edited until I say go.

This is the one approval beat Open owns, and it exists because I ask for it every
time. Past my go it is ordinary work under the ordinary rules — a worktree and a PR
for the harness, a direct edit for `~/.claude/` — which need no second ceremony.

---

## Guardrails
- **Tooling scope only.** Product/eng work → Linear, not this. A fact to remember
  → memory, not this. Redirect and don't file it here.
- **Defer is creation only.** No status field, no `done/`. Finishing a task =
  deleting its file — which **`/done` does at close-out**, for the tasks a
  session actually finished. When the work lands with no worktree to tear down
  (a `~/.claude/` fix), delete the file and its `TASKS.md` line yourself once
  it's verified.
- **List is display-only.** Never selects or executes from List.
- **Open reads and plans; it doesn't build.** One task per run. It ends at a plan
  I've approved — the build is a normal conversation afterwards, under the normal
  rules.
- **Preserve detail.** Deferred notes rot when vague. Keep the file paths, symbol
  names, and reproduction context that let a future session act without re-investigating.
