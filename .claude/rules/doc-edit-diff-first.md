# Show a diff before applying an edit to an existing doc

## When to Apply
Before writing a **real edit to a document that already exists** — a PRD, an eng design, a Notion
page, a spec, a knowledge-base entry, a README. Any prose document with a prior author, including
a past version of you.

Not code. A code change is reviewed as a git diff in a PR; this rule is for documents, where the
edit lands with no diff and no review step in between.

## The Rule

**Present the change first, as a fenced `diff` block. Apply only what was agreed.**

````
```diff
- The sync runs every 15 minutes and retries twice on failure.
+ The sync runs every 5 minutes. Failures surface in the Sync Errors panel
+ rather than retrying silently.
```
````

- **`-` is the author's original line, `+` is the replacement.** Use the fenced `diff` language
  tag — it renders red/green in the Claude Code UI. HTML colour and underline do not render;
  don't reach for them.
- **Section by section for a large doc.** One 400-line diff is not review, it's a wall. Show the
  sections that change, in document order.
- **Work from the author's original as the base.** These are surgical edits, not a clean-slate
  rewrite that happens to preserve the meaning. **Unchanged prose stays byte-for-byte** — if a
  line isn't part of the change, it must not appear in the diff at all.
- **No change is a valid outcome.** If the doc already says the thing correctly, say so instead
  of producing an edit to justify the request.

## Why

Silently rewriting a doc buries the real change among incidental rewording, and it reframes prose
that nobody asked to have reframed — the exact failure the avoid-polishing rule exists to prevent
(see `python-service-style.md`). The cost lands hardest on a doc someone else owns: a PM opens
their PRD and can't tell what actually moved.

The deeper reason is that **a document edit leaves no trace to review afterwards.** Code has a PR;
a Notion page or a gitignored knowledge-base entry has nothing. If the change isn't seen before it
lands, it is never seen at all. So the review has to happen at write time, or not at all.

## Enforcement

For `knowledge-base/` there is a backstop: `kb_write_gate_hook.py` (PreToolUse on **Bash**) raises
a confirmation on a shell command that both names a `knowledge-base` path and carries a write
operator, and the `kb` skill owns the diff-and-approve flow.

Note what that backstop is not. Recognising every possible shell write is undecidable, so the hook
matches the shapes the skill actually uses plus the obvious hand-rolled ones; an exotic write can
slip past. It is a backstop, not a wall — and everywhere outside `knowledge-base/` there is no
hook at all. This rule is the thing standing between a doc and a silent rewrite. Follow it
without being asked.

This applies across all repositories and projects.
