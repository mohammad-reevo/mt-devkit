---
name: plan-split
description: Split a planning conversation into N parallel Claude Code sessions, each in its own git worktree with a self-contained brief. Use at the end of a planning conversation when the work cleanly decomposes into independent parts (typically one PR per part).
allowed-tools: Read, Write, Bash, AskUserQuestion
---

# Plan Split

Turn a planning conversation into N parallel Claude Code sessions, each running in its own git worktree with a focused brief and no awareness of the other parts' internals. Coordination happens through merged code, not through cross-session communication.

## When to Use

The user invokes this at the end of a planning conversation, typically after producing a handoff doc that describes the overall change and how it splits. Each part should be roughly one PR.

If the conversation hasn't produced a structured handoff doc yet, the planning session itself should help draft one before this skill runs.

## Inputs you need

Either parse from a handoff doc the user points you at, or reconstruct from the planning conversation:

- **`plan_summary`** — 1-3 sentences on the overall change.
- **`shared_context`** — anything every part-session needs: conventions, file locations, design decisions, the interface contracts between parts. Anything that would otherwise duplicate across every brief.
- **`parts`** — list of parts. Each has:
  - `name` — filesystem-safe identifier (alphanumeric + `_` + `-`). Used for worktree dir and session display name. e.g. `be-auth`, `fe-toast-fix`.
  - `branch` — git branch name for the worktree.
  - `base` *(optional, default `main`)* — branch to fork from.
  - `brief` — self-contained description of what this part does, what files it touches, what success looks like. Must be readable by a fresh Claude with zero memory of the planning conversation.

There is no `depends_on` in v1. All parts run in parallel and coordinate through interface contracts captured in `shared_context` and per-part briefs.

## Steps

### 1. Read or reconstruct the split

If the user pointed at a handoff doc path, read it and structure into the schema above. Otherwise pull it from the planning conversation.

### 2. Propose, don't commit

Show the user the proposed split before creating anything:
- Number of parts and the shared-context length (rough sanity check).
- For each part: `name`, `branch`, one-line summary of the brief.

Then ask the user to confirm. Use `AskUserQuestion` if confirmation isn't clearly forthcoming from their next message.

**Brief quality check first.** Every brief must stand alone — if it says "as discussed," "see the diagram above," or references the planning conversation, fix it before proposing. A brief that can't survive a fresh session is broken.

### 3. Write the manifest

After confirmation, write a JSON manifest to `/tmp/plan-split-<unix-ts>.json`:

```json
{
  "plan_summary": "...",
  "shared_context": "...",
  "parts": [
    {"name": "be-auth", "branch": "feat/be-auth", "base": "main", "brief": "..."}
  ]
}
```

### 4. Run the script

```
bash ~/.claude/skills/plan-split/split.sh /tmp/plan-split-<unix-ts>.json
```

For each part the script:
- Creates `worktrees/<name>` on a new branch via `git worktree add`.
- If the repo has `.claude/skills/worktree/worktree_setup.sh` (devkit), runs it to copy env files, set up sub-repo worktrees, and install Python deps.
- Writes `<worktree>/.claude/brief.md`.
- Prints a copy-paste launch command per part.

Failure modes (the script handles them):
- Not in a git repo → fails loudly.
- Worktree dir already exists → fails loudly; user resolves manually.
- Branch already exists → `git` surfaces the error; user resolves manually.

### 5. Hand off

Print the script's launch commands verbatim. The user opens N new VSCode terminals (Ctrl+Shift+`) and pastes each.

Do **not** try to auto-spawn terminals — there's no reliable cross-terminal way to do this from inside an existing Claude session, and copy-paste is faster than fighting it.

## Anti-patterns

- **Don't add `depends_on` logic.** If two parts truly need ordering, they probably should have been one part. v1 keeps this simple on purpose.
- **Don't try to coordinate between sessions.** The whole point is that each session is autonomous after launch. Resist building back-channels.
- **Don't put devkit-specific paths in this skill.** The setup script is detected at runtime via `.claude/skills/worktree/worktree_setup.sh` in the repo root.
