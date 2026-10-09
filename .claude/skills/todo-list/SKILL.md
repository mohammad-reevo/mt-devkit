---
name: todo-list
description: Keep and render the session's todo list — two lists, Completed then Todo, one item per unit of work (a PR, or a set of PRs that land together) with its chores (CI, update-branch, review comments, deploy waits) as sub-bullets, persisted to a file so the answer is a read, not a reconstruction. Never lists /done or its close-out steps. Kept unasked in any session with two or more PRs. Triggers on "todo list", "what's left", "where are we", "remind me what's left", "anything left", "/todo-list".
---

# todo-list — the session's todo list

One list per session, kept in a file and rendered on ask. The shape is fixed so every answer
reads the same.

## The file

`~/.claude/tmp/<slug>/todo.md`, where `<slug>` is the session's worktree name (`worktrees/<slug>`
or `.claude/worktrees/<slug>`); a session with no worktree picks a kebab-case slug for its work.
`/done` removes `~/.claude/tmp/<slug>/` at teardown, so the list ends with the session.

**A project drive keeps no second file.** Its index `~/.claude/spec/<project>-project.md` is the
store; render the list from its rows (`merged` slices are Completed, the rest Todo) and put chores
under each slice's PR.

## When to write it

- **Unasked, from the second PR on.** Once a session has two or more PRs open or planned, create
  the file and keep it current without being asked.
- **Update at every state change:** a PR opens, merges, or goes ready for review; a chore
  appears (CI red, branch stale, threads open) or clears. Do it in the same turn as the change.
- **Answer from the file.** On "what's left", read it — refresh PR states with `gh pr view` —
  rather than re-deriving the list from the conversation or a compaction summary.

## The shape

```markdown
**Completed**
1. <unit of work> — <PR link> merged
   - <PR link> merged            ← one line per PR when the unit has several

**Todo**
1. <unit of work>
   - <PR link> — <state: open / CI red / ready for review / approved>
     - <chore: fix CI (<check>) / update-branch / address N comments / wait for deploy>
```

- **One item per unit of work.** A unit is one PR, or several that land together — a BE PR and
  its FE PR, a migration PR and the code PR stacked on it, the PRs of one split ticket. Each PR
  inside it carries its link and state.
- **Chores are sub-bullets of the PR they act on** — fixing CI, update-branch, addressing review
  comments, waiting on a deploy, a post-deploy check. Never their own top-level item.
- **Completed first, then Todo, as two lists.** Never interleave done and open items. A unit moves
  to Completed only when every PR in it is merged and nothing remains for it. An empty list says
  "none".
- **Never list `/done` or what it does** — worktree teardown, scratch or throwaway-DB cleanup,
  knowledge-base writes, draining a `tasks/` chore. It runs at the end of every session, so it is
  implied; listing it makes a finished list look unfinished.
