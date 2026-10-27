# <project> — project brief

> Orchestrator: <session name> (mt-devkit root). Tickets: <IDs>. Linear: <project, milestone>.
<> Hackathon: <idea page URL>>

## Goal

<What the project turns the product into, in a paragraph.>

## What done looks like

- <user-visible outcomes, one per line>

## Decisions (settled — don't re-litigate)

1. **<topic>:** <the decision, with the file:line it lands on where that helps a sub-session>.

## Orchestration

- **Bases:** every slice targets `mohammad/<project>-base` in <repos>; migrations target main.
  Merging slices into the base and the final base → main PR are Mohammad's.
- **Gates:** <direct — Mohammad answers each session's gates in that session | relayed — one
  session's gate at a time, through the orchestrator>.

## Open

- <a question no slice can settle alone; it moves to Decisions once answered>

## Contracts between slices

- **<contract>** — produced by `<slice>`, consumed by `<slices>`. <The shape, as planned; updated
  from each `decided` report.>
