---
name: create-project-overview
description: Write a project's one-page Overview in Notion — the customer problem and what the project builds, Goals handed off to the eng doc, a concrete Measurement bar (acceptance suite, usage metrics, extensibility), the dated Timeline, Stakeholders and Team. Grounded in the PRD, eng doc and Linear project; one approval gate on the outline, then the whole page in one pass, reviewed after. Standalone, and the `overview` step of create-project-discovery. Triggers on "write the project overview", "create the overview for <project>", "/create-project-overview".
---

# create-project-overview — the one-page why, success bar and who's involved

Leads, PMs and stakeholders open this page first. It answers three things fast: why the project
exists, how we'll know it worked, and who is involved. Everything deeper lives in the PRD and the
eng doc, and the overview links there instead of restating them.

## 1. Inputs

- **Target page** — where the overview goes. Usually a blank `<Project> - Project Overview`
  child of the project's workspace hub. Write into the page I give; create one only if I ask.
- **Sources** — the PRD, the eng doc (its Goals and Non-goals section), the Linear project, and
  the project's knowledge-base overview if there is one. Look these up from the workspace hub
  before asking.

## 2. Research

Read the sources (a subagent keeps the page dumps out of the main thread) and pull out: the
customer problem in the customer's terms, what the project builds, the acceptance behaviours the
eng doc or tickets commit to, any named prospects or customers it unblocks, the release dates,
and the people with a role on it.

## 3. Outline → my yes

One bullet per section saying what it will hold, the Measurement items in full, the Timeline
dates and where they came from. Flag anything the sources don't settle (no dates yet, an
unnamed stakeholder role). **Wait for a yes**, then write the whole page in one pass. I review
after; there is no per-section gate.

## 4. Shape

H1 sections, in order. About 40–50 lines; no padding.

- **Introduction** — two short paragraphs: the customer problem, then what the project builds.
- **Goals** — one line mentioning the eng doc's Goals and Non-goals section. Never restate them.
- **Measurement** — a numbered list of three:
  1. **Test Acceptance Suite** — 3–5 end-to-end behaviours checked against a real (test) vendor
     org, each one observable ("fires exactly once", "appears on the timeline once").
  2. **Usage and Metrics** — the pilot bar, then Quantity, Time-to-Value and Deals / Customers
     Unblocked, naming customers only where a source names them.
  3. **Extensibility** — what the next provider or variant should cost.
- **Timeline** — dated bullets per release stage (initial testing, UAT / pilot org, all
  customers; `knowledge-base/concepts/release/release-stages.md`). No dates yet → "TBD after
  <what unblocks them>", never an invented date.
- **Stakeholders** — one line per person: name, role, relation to the project.
- **Team** — one line on who builds it.
- **Docs** (optional) — a link list, only when the hub doesn't already carry it.

No progress status anywhere: that's `create-progress-report`'s job, and the overview would rot.

## 5. Reference docs

Structure only — never copy content.

- [Sequences Integration - Project Overview](https://app.notion.com/p/3de7019cb5b180ae9117dc2133d3215b)
- [Prospecting Integrations - Project Overview](https://app.notion.com/p/4107019cb5b180d5974bc9aa786b835f)

## Guardrails

- **No invented requirements, dates or customers** — a gap is flagged in the outline.
- **Notion writes go only to the target page.** Linking it from the hub is my call; propose it.
- Scratch under `~/.claude/tmp/<project-slug>/`.
