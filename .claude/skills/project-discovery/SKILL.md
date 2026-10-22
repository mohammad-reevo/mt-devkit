---
name: project-discovery
description: Understand a multi-ticket project in depth before anyone executes it — the product context, how the systems involved work, the design, its gaps, the eng doc, the implementation doc, the tickets, the open questions and the knowledge base — one step at a time, each written up for me to read before the next starts. Sets up a scratch dir with a short main file (step order, decisions, parked, notes), one write-up file per step, and an open-questions file; hands a short core step list plus a menu of optional steps (vendor spike, test org, timeline, release strategy, another team's dependency, reviewer comments, PRD update). Composes create-eng-doc, create-implementation-plan, linear-tickets, author-knowledge-base and workflow's project drive rather than duplicating them. Standalone, upstream of workflow. Triggers on "discover this project", "understand <project> before we build it", "start project discovery", "next discovery step", "/project-discovery".
---

# project-discovery — understand the project before executing it

For the shape of project that needs more than `scope`: a multi-ticket feature with a PRD, a
design doc, a Linear project, often a vendor and a dependency another team owns. The aim is
that execution is a breeze and can lean on agents, because every error a design can carry
was caught on paper first. Modelled on the Outreach / Sequences Integration discovery.

A single idea or ticket is `scope`'s job, not this one.

## Modes

- **`start <project>`** — set up the scratch dir (§ Setup), then run the first step.
- **`<project>`** (resume) — read the main file, report where things stand in two lines, and
  continue with the next step the main file allows (§ Running a step).
- **`add <menu step> [after <step id>]`** — put a menu step into the order.

## Setup

Scratch lives in `~/.claude/tmp/<project>/` (per `scratch-files.md`):

```
main.md               the spine — step order, decisions, parked for v2, notes
steps/<step-id>.md    one write-up per step
open-questions.md     every question, stable Qn numbers
```

1. **Ask once which source wins on a conflict** (AskUserQuestion) — e.g. "the design doc and
   the Linear tickets over the old PRD; the tickets win; the code is the reference for anything
   already built". Write the answer at the top of `main.md` and `open-questions.md`.
2. Copy `templates/main.md` and `templates/open-questions.md` in, and fill the goal line.
3. Write the **core steps** into the order, in the order below. Menu steps go in only when I
   ask (`add`), or when you propose one and I agree.

**Step ids are stable slugs, never numbers that get renumbered.** The order is a separate
numbered list in `main.md`; its numbers are positions only, and nothing ever refers to them.
Write-ups, questions and decisions name a step by its id (`design`, `spike`). Inserting a
step is one new line — never a renumbering pass.

## Core steps

Every multi-ticket project needs these, in this order:

1. **`context` — product context.** Read and digest the PRD, the design doc and the Linear
   project. Produces: the problem, the product bet, who experiences what. Questions it raises
   go to `open-questions.md` under this step.
2. **`systems` — how the systems involved work, at altitude.** The native system and, if
   there is one, the vendor's — the same idea in two vocabularies. Conceptual, not code paths.
3. **`design` — system design and intended end state.** The big write-up: scope, each
   component, how the pieces connect, grounded in the code. I read it slowly and ask questions.
4. **`gaps` — retrospective on the product gaps.** Re-read the parked questions with the
   design in hand. Each gap gets context, a recommendation, what it changes, and In short; I
   make the call per gap. Corrections fold back into `design` inline (§ Corrections).
5. **`eng-doc` — eng doc.** Via `create-eng-doc`: open scope decisions first, a draft shaped
   like its golden example, then its review-only loop while I rewrite. Detail cut from the doc
   lands in `implementation-details.md` in this scratch dir.
6. **`impl-doc` — implementation doc.** Via `create-implementation-plan`, reading
   `implementation-details.md`: sections, one sentence per ticket.
7. **`tickets` — tickets.** Via `linear-tickets`: apply the implementation doc's breakdown to
   Linear. Carries the **Carry-ins** list (§ Conventions).
8. **`questions` — revisit the open questions.** Close what the earlier steps answered, make
   the remaining calls, carry ticket-level leftovers into Linear.
9. **`kb` — knowledge-base entries.** Via `author-knowledge-base` — this step is the explicit
   ask its write rule needs: an overview (what the project is, where its docs live), rules
   (norms any session on the project must follow), progress (which tickets moved).
10. **`execute` — begin executing.** Hand the ticket groups to `workflow`'s project drive.

## Menu steps

Each goes in only when the project needs it:

- **`timeline` — timeline from measured velocity.** Via `estimate-timeline`: dates I can
  defend, not a gut call. Feeds `release`; the dates land where I put them.
- **`release` — release strategy.** Which slices reach UAT, beta and all customers, and when
  (`knowledge-base/concepts/release/release-stages.md` for the stage names). Needs the
  blockers and the timeline first.
- **`dependency` — review another team's dependency.** Read their contract doc against our
  design; list each blocker, who owns it, and what it gates. Questions for that team are
  handed to me — I take them to the owner; the step never messages anyone.
- **`reviewers` — address reviewer comments on the eng doc.** The same loop as `eng-doc`: I
  rewrite, Claude reviews and hands wording, no direct edits without my go.
- **`prd` — update the PRD.** Product changes arrive mid-process. Fold them in via
  `create-prd`, then re-check the eng doc, the scope decisions and the implementation doc
  against the new PRD. My own notes pages stay unopened until this step starts.
- **`test-org` — set up a vendor test org.** One we are allowed to test in, never a
  customer's. Produces the credentials path and the rules for what may be created there.
- **`spike` — vendor spike.** Answers what the vendor's public docs leave open, in the test
  org. Blocked by `test-org`. Its findings fold back into the eng doc, the implementation doc,
  the tickets and `open-questions.md`; whatever it couldn't test is carried to a ticket.

A project may need a step that is neither. Add it with a new id and a one-paragraph entry in
the order, the same way.

## Running a step

**The main session waits strictly.** It starts the next step only after I say I've read the
current write-up. Between steps I ask questions: answer each in a few lines, end with an
**In short** line, and record it (a question goes in `open-questions.md`; anything else under
the step's write-up).

**Other sessions may run steps out of order**, when I start one for a step. The order line
then reads `in session <name>`, and the main session doesn't touch that step until it comes
back marked done. The other session writes its own step file and updates its own order line.

**Step statuses** in the order: `not started` · `in progress` · `awaiting your read` · `done` ·
`blocked by <step id>` · `in session <name>`. `done` is set when I say I've read it.

**Each write-up** (`steps/<step-id>.md`, shape in `templates/step.md`) opens with one italic
line saying when it was written and what it waits on, and ends with **In short**. Noisy
research goes to subagents; only findings land in the write-up.

## Open questions

`open-questions.md` holds every question the steps raise (shape in
`templates/open-questions.md`):

- **One `### Qn · <question> 🟢|🔴` entry per question.** Numbers are stable — never
  renumbered. Grouped under the step they came out of.
- **A digest at the top** listing only what's unanswered and what each waits on, then the
  count answered. Re-sort it whenever a status changes.
- **Every answer ends with an In short line** — read first; the rest is evidence.
- **A decision that answers a question is recorded under that question only**, as a dated
  `**Decision (Mohammad, <date>):**` line. Never also in `main.md`.
- **Answering.** Questions research alone can settle are answered in a batch, by subagents;
  each stays 🔴 with `· proposed` in its heading until I've seen it. Questions that are my call
  come to me one at a time (per `discussion-turns.md`).
- **Spike-dependent questions are parked, not guessed** — the heading names what it waits on.

## Conventions

- **Decisions before the doc that depends on them.** Make them explicitly (AskUserQuestion)
  before writing anything that would otherwise hedge.
- **`main.md`'s Decisions list** holds dated decisions that didn't come from a question —
  including terminology I dislike, so later writing avoids it.
- **Scope-adding findings go to the `tickets` step's Carry-ins list**, not into the eng doc.
- **Claude never edits a section I wrote.** It suggests old → new; I write
  (`create-eng-doc` §6). Claude-authored sections go to Notion only on my go, re-fetching the
  page first so my edits survive.
- **Superseded docs are kept, not deleted** — a historical overview stays, marked superseded.
- **Facts about the code are verified before they're asserted** (`shipped-work-code-is-truth.md`);
  nothing is invented to fill a gap (`no-invented-requirements.md`).

### Corrections

When a later step proves an earlier write-up wrong, don't rewrite history: add an inline
`**Correction (<step id> / Qn, <date>):**` note at the point it corrects, and mention it in
the later step's write-up.

## Guardrails

- **Never message anyone, request reviews, or publish a doc** — questions for other people
  come to me; Notion publishes are on my go.
- **One step at a time in the main session** — no running ahead.
- **Composes, doesn't duplicate** — the eng doc, implementation doc, tickets, KB and
  execution belong to their own skills; this skill sequences them.
- **The scratch dir dies at `/done`.** What must outlive the project goes into the KB in the
  `kb` step.
