---
name: claude-task
description: Manage deferred tooling tasks in ~/.claude/tasks/ — "revisit later" chores against my own harness (personal `~/.claude/` or the devkit repo). Not Linear (product work), not memory (facts). Three subcommands — `claude-task defer` captures a task, `claude-task list` shows all tasks, `claude-task execute <fuzzy>` drains one (clarify → do → delete). Triggers on "claude task", "defer this", "note this for later", "list claude tasks", "execute claude task", "do a deferred task", "/claude-task".
---

# claude-task — capture, list, and drain deferred tooling chores

Manage **tooling tasks** for later: fixes or improvements to my own harness —
personal `~/.claude/` config, or the devkit repo. These are NOT product work
(that's Linear) and NOT facts (that's memory). They live as markdown files in
`~/.claude/tasks/`, one file per task, indexed by `TASKS.md`.

## Router — pick the subcommand

Dispatch on how the skill was invoked:

- **`defer`** (`claude-task defer`, "defer this", "note this for later") → go to
  **§ Defer**. Captures a new task.
- **`list`** (`claude-task list`, "list claude tasks") → go to **§ List**.
  Display-only; shows all tasks and stops.
- **`execute <fuzzy>`** (`claude-task execute <name>`, "do a deferred task",
  "work on the edit-guard one") → go to **§ Execute**. Drains one task.
- **No/ambiguous subcommand** → if the intent reads as capture-a-new-thing, use
  Defer; if it reads as work-on-an-existing-thing, use Execute; otherwise run
  List and ask what they want.

`~/.claude/tasks/TASKS.md` is the index, loaded on demand (when working with
tasks), not every session.

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
`edit-guard-40line-cap`). This is the filename: `~/.claude/tasks/<slug>.md`.

**Dedup check first:** `ls ~/.claude/tasks/` and scan slugs/titles. If a task
already covers this, update that file instead of creating a duplicate — say so.

### 3. Determine the target
- `personal-claude` — the fix touches `~/.claude/` (hooks, rules, skills, config).
- `devkit` — the fix touches the devkit repo (`.claude/`, `policy/`, root files).

Infer from where the fix lands. If ambiguous, ask.

### 4. Write the task file
`~/.claude/tasks/<slug>.md`:

```markdown
---
name: <slug>
title: <one-line, human-readable — what becomes true when this is done>
target: devkit | personal-claude
created: <today's date, YYYY-MM-DD>
source: <where observed — PR #, session, ticket — optional>
---

## Problem
What's wrong / what's missing.

## Why it matters
Impact — why it's worth doing.

## Fix ideas
- Options, if more than one. It's fine to leave the choice open — Execute will
  surface these and ask which to take.

## Links
- [[other-slug]] for related tasks, memory names, PRs.
```

Required frontmatter: `name`, `title`, `target`, `created`. `source` optional.
Body is freeform — Problem / Why / Fix ideas / Links is a good default skeleton,
not enforced. Preserve concrete detail (file paths, symbols, denial messages) —
that's what makes the task actionable later.

### 5. Add the index line
Append to `~/.claude/tasks/TASKS.md`:

```
- [<slug>](<slug>.md) — <target> — <short hook from the title>
```

### 6. Confirm
Tell the user the file path and one line on what was captured. Done.

---

## § List — show all deferred tasks

Read `~/.claude/tasks/TASKS.md`, show the tasks (slug — target — hook), and
**stop**. Display-only: do not select or execute anything.

---

## § Execute — drain one task

Read a task, get the input the note left open, do the work, delete the task.
One task per run.

### 1. Select the task
- **A task name given** (e.g. `claude-task execute worktree`, "do the edit-guard
  one") → **fuzzy-match** the argument against task slugs and titles in
  `~/.claude/tasks/`:
  - Exactly one clear match → use it.
  - Multiple plausible matches → show just those and ask which.
  - No match → say so, show the full list, and ask.
- **No name given** → read `TASKS.md`, show the list, and ask which one.

Read the selected `~/.claude/tasks/<slug>.md` in full.

### 2. Clarify the open choices (before any edits)
Deferred notes usually leave decisions open — a "Fix ideas" list with several
options, an unresolved scope question. Surface those and get the user's input:
- Which approach to take (present the options, recommend one).
- Any scope constraints or things to leave out.

Do this **before** touching code. If the note is fully specified and
unambiguous, say so and skip straight to execution.

### 3. Route by target
Read the `target` frontmatter field:

- **`personal-claude`** → the fix touches `~/.claude/` (hooks, rules, skills,
  config). Edit there directly — `~/.claude/` is exempt from the worktree gate.
- **`devkit`** → the fix touches the devkit repo. Devkit edits hit the
  always-worktree Edit/Write gate, so work in a **devkit worktree**
  (`EnterWorktree` or `git worktree add`), then normal branch → implement →
  verify → push → PR flow. Don't edit the primary devkit checkout.

### 4. Do the task
Execute the confirmed approach. Follow the note's detail (file paths, symbols,
context) and the relevant project rules. Verify the change works — for devkit
harness code that means exercising the hook/skill, not just editing it.

### 5. Delete the task
Once the work is done (and, for devkit, pushed as a ready PR):
- Delete `~/.claude/tasks/<slug>.md`.
- Remove its line from `~/.claude/tasks/TASKS.md`.

Then report what was done — and for devkit, the PR link.

---

## Guardrails
- **Tooling scope only.** Product/eng work → Linear, not this. A fact to remember
  → memory, not this. Redirect and don't file it here.
- **Defer is creation only.** No status field, no `done/`. Finishing a task =
  deleting its file (done by Execute).
- **List is display-only.** Never selects or executes from List.
- **Execute: one task per run, clarify before editing, delete only after the work
  lands.** For personal-claude that's after the edit is verified; for devkit
  after the PR is up. Never edit the primary devkit checkout — respect the gate.
- **Preserve detail.** Deferred notes rot when vague. Keep the file paths, symbol
  names, and reproduction context that let a future session act without re-investigating.
