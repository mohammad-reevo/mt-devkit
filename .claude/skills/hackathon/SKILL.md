---
name: hackathon
description: My personal hackathon — vibe a provable MVP of a new concept agentically, to find where we can innovate and learn something, not to ship. Two modes. `ideate` brainstorms ideas with me (workflows/integrations first, beyond is fine), ranks each one's innovation 1–5, and keeps the Hackathon Ideas database in Notion current — adding, merging and dropping ideas as I react. `execute <idea>` takes one idea from that database to a demoable MVP via `workflow` in agentic mode, on a hackathon base branch that never merges to main, ignores CI, and ends with the result written back to the idea's Notion page. Triggers on "hackathon", "let's brainstorm hackathon ideas", "more hackathon ideas", "build the hackathon idea", "execute <idea>", "/hackathon".
---

# hackathon — innovate, prove it, learn

Not a real hackathon. The point is to vibe a **simple, provable MVP** that demonstrates a concept,
so we can see where Reevo can innovate and learn something new along the way. It is never
production-ready and never meant to merge. Once an idea is picked I leave you loose for hours: no
PR reviews, no guidance, no check-ins.

**Innovate, don't match the competition.** An idea that copies what another tool already does, or
that is already on our roadmap, is not a hackathon idea. My home turf is workflows and
integrations; ideas may go beyond it, a new page or a completely new product included.

## The doc

Everything lives in Notion, on my private **Hackathon Projects** page:
https://app.notion.com/p/4027019cb5b180759087fb6bd57e5b44

Its inline **Hackathon Ideas** database (data source `collection://d7d9dc30-f15a-43a5-8aa5-c0c53ea8ea70`)
is the list of ideas — the source of truth, never a copy in this repo. Columns:

| Column | Values |
|---|---|
| Idea | title |
| Category | Added feature (extends an existing product) · Detached / new surface (a new page or surface beside them) · Completely new (no current product does this) |
| Summary | one or two lines |
| Area | Workflows · Integrations · AI · Ask Reevo · Spreadsheets (add options as needed) |
| Status | Idea · Discussing · Building · Demoed |
| Innovation | 1–5, rubric below |

Each idea's page carries `## Pitch` (or `## Original pitch` for mine), `## Sub-ideas`, and
`## Deep dive`. **Ideas are not bite-sized**: a related idea folds into an existing one as a
sub-idea, and which pieces we build is decided at execute time.

**Innovation rubric** — 1 not even worth it · 2 cool but not that big · 3 average · 4 innovative
and worth doing · 5 cutting edge (what Anthropic is trying right now).

### Working the Notion connector

- **Fetch before every edit** — I reorganize the page and the rows myself between turns.
- **`update_content` drops `properties`.** Passing both in one call changes the content and
  silently keeps the old properties; set properties with their own `update_properties` call.
- **`query-data-sources` (rows/SQL) has a workspace quota** that runs out mid-session. Read the
  data source with `fetch` and rows by page id instead; keep a row's page id when you create it.
- Notion is my private page, so writing to it is not outward-facing — no approval needed for an
  edit I asked for or that a mode below prescribes.

## Mode: ideate

Brainstorm mode (`explanation-modes.md`): ideas at altitude, never implementation. Read
`ideation.md` in this directory first — it is what I liked, what I dropped and why, and the
principles behind both. Don't re-pitch anything it lists as dropped.

1. **Read the database** so you know what exists, and pitch around it: a spin on an existing idea
   becomes a sub-idea there, not a new row.
2. **Pitch a numbered batch**, each item a bold name, two or three lines, and an innovation rank.
   Mix spins on my ideas with your own. Before pitching, ask yourself whether it already exists in
   Reevo, is on the workflows roadmap, or is just a better version of something we have (the AI
   workflow builder, field history, imports) — if so, drop it or say so.
3. **Recommend** the few you'd pick, one line each on why, then ask what goes in the table.
4. **Apply my reactions in the same turn**: add rows (rank them), fold ideas into existing pages
   as sub-ideas, drop what I drop, and capture my reasoning on the idea's page (Deep dive) when I
   give it. Then record what I liked or dropped, and why, in `ideation.md` — that file is how the
   next session pitches better.
5. **Keep going** until I say I'm done; then help pick one to execute — recommend on innovation,
   whether a few hours can prove it, and how demoable the proof is.

## Mode: execute `<idea>`

Take one idea to a demoable MVP. This session becomes the **orchestrator**
(`orchestrate-session`): it holds the idea and the index, and each slice runs in its own
sub-session as an agentic `workflow` drive (`workflow` § Modes). The funnel phases do the work.

### 1. Frame the MVP

- Fetch the idea's page; set Status to **Building**.
- Settle the **provable slice**: the smallest build that demonstrates the concept with evidence —
  a number (tokens, cost, latency, records affected), a run you can show, or screenshots. Say what
  the demo will show before anything is built. Research the code first (a subagent) so the slice
  rests on what exists.
- Name the project `hackathon-<idea-slug>` and split the slice into the few pieces that can build
  in parallel (BE / FE / one per sub-idea), with the contract between them (the endpoint or types
  the FE consumes). Write the MVP framing — what's in, what the demo shows, the slices — into the
  idea page's Deep dive.

### 2. Drive it

Run `orchestrate-session` for project `hackathon-<idea-slug>`, with the framing as its project
brief. The brief and index carry `> Hackathon: <idea page URL>`, which switches on
`orchestrate-session` § Hackathon (orchestrator-owned bases, merging, the openapi bridge, the
demo stack) and, in every sub-session, `workflow` § Hackathon projects:

- **MVP bar, not house bar.** Scope and plan aim at the demo; tests only where they help prove
  it; reviewer findings that are polish or house-rule conformance are declined, correctness ones
  that would break the demo are fixed.
- **The base branch is `mohammad/hackathon-<idea-slug>-base`** in each repo touched, cut once from
  fresh `main`. Slice PRs target it (ready, never draft). **It never merges to main** — no final
  PR, no update-branch from `main`, ever. Main moving on is irrelevant.
- **CI is not a gate.** No babysit; a red check is ignored unless it points at a real bug in the
  demo path.
- **The orchestrator merges** each verified slice into the hackathon base, and only there;
  sub-sessions never merge.
- Agentic stops still stop (`workflow` § Modes): a repeated failure or structural drift ends that
  slice, and the rest carry on.

### 3. Prove it, then write it up

verify proves each slice on its own local stack (`tester`). Once every slice is merged into the
bases, the orchestrator runs the end-to-end demo on one stack across them
(`orchestrate-session` § Hackathon), capturing the evidence the frame promised. Then write the
result onto the idea's Notion page, under a `## MVP result` heading:

- what was built, and what it demonstrates — with the evidence (numbers, screenshots)
- how to run the demo: the branches, the stack, the exact steps
- the PR links
- what we learned, and what a real version would need

Set Status to **Demoed**. Close with the page link and the one-paragraph story I'd tell someone
about it.

## Guardrails

- **Nothing reaches main.** Not a merge, not a PR targeting it, not a cherry-pick.
- **Brainstorm stays a brainstorm.** Ideate never starts building; execute starts only on my pick.
- **The database is the list.** Never keep a second list of ideas in a file or the KB.
