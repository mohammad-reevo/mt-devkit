---
name: scope
description: Funnel head of my personal dev workflow. Brainstorm/discuss a raw development idea — or a Linear ticket — into a converged high-level direction — 2–3 approaches with tradeoffs, light research, open questions, and the testing the work warrants (unit/integration, at altitude). Deliberately NO task breakdown and NO file paths. Decides the idea's name up front (yours if given, else self-generated), and records the name in the scope file. Writes ~/.claude/spec/<name>-scope.md for plan to consume. Use when starting a new idea or kicking off a ticket, before any planning. Triggers on "start this ticket", "kick off <TICKET-ID>", "let's start <TICKET-ID>".
---

> Personal rebuild — self-contained, no devkit dependency.
> Part of the funnel: **scope → plan → implement → verify → babysit → done**
> (see `~/.claude/spec/my-devkit-design.md`).

# scope — brainstorm an idea into a direction

You are running the **divergent** phase. Your job is to help me converge on a *direction*,
not a plan. Stay at altitude the entire time.

## Name & re-entrancy (always first)

**Decide the name.** If I gave you a name, use it. Otherwise generate a short kebab-case name
from the idea (e.g. "rate-limit the sync API" → `sync-rate-limit`). For a Linear ticket, still
derive a short human-readable kebab-case name from the idea — never use the bare ticket id
(e.g. `CRMF-1641` "Expand eval dataset using GTM traces" → `expand-eval-dataset`, not
`crmf-1641`). This name is the **slug for the whole funnel** — it names the
scope/plan files, the worktree, and the branch `mohammad/<name>`, and it's recorded in the
scope file (below) so downstream phases read it rather than re-derive it.

**Re-entrancy.** Check `~/.claude/spec/<name>-scope.md`:
- **Exists** → revision (plan kicked it back, or I changed my mind). Read it, state the
  current direction, ask what changed. Revise from there — don't start over.
- **Doesn't exist** → fresh scope, run the four beats below.

## The four beats

### 1. Frame
Restate the idea in your own words — the problem and the why, not the solution. If the idea
is genuinely ambiguous (unclear goal, unclear user, unclear constraint), ask 1–3 clarifying
questions. If it's clear, skip straight to research — don't manufacture questions.

If I hand you a **Linear ticket** (an identifier like `CRMF-1641`, a URL, or "this ticket"),
that ticket *is* the frame: fetch it with `mcp__linear__get_issue` (accepts the identifier or
URL), read its description, deliverables, comments, and linked docs, then restate it the same
way. A ticket often describes a defect, so the frame is "what's actually wrong and why" — but
that's just the shape of a bug-flavored idea, not a different mode. I may still paste extra
context on top; fold it in. If the ticket's premise turns out to conflict with what beat 2
finds in the code (already fixed, wrong premise, bug is elsewhere), say so plainly.

### 2. Light research (default beat — you judge the depth)
Ground the approaches in reality before proposing them. Read-only, timeboxed — this is
reconnaissance, not investigation.

- **Codebase-touching idea** → dispatch one Explore agent (medium breadth) to answer: what
  already exists in this area, what nearby patterns/conventions apply, what would each
  approach collide with. Keep the findings at "what's relevant" altitude — if the agent
  returns file inventories or line numbers, summarize them away.
- **External-tech idea** (new library, protocol, service) → quick web search for the
  current state of the art and obvious gotchas.
- **Self-contained idea** (pure-harness, pure-process, or I clearly already know the
  terrain) → skip research entirely and say so in one line.

One research pass. If the discussion later reveals a knowledge gap, do one more targeted
pass — don't loop.

### 3. Diverge → converge
Present **2–3 genuinely different approaches** — not one approach and two strawmen. For
each: what it is (2–3 sentences), tradeoffs (effort, risk, blast radius, reversibility).
Recommend one and say why.

Then discuss. This is conversational and may take multiple rounds. I pick the direction —
you advocate, you don't decide.

**Testing call (part of the direction).** Before writing the file, settle — at altitude — what
testing the chosen direction warrants: unit tests for new logic, an integration test for a
flow, or none for a trivial/refactor change. Name the *kinds* and what they'd cover, never test
files or cases (that's plan). This is the **one place test-building is scoped** — plan
turns it into concrete test tasks and implement builds them; verify does post-build
verification only and never decides tests.

### 4. Write the scope file (only after I've agreed on a direction)
The discussion is ephemeral; the file is the converged record — not a transcript. Write
`~/.claude/spec/<slug>-scope.md`:

```markdown
# <Idea title> — Scope

> Name: <name>   (the slug — names the scope/plan files, the worktree, and branch mohammad/<name>)

## Idea
2–4 sentences: the problem and the why.

## Approaches considered
One subsection per approach, including rejected ones.
Each: what it is, tradeoffs. Rejected ones get one line on why rejected.

## Chosen direction
What we're doing, at altitude. The shape of the solution — never tasks, never file paths.

## Testing
What testing the chosen direction warrants, at altitude — the kinds of tests + what they cover,
or "none" + why. plan turns this into concrete test tasks; it doesn't invent test scope.

## Open questions
Things plan must resolve or ask me about.

## Out of scope
What we consciously deferred, so plan doesn't reinvent it.
```

Close by telling me the file path. Return to `/workflow` to continue the funnel — it owns
what comes next.
This filename is the **slug authority** for the rest of the funnel — downstream skills find
the chain by this file, they never re-derive the slug from the idea.

## Guardrails

- **No descending.** If the discussion starts producing task lists, file paths, function
  names, or schemas — stop, say "that's plan territory", and capture the thread as an
  open question instead. This applies to your own output too: catch yourself.
- **Honest tradeoffs.** Every approach gets real costs named. An approach with no listed
  downside means you haven't thought about it enough.
- **No invented requirements.** Scope what I asked about. Gaps you notice become open
  questions, not silently-added scope.
- **One artifact, no state.** No session files, no hooks, no auto-transition into plan
  (Wave 1: I drive).
