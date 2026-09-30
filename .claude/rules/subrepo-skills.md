# Sub-repo skills — find them, read the one that fits

## When to Apply
Scoping, planning, or implementing work in `salestech-be` or `frontend-monorepo`. Sessions run
from the mt-devkit root, so Claude Code never auto-loads those repos' own skills.

## Rule
Before designing or building in an area, check whether the repo already has a procedure for it:

```bash
grep -H '^description:' <repo>/.claude/skills/*/SKILL.md   # .agents/skills is a symlink to the same dir
```

Read the matching `SKILL.md` in full and follow it — e.g. `flow-trigger-create` for a new
workflow trigger, `db-migration` for a migration, `flow-verify-trigger` to prove one works.
A plan task that follows one names it (`follows: <repo>/.claude/skills/<name>`), so the
implementer reads it too.

mt-devkit wins where both have a skill for the same job — worktrees, code review, PR
descriptions/workflow, local env and DB, starting services. Assimilation Harness skills are
governed by `assimilation-harness.md`, not this rule.

**Why:** the repos encode tested procedures (surfaces to register, conventions, grounding);
skipping them means re-deriving the surface list and missing steps.

This applies across all sessions working in this workspace.
