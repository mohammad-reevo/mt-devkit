---
name: create-implementation-plan
description: Turn a stream of work — an eng-design doc, a PRD, a described change, or a large diff to dissect — into a comprehensive, code-grounded implementation plan that decomposes it into independently-shippable pieces (each ≈ one ticket / PR / Claude-Code conversation) with explicit dependencies. Tracker-agnostic — produces a spec-style markdown doc, no Linear/Jira/ticket references or polished overview (a downstream "plan → Linear" bridge handles that). Scales from a 2–3 PR change to a full project. Standalone, upstream of the scope→plan→implement funnel. Triggers on "create an implementation plan", "plan out this work", "break this into PRs/tickets", "dissect this into workable pieces", "/create-implementation-plan".
---

# Create an Implementation Plan

Turn a converged stream of work into a **comprehensive, code-grounded implementation
plan** that decomposes it into independently-shippable **work items** — each roughly one
ticket / PR / Claude-Code conversation — with explicit dependencies. The output is a
single spec-style markdown doc. This skill owns the *decomposition and the code
grounding*; it is deliberately **tracker-agnostic** — no Linear, no ticket IDs, no
polished overview. A downstream "plan → Linear" bridge maps the plan onto a tracker.

**Scale to the work.** A 2–3 PR change gets a short flat plan; a full project gets
tracks/phases and deeper research. Match the effort to the input — don't over-engineer a
small dissection, don't under-plan a project.

**Shape of the run:** gather → ground in real code → decompose into work items → a light
bi-directional reconcile against the source → one approval gate on the breakdown → write
the comprehensive doc → iterate. Keep the main thread lean — delegate wide reads and code
research to subagents; think in the main thread.

## 1. Gather inputs

Collect (or infer from context) the source of work and the ground it touches:

- **The source of work** — an eng-design doc, a PRD, a scope doc, a described change, or an existing large diff to dissect. Read the design authority in full; there may be more than one.
- **The repos / subsystems** the work touches.
- **A slug** — a short kebab name for the work (reuse the idea's existing name if it has one).

**Most-recent source wins** on conflicts between documents — note the conflict rather than
silently picking one. Don't over-ask: for a small change, infer the essentials and proceed.

## 2. Ground it in real code

This is what makes it an *engineering* plan and not a wish-list. Fan out **research
subagents** (`Explore` / `general-purpose`) into the actual repos to turn the design into
**concrete touchpoints** — real services, files (`path/to/file.py:line`), functions, the
precedent being copied, the integration points. Keep the noisy exploration inside the
subagents; only the grounded findings return to the main thread.

**Scale depth to the work** — a small change may need one quick sweep; a project warrants
roughly one subagent per subsystem. Ground every load-bearing claim in a real identifier:
"the resolver" is weak; "`TemplateResolver` (`core/flow/runtime/template.py`)" is the bar.

## 3. Decompose into work items

The core of the skill. Carve the work into **independently-shippable pieces, each ≈ one
ticket / PR / Claude-Code conversation** (occasionally two — not a hard rule). For each:

- **Goal** — one line: what it accomplishes.
- **Deliverable** — what the PR ships.
- **Touchpoints** — the real files/functions it edits (from §2).
- **Dependencies** — what it is **blocked by** / **blocks**, at both item and sub-item level.
- **Rough size**.

Group into **tracks / phases** when the work is large; keep a **flat list** when it's
small. Draw the **dependency graph** and call out what can **start in parallel** and the
**critical path**. A good work item is a coherent body of work someone can pick up and ship
without half-finishing three others — split when a piece spans unrelated concerns, merge
when two are so linked that shipping one alone makes no sense.

## 4. Reconcile against the source (light, bi-directional)

A quick two-way sanity check — **only when there's a design doc to check against**:

- **Coverage:** every load-bearing detail in the source maps to some work item.
- **No drift:** the plan doesn't contradict the source, invent requirements, or silently re-scope.

Report any gap or contradiction and resolve it — fix the plan, or flag a source that needs
updating. Keep it simple; this is a sanity pass, not an audit. Skip it entirely when
there's no formal source (e.g. "dissect this diff into 3 PRs").

## 5. Propose the breakdown → get approval

Present the **work-item breakdown + dependency graph** and get the user's sign-off **before
writing the full doc**. This is the one collaborative gate — the user merges, splits,
resequences, or re-scopes pieces here. For each item give one line on what it is and its
blockers; flag anything genuinely optional or a follow-up. Reorganize on their steer until
they're happy, then write.

## 6. Write the comprehensive plan doc

On approval, write the plan to **`~/.claude/spec/<slug>-implementation-plan.md`** — the
durable artifact for a standalone change, or the input the "plan → Linear" bridge consumes.
Structure:

- **Goal / approach** — a few lines on what the work is and the shape of the plan; link the source doc(s).
- **Work-item breakdown** — every piece with its goal, deliverable, grounded technical detail, dependencies, and size. Grouped into tracks/phases for a project; a flat list for a small change.
- **Dependency graph** — an ASCII blocks/blocked-by diagram; note parallel starts + the critical path.
- **Settled decisions** — the calls made while planning, so they aren't re-litigated at build time.
- **Open questions** — genuinely unresolved build-time points. Pose them; don't invent answers.

**Comprehensive beats pretty.** The goal is a plan complete enough to drive real
implementation — each item buildable from its own entry plus the source docs it links. Do
**not** produce a separate polished overview or reference any tracker; the readable summary
and the tickets are the bridge's job.

## 7. Iterate

Hand it over: the user reviews and reorganizes directly. Adjust when asked; **re-read the
doc first** so you build on their edits, not your last version.

## Guardrails

- **Ground in real code** — every load-bearing claim traces to a real identifier (§2).
- **Tracker-agnostic** — no Linear/Jira, no ticket IDs, no polished overview. The plan stays portable; a downstream bridge maps it onto a tracker.
- **Most-recent source wins** on conflicts between source documents.
- **No invented requirements** — plan the decided work; a gap the source leaves open is an open question, not an invented answer.
- **Scale to the work** — a 2–3 PR change gets a short flat plan; a project gets tracks/phases and deep research.
- **Response altitude** when synthesizing multi-agent research — findings, not transcripts, into the doc and the chat.
- **Standalone, and distinct from the funnel.** Invoked directly, upstream of the scope→plan→implement funnel and of the "plan → Linear" bridge. Not the same as the funnel `plan` skill (per-idea task breakdown for immediate build in a worktree) or `plan-split` (fan-out to parallel worktrees) — this one decomposes a stream of work into shippable, dependency-linked pieces, agnostic of how they get built or tracked.
