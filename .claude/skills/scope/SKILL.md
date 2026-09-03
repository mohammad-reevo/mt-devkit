---
name: scope
description: Funnel head of my personal dev workflow. Investigate a raw development idea — or a Linear ticket — into a converged high-level direction — the actual cause and its difficulty reported first, then 2–3 approaches whose load-bearing assumptions have been checked, open questions, and the testing the work warrants (unit/integration, at altitude). Deliberately NO task breakdown and NO file-level change plans. Decides the idea's name up front (yours if given, else self-generated), and records the name in the scope file. Writes ~/.claude/spec/<name>-scope.md for plan to consume. Use when starting a new idea or kicking off a ticket, before any planning. Triggers on "start this ticket", "kick off <TICKET-ID>", "let's start <TICKET-ID>".
---

> Personal rebuild — self-contained, no devkit dependency.
> Part of the funnel: **scope → plan → implement → verify → babysit → done**
> (see `~/.claude/spec/my-devkit-design.md`).

# scope — investigate an idea into a direction

You are running the **divergent** phase. Your job is to help me converge on a *direction*,
not a plan. Stay at altitude the entire time.

This phase exists so I can understand three things before any planning starts: **what's
actually going on**, **how hard the resulting PR is**, and **what our real options are**.
Approaches proposed before the first two are understood are guesses, and we end up
reversing them mid-discussion — don't produce them.

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
- **Doesn't exist** → fresh scope, work through the phases below.

## How scope runs

Five phases, in order. They are **your working order, not an output format** — never render
them as section headers, never label a message with a phase name, never refer to them by
number when you talk to me. What I see is an answer; the phases are how you got there. How to
present it is § Reporting, below.

### Frame
Restate the idea in your own words — the problem and the why, not the solution. If the idea
is genuinely ambiguous (unclear goal, unclear user, unclear constraint), ask 1–3 clarifying
questions. If it's clear, go straight to investigating — don't manufacture questions.

**Don't state a cause here.** You haven't read anything yet. Frame the *problem*; investigating
establishes what's actually true.

If I hand you a **Linear ticket** (an identifier like `CRMF-1641`, a URL, or "this ticket"),
that ticket *is* the frame: fetch it with `mcp__linear__get_issue` (accepts the identifier or
URL), read its description, deliverables, comments, and linked docs, then restate it the same
way. I may still paste extra context on top; fold it in. Where a ticket asserts *why*
something is broken, treat that as a **hypothesis to confirm or kill while investigating** —
not as established fact, and not as part of the frame.

### Investigate — cause + difficulty
The real first research pass. Its job is not "what exists in this area" — it's **what is
actually true here**: how does this work today, and where does it actually break.

**Check the knowledge base before dispatching anything.** An entry may already hold what a
research pass is about to re-derive — how a subsystem fits together, why something is shaped the
way it is, what a project's tickets actually cover. Scan the index in your context; if nothing
there fires but the area feels previously-trodden, invoke **`kb`** `search`. This is cheap and it
runs before the expensive part, which is the entire point — re-investigating what the KB already
holds is the cost this store exists to remove.

Read-only. Dispatch Explore agent(s), **scaled to the idea** — one for a single-surface
change, more when it spans repos or both backend and frontend. Keep the grounding they return
(which components are shared, how many consumers, which call sites); that detail is what the
difficulty read is made of. Summarize it away only later, when writing the file.

For an **external-tech idea** (new library, protocol, service), the equivalent is a web
search for current state of the art and the obvious gotchas. For a **self-contained idea**
(pure-harness, pure-process, or I clearly already know the terrain), skip this phase and say
so in one line.

Establish two things, and lead with them when you report:

- **Cause / mechanism.** For a defect: where it actually breaks and why — including why the
  broken thing is the way it is, if that constrains the fix. For a feature: how the area
  works today and what the change has to fit into. Name the code that explains it; naming
  a component or function to explain a mechanism is not descending (see Guardrails).
- **Difficulty read.** How big the resulting PR is, before anyone picks an approach: shared
  vs local, how many consumers or call sites, one repo or two, any migration or data change,
  whether test scaffolding already exists — and what's genuinely still uncertain.

**The cause comes first in the message — but it doesn't have to be the whole message.** If what
you found is uncontroversial, keep going into candidates in the same turn; I'd rather read one
coherent answer than collect it across three.

**Stop and wait only when what you found changes the problem** — the ticket's stated cause
doesn't hold, the thing is already fixed, the bug is somewhere else, or the real work is much
bigger than the framing implied. Then say that plainly and stop, because everything downstream
would be built on a premise I need to correct first. That is the one interruption worth its
cost; a routine "here's the cause, shall I continue?" is not.

### Candidates — validate what's load-bearing
Now generate **2–3 genuinely different** candidates, shaped by the cause — not one approach
and two strawmen.

Then, **before presenting any of them**, run a second targeted pass: for each candidate name
the **single assumption that would make it collapse**, and check it. A targeted read, running
the real parser/evaluator/query, a quick search — whatever settles that one question. This
pass is required; it is the difference between a proposal and a guess.

- **One question per candidate.** This is a check, not another sweep.
- **A killed candidate is a result, not a failure.** It becomes a rejected approach with a
  real reason — which is worth more than a surviving one you never tested.
- **Purpose cap, not a time cap.** Research only what would change a decision. Stop when the
  remaining unknowns wouldn't change which approach I'd pick.

### Discuss — converge
Put the candidates in front of me and recommend one. Each carries what it is, what it costs,
what the validation pass found, and its share of the difficulty read — but as **prose that
argues for or against it**, not as a labelled block with those four fields filled in. Shape it
per § Reporting.

Then discuss. This is conversational and may take multiple rounds. I pick the direction —
you advocate, you don't decide.

**Testing call (part of the direction).** Before writing the file, settle — at altitude — what
testing the chosen direction warrants: unit tests for new logic, an integration test for a
flow, or none for a trivial/refactor change. Name the *kinds* and what they'd cover, never test
files or cases (that's plan). This is the **one place test-building is scoped** — plan
turns it into concrete test tasks and implement builds them; verify does post-build
verification only and never decides tests.

### Write the scope file (only after I've agreed on a direction)
The discussion is ephemeral; the file is the converged record — not a transcript. Write
`~/.claude/spec/<slug>-scope.md`:

```markdown
# <Idea title> — Scope

> Name: <name>   (the slug — names the scope/plan files, the worktree, and branch mohammad/<name>)

## Idea
2–4 sentences: the problem and the why. For a defect, the established cause belongs here —
what actually breaks and why, not the ticket's guess.

## Approaches considered
One subsection per approach, including rejected ones.
Each: what it is, tradeoffs. Rejected ones get one line on why rejected — grounded in what
the validation pass actually found, never a hand-wave.

## Chosen direction
What we're doing, at altitude. The shape of the solution — never tasks, never a file-level
change plan.

## Testing
What testing the chosen direction warrants, at altitude — the kinds of tests + what they cover,
or "none" + why. plan turns this into concrete test tasks; it doesn't invent test scope.

## Open questions
Genuine unknowns that still need my input — each written as a direct, answerable question (not
"figure out X"), ideally with your recommendation. Resolve what you can yourself first (a
targeted read/research pass); only what you genuinely can't settle lands here.

## Out of scope
What we consciously deferred, so plan doesn't reinvent it.
```

**Where the difficulty read goes.** Into the file as *justification* — folded into an
approach's tradeoffs or the chosen direction ("~82 executors plus a standing obligation on
every node added later"). **Never as a standalone estimate section** and never as a numeric
guess at size or duration: it comes from a reconnaissance pass, so plan would inherit an
approximation as authority. You give me the full read live while investigating; the file keeps
only the parts that explain a decision.

Close by telling me the file path. Return to `/workflow` to continue the funnel — it owns
what comes next.
This filename is the **slug authority** for the rest of the funnel — downstream skills find
the chain by this file, they never re-derive the slug from the idea.

## Reporting — how this reaches me

Everything above is about doing the work. This is about showing it, and it's the half that
usually goes wrong: the investigation is fine and the message is a form I have to interrogate.

**`response-altitude.md` governs the shape** — read it as binding here. Note it's a different
axis from the "stay at altitude" rule everywhere else in this skill: that one is about how deep
to *think* (no task lists, no file-level plans); this one is about how much to *show*. Getting
the first right doesn't get you the second.

What that means concretely for a scope message:

- **Lead with what's actually true.** The cause in the first sentence or two — not a preamble,
  not a restatement of what I asked, not "I investigated X and found several things."
- **Approaches are paragraphs, not records.** One short paragraph each: what it is and the
  honest reason to pick it or not, with the validation result and the difficulty carried
  *inside* the argument. Never a per-candidate template with `Tradeoffs:` / `Validation:` /
  `Effort:` lines — three candidates times four labels is a wall, and it's the finding-card
  shape `response-altitude.md` bans.
- **The difficulty read is a clause, not a section.** It's how big this is — say it where it
  bears on a choice ("~82 executors, plus every node added later"), not as its own block.
- **End with the decision you need from me.** One line, stated plainly: which approach, or the
  specific question blocking you. A scope message that ends without naming what it wants
  forces me to ask — that's the failure this section exists to prevent.
- **Length follows the decision, not the effort.** A big investigation that resolves cleanly
  gets a short message. Never pad to show the work, and never trim by *checking* less — what
  you show and what you verify are separate axes.

## Guardrails

- **Share as you go.** Findings land in conversation as they're settled; don't hold everything
  for one dump at the end. This is a discussion phase, not a report. But "as you go" means
  *ordered within the message* — lead with the cause, then the options — not a hard stop after
  every phase. There is exactly one mandatory stop: I pick the direction before you write the
  file. Stop earlier only when the premise itself changed (see Investigate).
- **No descending.** If the discussion starts producing task lists, file-level change plans,
  or schemas — stop, say "that's plan territory", and capture the thread as an open question
  instead. This applies to your own output too: catch yourself.
  **Naming code to explain a cause is not descending.** Saying "`AdvancedFilter` copies
  `value` into local state at mount and never reads it again" is exactly the job — you cannot
  state a mechanism without naming the mechanism. The line is *explaining* versus *planning*:
  which code is implicated, yes; which files to change and in what order, no.
- **Honest tradeoffs.** Every approach gets real costs named. An approach with no listed
  downside means you haven't thought about it enough.
- **No invented requirements.** Scope what I asked about. Gaps you notice become open
  questions, not silently-added scope.
- **Resolve before asking.** An open question is a last resort, not a catch-all for anything
  unresolved. Before one lands in the file, try to answer it yourself — a targeted read or
  research pass. Keep only what genuinely needs my call, and phrase each as a straight,
  answerable question with your recommendation — so the gate can ask it plainly rather than
  hand me a vague list.
- **One artifact, no state.** No session files, no hooks, no auto-transition into plan
  (Wave 1: I drive).
