---
name: agent-testing-party
description: Run an agent-driven testing party for a project before UAT — interactively. Asks me what to test, against which environment, which external systems it may write to, and which steps only I can do; splits the work into areas of scenarios I approve; builds a reproducible testing kit in the knowledge base (README setup recipe, scenarios, results, scripts, evidence); runs it area by area, keeping the kit current as it goes; turns product bugs into a Linear parent + sub-tickets; hands the fixes to orchestrate-session; and re-tests on main once they merge. The kit is the lasting reference point — the next run starts from it. Reference run — Sequences Integration, `knowledge-base/projects/sequences-integration/testing-kit/`. Not the human testing party: `create-testing-party-doc` writes its Notion doc and `testing-party-triage` gathers its Slack-filed bugs. Triggers on "run a testing party", "agent testing party", "test this project end to end", "build a testing kit", "/agent-testing-party".
---

# agent-testing-party — test a project end to end, and leave a kit behind

A testing party run by the agent: it exercises a feature against a real environment, scenario by
scenario, and records everything in a **testing kit** in the knowledge base, so the tests can be
re-run and the results stay a reference point. Reference run: Sequences Integration —
`knowledge-base/projects/sequences-integration/testing-kit/` (six areas, a local stack, GTM's live
Outreach org, four bugs → CRMF-3051 → fixed through `orchestrate-session` → re-tested). Read its
README before starting a new kit; it shows every section below in use.

**It is interactive.** Every phase that needs a call asks me, one numbered question at a time, with
options and a recommendation (`discussion-turns.md`). A question the code, the docs or a read-only
tool can answer is researched, not asked.

## 1. Frame — ask me

Read what exists first: the project's KB entries, PRD / eng doc, tickets, any human testing-party
doc. Then ask only what's still open, one at a time:

1. **What's in scope** — the features / tickets to cover, and what's explicitly out (e.g. waiting
   on another team, needs an account we don't have).
2. **Environment** — local stack (default: isolated, its own org; dev is shared and flaky), dev,
   or both. Data that pollutes an org (imports, backfills, bulk contacts) runs in a **throwaway
   org** (`concepts/local-env/throwaway-orgs.md`).
3. **External systems and their write rules** — for any live vendor org: which records the agent
   may create or change (a name prefix like "[Testing Party]", specific sequences / mailboxes),
   whether each write must be announced first, and cleanup. Write the rules into the kit README
   before the first write.
4. **What only I can do** — OAuth consent, opening a real inbox, a click in a vendor UI, approving
   a backfill. Each becomes a `>>> MOHAMMAD:` step with exact instructions; everything else the
   agent does itself, through APIs where a UI isn't needed.
5. **Where to stop** — e.g. report bugs only, or also fix them.

Record each answer as it's given in the kit README (§ 3) — never only in the conversation.

## 2. Plan the areas — I approve

Split the scope into **areas**, one per capability (e.g. enroll, pause/resume/unenroll, trigger
events, changes made in the vendor, manual UI, backfill). Per area, list numbered scenarios —
one observable behaviour each, with the expected result — and how each runs:

- **scripted** — a kit script drives it through the API and asserts on the DB / vendor state;
- **agent UI pass** — a `tester` subagent with Playwright, screenshots as evidence;
- **manual** — a `>>> MOHAMMAD:` step.

Present the areas as a table (area · scenarios · how · needs me?) and an order (cheapest
confidence first; areas that create shared fixtures before those that use them). Wait for my
approval; an area I cut goes into the README's out-of-scope list with why.

## 3. Build the kit in the knowledge base

`knowledge-base/projects/<project>/testing-kit/`, written through `author-knowledge-base`
(a `projects/` write: write, then show). One index line naming what's on screen when it's needed:
the env, the scripts, the gotchas.

```
README.md            setup recipe, rules, script list, evidence, after-a-run
scenarios/<area>.md  numbered scenarios + how each runs (+ code facts learned)
results/<area>.md    latest result per scenario: 🟢 works · 🟡 off · 🔴 broken · ⚪ not run
scripts/area<N>_*.py one per scripted area
evidence/            screenshots, run output, bug write-ups — what scratch would lose
```

- **README is the recipe a cold session follows**: how to bring the environment up, every process
  started by hand and why, fixtures (orgs, users, connections, ids), the external-write rules, the
  `>>> MOHAMMAD:` steps, the scripts and their flags, and the cleanup after a run.
- **Scripts are re-runnable**: a fresh `<tag>` per run in every name they create; `--target`
  (stack / dev); refuse to run if other active flows would fire (`--switch-off-others` to
  proceed); a cleanup that leaves the env as found; a final settle + audit that catches late
  duplicates; state under `~/.claude/tmp/<kit>/` (recreatable) — never evidence there.
- **Results are latest-per-scenario**, overwritten each run, citing run / record ids inline, so the
  record survives without the scratch dir.

## 4. Run, area by area

- One area at a time, in the approved order. Narrate each step in a line; stop for me only at a
  `>>> MOHAMMAD:` step, and give the exact instructions.
- **Keep the kit current in the same turn as you learn it.** A process you had to start, a fixture
  you had to create, a script bug you fixed, a flaky step and its workaround — into the README /
  script before moving on. This is what makes the kit reproducible; a run that only lives in the
  conversation is lost at compaction.
- Long or noisy work (a UI pass, a full area run) goes to a `tester` subagent with a brief that
  names the kit, the env, the write rules, and the report shape; keep only its verdicts.
- Before compaction in a long party, `handoff-session` — the reference run needed it twice.
- **Classify every failure**: a script bug (fix the script, re-run) vs a product bug (record it,
  move on). Never mark a product bug 🟢 by bending the script's expectation to match it.

## 5. Bugs → Linear

Each product bug gets a write-up in `evidence/bugs-<id>.md`: what happens, what's expected, the
cause where known (`file:line`), evidence (run / record ids, log lines), and the script step that
reproduces it. At the end of the run, ask me before filing, then `linear-tickets`: a parent
("Agent testing party: bugs found" — the areas tested, what's out of scope, where the kit is) with
one sub-ticket per bug. Write the ticket ids back into the write-ups and the results rows.

## 6. Fix — only if I said so in § 1

Hand the bugs to `orchestrate-session`: one PR per bug, each to main (no project base unless the
fixes chain). The sessions read the bug write-ups and the kit's repro steps.

## 7. Re-test on main

Once every fix has merged: pull main into the kit's environment, re-run each bug's repro step
(a `tester` subagent), and flip its results rows with the new run's ids. A fix that changes
behaviour other scenarios relied on (e.g. a stricter refusal) updates those scripts' expectations
in the same pass — otherwise the next run reports false failures. Copy the evidence into
`evidence/`.

## 8. Close out

Report: what the kit holds (KB additions), what was tested in total and its result, the bugs and
their tickets, what stayed out of scope. Take the environment down (`local-stack down`, plus every
process started by hand, by PID). Name any acceptance criteria the party didn't cover, so they're
not mistaken for done.

## Gotchas from the reference run

- **A stack's default processes aren't the whole product.** Consumers, workers and pollers a
  feature needs may not start by default — symptoms are "nothing happened" (events never written,
  sends stuck QUEUED, a page 404ing). Find the missing process, start it, and write it into the
  README.
- **Quick tunnels die when the Mac sleeps** — vendor webhooks then point at a dead URL. The README
  carries the restart recipe; check the tunnel before each run.
- **OAuth consent has a short window** (~10 min for Outreach): have the URL ready when you ask me.
- **Never read `.env` secrets**; load them inside a script with python-dotenv.
- **Backfills and data migrations need my explicit approval per run**, dry run first.
- **Only my orgs stay clean** — a new throwaway org is fine and is left in place afterwards.

## Guardrails

- Never write to a live vendor org outside the rules recorded in § 1.
- Never merge, request reviews, or message people.
- The kit is the deliverable: a result not in `results/`, or a setup step not in the README, didn't
  happen as far as the next session is concerned.
