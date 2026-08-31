---
name: langfuse-traces
description: Analyze traces in Langfuse — latency, throughput (ms per output token), token usage, cost, error rate — sliced by organization, workflow/flow, module, or model. Runs through the Langfuse MCP connector (no login, works in background sessions). Covers the discovery ladder for finding the right observation name and metadata keys, the parent-span/child-generation join that trace data actually requires, and the unit + filter traps that silently return wrong or empty results. Traces only — not prompts, datasets, scores, or evaluators. Triggers on "check langfuse", "analyze the traces for X", "latency per token", "how slow is <node/module>", "why did that Datadog LLM monitor fire", "find traces for org/flow X".
---

# langfuse-traces — analyze traces

> Personal harness tool. Runs through the **Langfuse MCP connector** (`mcp__langfuse__*`) —
> self-refreshing auth, no browser step, works in a background session.
> Project `cm0o7tz9u005xl6rxv30rky82` on `https://us.cloud.langfuse.com`.

**Scope: traces only.** Observations, their latency, tokens, cost, and metadata. Prompts,
datasets, scores, evaluators and dashboards are out of scope — don't reach for those tools here.

## The five tools that matter

| Tool | Use it for |
|---|---|
| `getObservationFilterValues` | **Discovery.** What observation names / environments / models exist. |
| `getObservationFilterSchema` | Which columns are filterable in `listObservations`, and with which operators. |
| `getMetricsSchema` | Which measures/dimensions/filters `queryMetrics` accepts. |
| `queryMetrics` | **Aggregates.** Percentiles, counts, time series. Fast, cheap, no raw rows. |
| `listObservations` | **Raw rows.** The only way to get per-run values, and the only place you can filter on `latency` or token counts. |

Reach for `queryMetrics` first — it answers most questions without pulling rows.

## Always pin the environment

`environment` values in this project: **`prod`**, `default`, `local`, `pytest`. Local dev and
pytest runs land in the same project, so an unpinned query silently mixes them into prod numbers.
Every query gets `{"column":"environment","operator":"=","value":"prod","type":"string"}`
(`listObservations` wants `"any of"` with a list).

## Discovery ladder — never guess a name

Names are **not** the code's identifiers. A flow node's `NodeType` is
`clean_and_transform_data`, but the trace is named **`WorkflowCleanAndTransformData`**. Look it up:

```
getObservationFilterValues(column="name", fromStartTime=…, toStartTime=…, limit=100)
```

Then read one real row before writing any metadata filter — the keys are not guessable, and a
wrong key returns an empty set rather than an error:

```
listObservations(name="<TheName>", fromStartTime=…, toStartTime=…,
                 fields=["id","metadata","latency","traceId"], limit=5)
```

Scoped reads (anything projecting or filtering `metadata`, `input`, or `output`) **require**
either a `traceId`, an `id` filter, or **both** `fromStartTime` and `toStartTime`.

## Trace shape for flow-engine / `ReePredict` modules

Only nodes that make an LLM call are traced (`LLM_NODE_TYPES`). One node execution =

```
<ModuleName>            root SPAN  → carries the DOMAIN METADATA, and the wall-clock latency
└── dspy.Predict        GENERATION → carries TOKENS, cost, model. ONE CHILD PER RETRY ATTEMPT.
```

**The domain metadata and the token counts live on different observations.** This is the single
most important fact in this skill.

| | Parent span | `dspy.Predict` child |
|---|---|---|
| `organization_id`, `user_flow_id`, `flow_run_id`, `workflow_id` | ✅ | ❌ |
| `usageDetails` (input/output tokens), model, cost | ❌ (empty `{}`) | ✅ |
| `scope.name` = `"<ModuleName>-tracer"` | ✅ | ✅ |

So **filter the parent for *who*, the child for *how much*, and join on `traceId`.**

`workflow_id` is the **Temporal** workflow id, not a flow id. `node_id` is absent entirely — to
get back to a node you need `flow_run_id` and the flow-run record. Flow-node traces have **no**
Langfuse-native `userId` / `sessionId` / `tags` / `version` — those fields are empty; don't filter
on them.

## Filtering metadata

`metadata` is a `stringObject` column and **requires a `key`**:

```json
{"column":"metadata","key":"organization_id","operator":"=",
 "value":"4d29f892-7e25-4efa-ad0b-f348bd0fc0fc","type":"stringObject"}
```

Org ids are in the `reevo-internal-orgs` rule. Resolve a `user_flow_id` to a human name with the
**`snowflake`** skill: `SELECT id, name FROM POSTGRES_DB_PROD.PUBLIC.USER_FLOW WHERE id IN (…)`.

**Scoping children when they carry no domain metadata:** filter
`metadata["scope.name"] = "<ModuleName>-tracer"`. That is the discriminator that survives on the
child, and it scopes to the module exactly the way a Datadog `module:` tag does.

## Traps — each of these silently returns wrong or empty results

1. **`latency` units differ by tool.** **Seconds** in `listObservations` (both the filter value and
   the returned field: `2.406` = 2406 ms). **Milliseconds** in `queryMetrics`. Same field name.
2. **`queryMetrics` cannot filter or group by `latency` or token counts** — only dimensions,
   `metadata`, and `start_time`. To slice on a latency threshold you *must* use `listObservations`,
   which does expose `latency`, `inputTokens`, `outputTokens` as number filters.
3. **Operators are not consistent across the two tools.** `metadata … "contains"` and a
   `traceName` filter both work in `queryMetrics` but have returned **empty** in `listObservations`
   for data that demonstrably exists. In `listObservations`, prefer exact `=` on metadata.
4. **Instrumentation changes silently break filters.** On **2026-08-28** the `dspy.Predict` child
   lost `user_flow_id` and `traceName` and gained `scope.name`. Any query built on the old keys
   returns 0 for later dates — which reads exactly like "no traffic". Always sanity-check a zero.
5. **Verify coverage before trusting any aggregate.** Count children against parents for the same
   window. Full coverage means equal counts; anything less means your filter is sampling.
   (`scope.name` gave 80/79/75 vs parent 80/79/75 = 100%; the older `user_flow_id`-on-child filter
   gave ~50% and would have halved every count.)
6. **A bogus-value control proves the filter binds.** Run the same query with a nonsense org id and
   confirm it returns 0. A filter that matches everything and a filter that works look identical.

## Context economy — route raw rows to files, never into the conversation

`listObservations` output for ~100 rows with `metadata` is >100k characters. When a result exceeds
the cap the MCP layer **saves it to a file and returns the path** — that is the cheap path, so
trigger it deliberately: request `fields:[…,"metadata"]`, split the window by day to stay under
`limit: 100` (avoids cursor chaining), then parse the files with a Python script and never read
them into context. Scratch goes under `~/.claude/tmp/<slug>/` per `scratch-files.md`.

Do the arithmetic in Python, not mentally — these analyses turn on ratios where a rounding slip
changes the conclusion.

## Computing throughput (ms per output token)

Langfuse has no native ms/token measure. It is `avg latency ÷ avg output tokens`, which is also
exactly what the Datadog LLM-throughput monitors compute, so the two are directly comparable:

```
queryMetrics(view="observations",
  metrics=[{measure:"latency",aggregation:"avg"},{measure:"outputTokens",aggregation:"avg"}],
  filters=[name = "dspy.Predict",
           metadata["scope.name"] = "<ModuleName>-tracer",
           environment = "prod"],
  timeDimension={granularity:"hour"})
```

Then divide per bucket. Two things to hold onto when reading the result:

- **It is a ratio of averages, not an average of ratios** — matching the monitor. In a low-volume
  bucket one hung call moves it enormously; always report `n` alongside the ratio.
- **ms/token is mildly *anti*-correlated with output size** (fixed per-call overhead amortizes), so
  a run that looks slow on raw latency can be the most efficient per token. That is the whole point
  of the metric: raw-latency thresholds misclassify big-output runs as incidents.

**Ruling retries in or out:** count `dspy.Predict` children under the parent. One child = a single
attempt that genuinely hung (a provider stall). Two or more = a retry.

## Worked example

`references/worked-example-ms-per-token.md` — the full 2026-08-31 investigation of
`WorkflowCleanAndTransformData` throughput: reproducing a Datadog monitor from trace data,
every query used, the parent/child join, coverage verification, and the findings. Read it when a
new analysis rhymes with it; it is the fastest way to reuse the shape rather than rediscover it.
