---
name: todo-list
description: Keep and render the session's todo list — two lists, Completed then Todo, one item per unit of work (a PR, or a set of PRs that land together) with its chores (CI, update-branch, review comments, deploy waits) as sub-bullets, persisted to a file so the answer is a read, not a reconstruction; every ask (a bare /todo-list included) re-checks each PR's state, CI, branch and threads live before rendering; when a decision only I can make blocks a PR, the render leads with it and explains it plainly. Never lists /done or its close-out steps. Kept unasked in any session with two or more PRs. Triggers on "todo list", "what's left", "where are we", "remind me what's left", "anything left", "/todo-list".
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
- **A decision only I can make is a chore too**, under the PR it blocks:
  `- decision: <question> — recommended: <option>`. Its sources: an open gate question, a review
  finding that contradicts the plan, a `Pending:` plan line. GitHub can't show it, so the re-check
  never clears it — it goes when I answer.
- **Answer from the file.** On "what's left", read it — then re-check it, below — rather than
  re-deriving the list from the conversation or a compaction summary.

## On ask — re-check, then render

A bare `/todo-list` (no arguments), or any "what's left" ask, means: re-check every status
live, write the result back to the file, then render the two lists. The file says *which* PRs
and chores exist; it is never trusted for their *current state* — neither is the conversation.

For every PR in the list, in one pass:

```bash
gh pr view <url> --json state,mergedAt,isDraft,reviewDecision,mergeStateStatus
gh pr checks <url> --json name,bucket,workflow
gh api graphql -f query='query { repository(owner:"<owner>",name:"<repo>") {
  pullRequest(number:<n>) { isInMergeQueue mergeQueueEntry { state position }
    reviewThreads(first:100) { nodes { isResolved } } } } }'
```

Threads: `isResolved` on every one, per `github.md` — never a filtered "unresolved" list.

**CI comes from `gh pr checks`, never `statusCheckRollup`.** The rollup keeps a failed entry from
an older run of a check after a newer run of it passed, so it reports a green PR as red;
`gh pr checks` shows each check's current run. A `fail` bucket is a failing check.

From that, set the PR's state and rebuild its chores: a merged PR drops its chores; a failing
check, `mergeStateStatus` `BEHIND` / `DIRTY`, or an unresolved thread adds one; one that has
cleared goes. **`isInMergeQueue` true** → the state is `in merge queue (position <n>, <state>)`
and the CI and update-branch chores drop, since the queue owns both; unresolved threads still
count. Move a unit to Completed once every PR in it is merged.

No file yet → build it from the session's PRs (`gh pr list --author @me --head <branch>` for
each repo's checked-out branch in the worktree), write it, then render.

## The shape

```markdown
**Completed**
1. <unit of work> — <PR link> merged
   - <PR link> merged            ← one line per PR when the unit has several

**Todo**
1. <unit of work>
   - <PR link> — <state: open / CI red / ready for review / approved / in merge queue (position N, <state>)>
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

## A pending decision

When the file holds a `decision:` chore, the render changes so I never have to ask "what do you
need from me?". No decision → the shape above, unchanged.

1. **Lead line:** "I need one decision from you before <PR> can <next step>."
2. **The two lists**, as above — the decision stays a terse sub-bullet there.
3. **The decision**, in plain terms for someone who has lost the thread: what the feature is,
   what the plan says, what the rule or constraint says and who raised it, what each option
   costs. A few lines, per `discussion-turns.md`.
4. **Recommendation** — one line, with why.
5. **The question**, asked directly.

Several decisions → one numbered block each for 3–5, the lead line counting them.
