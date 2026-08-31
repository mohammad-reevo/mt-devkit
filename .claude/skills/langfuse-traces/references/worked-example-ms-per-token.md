# Worked example — reproducing a Datadog LLM-throughput monitor from Langfuse traces

Real investigation, 2026-08-31. Question: *"Find all traces for the Clean and Transform Data node
for a specific workflow — can I filter by org id? Analyze latency, and latency per token."*

The target was Datadog monitor **25425944**, *[prod][Workflow] Clean & Transform Data LLM
Throughput Degraded*:

```
avg(last_15m):
  avg:salestechbe.llm.latency.avg{env:prod,module:workflowcleanandtransformdata}
/ avg:salestechbe.llm.tokens.output.avg{env:prod,module:workflowcleanandtransformdata}
> 80                              # warn 50, stated baseline ~24
```

Reproducing that ratio from trace data is the whole exercise. Follow the order below — each step
exists because skipping it produced a wrong answer the first time.

---

## 1. Find the real observation name

`NodeType.CLEAN_AND_TRANSFORM_DATA = "clean_and_transform_data"` never reaches Langfuse at
runtime. `getObservationFilterValues(column="name", …)` surfaced the actual name:
**`WorkflowCleanAndTransformData`**. The trace and the root observation share it.

## 2. Read one row before filtering

```
listObservations(name="WorkflowCleanAndTransformData", limit=5,
                 fromStartTime=…, toStartTime=…,
                 fields=["id","metadata","latency","traceId","environment"])
```

Metadata on the **parent span**:

```json
{"user_flow_id": "...", "organization_id": "...", "flow_run_id": "...",
 "workflow_id": "flow_<id>_trigger_CONTACT_CREATED_contact_<id>",
 "scope.name": "WorkflowCleanAndTransformData-tracer",
 "attributes.user_id": "...", "attributes.organization_id": "..."}
```

So yes — filtering by org id works, via the `metadata` `stringObject` column with
`key: "organization_id"`.

## 3. Aggregate latency, then look for structure

August 2026, GTM org, prod, n=6,506: avg 6.12 s, p50 **3.06 s**, p90 **17.1 s**, p95 18.9 s,
p99 21.7 s, max 47.9 s.

A p50→p90 cliff that steep is two populations, not a tail. Splitting by `user_flow_id`:

| Flow | n | p50 | note |
|---|---|---|---|
| `76e3fd57…` *Automated Outreach re-engagement* | 1,052 | **17.2 s** | owns the entire p90+ shoulder |
| everything else | 5,454 | **2.90 s** | |

The two buckets summed exactly to the total (1,052 + 5,454 = 6,506) — a cheap check that the
split was exhaustive and the filters weren't double-counting.

Flow names came from the **`snowflake`** skill:
`SELECT id, name FROM POSTGRES_DB_PROD.PUBLIC.USER_FLOW WHERE id IN (…)`.

## 4. Open one trace to see where the time goes

```
listObservations(traceId="<id>", fields=["id","name","type","latency","usageDetails",…])
```

```
WorkflowCleanAndTransformData   SPAN        15.788 s
└── dspy.Predict                GENERATION  15.684 s   claude-sonnet-4-6
```

Node overhead ≈ 0.1 s. **The node's latency is the LLM call.** The 17 s flow simply emits ~745
output tokens where the fast flows emit ~108 — at an identical ~42 tok/s decode rate. Not a bug.

## 5. The trap that invalidated the first answer

Raw latency was used as a stall proxy (`latency > 8 s`). Wrong: a 13.4 s run emitting **523**
tokens is 25.7 ms/token — perfectly healthy — while a 15.3 s run emitting **108** tokens is
141.8 ms/token. The first cut reported "46 stalls (1.2%)"; on the correct metric it was **1 in
234**. *Raw-latency thresholds misclassify big-output runs. ms/token is the discriminator — which
is precisely why the monitor divides output out.*

## 6. Scoping the child generation (where the tokens are)

Tokens live on `dspy.Predict`, which carries **no** domain metadata. Three filters were tried:

| Filter on the child | Result |
|---|---|
| `metadata["user_flow_id"] = …` | worked ≤ Aug 28, **0 rows** after — and only ~50% coverage before |
| `traceName = "WorkflowCleanAndTransformData"` | same: worked ≤ Aug 28, **0 rows** after |
| `metadata["scope.name"] = "WorkflowCleanAndTransformData-tracer"` | **0 rows before Aug 28, 100% coverage after** |

An instrumentation change on **2026-08-28** swapped which keys the child carries. The zeros looked
exactly like "the node stopped running" — it hadn't. Any saved Langfuse view scoped by `traceName`
or flow silently went to zero that day.

**Coverage check that caught it:** child counts per day vs parent-span counts per day.
`scope.name` → 80/79/75 against parents 80/79/75 = 1:1. The old filter → ~50%.

## 7. Compute the ratio

```
queryMetrics(view="observations",
  metrics=[{measure:"count",aggregation:"count"},
           {measure:"latency",aggregation:"avg"},
           {measure:"outputTokens",aggregation:"avg"}],
  filters=[{column:"name",operator:"=",value:"dspy.Predict",type:"string"},
           {column:"metadata",key:"scope.name",operator:"=",
            value:"WorkflowCleanAndTransformData-tracer",type:"stringObject"},
           {column:"environment",operator:"=",value:"prod",type:"string"}],
  timeDimension={granularity:"hour"})
```

Divide `avg_latency / avg_outputTokens` per bucket **in Python**, carrying `n` alongside.

**Validation that the reproduction is faithful:** the monitor's message states a baseline of ~24,
measured 2026-08-25. The same computation over Aug 25 trace data gave **23.5**. Do this — an
independent anchor is what separates "a number" from "the monitor's number".

## 8. Per-run table — the parent/child join

Aggregates can't give per-run values, so pull both sides and join. Split by day to stay under
`limit: 100` and skip cursor chaining; include `metadata` in `fields` so each result **overflows
to a file** instead of into context:

```
# children — tokens
listObservations(name="dspy.Predict", limit=100, fromStartTime=<day>, toStartTime=<day+1>,
  fields=["id","traceId","startTime","latency","usageDetails","metadata"],
  filter=[{column:"metadata",key:"scope.name",operator:"=",
           value:"WorkflowCleanAndTransformData-tracer"},
          {column:"environment",operator:"any of",value:["prod"]}])

# parents — flow attribution
listObservations(name="WorkflowCleanAndTransformData", limit=100, fromStartTime=…, toStartTime=…,
  fields=["id","traceId","startTime","latency","metadata"],
  filter=[{column:"environment",operator:"any of",value:["prod"]}])
```

Six calls → six file paths → one Python script joining on `traceId`
(`ms_per_token = latency_seconds * 1000 / usageDetails["output"]`). 234 rows, **0 unmatched**.
Total context cost of the raw data: ~600 tokens of file paths.

## 9. Findings

Aug 29–31, 234 runs, 100% coverage: median **18.2** ms/token, p95 30.7, p99 44.4, max **442.4**.
One run over crit, zero in the warn band.

| Flow | n | median out-tok | median ms/token |
|---|---|---|---|
| Enrich-inbound | 117 | 108 | 20.3 |
| Multi-owner-alert | 55 | 153 | 15.7 |
| Re-engagement | 62 | 1,068 | **14.2** |

- **ms/token falls as output grows** — a ~1 s fixed per-call overhead amortizing. The flow that
  looks worst on raw latency (~15 s/run) is the most efficient per token. A customer adding output
  fields pushes this metric *down*, not flat.
- **The alert was one hung call.** Aug 31 17:07:15Z: 47,777 ms for **108** output tokens =
  442.4 ms/token, with input/output both dead-on that flow's median, `level: DEFAULT`, no error. It
  landed in a 3-call hour and dragged the hourly mean to 141.3.
- **Retries ruled out.** DSPy emits one `dspy.Predict` child per attempt; every stalled trace had
  exactly **one**. The runbook's first suggestion (`llm.call.retry_attempt`) was the wrong lead.
- **Low volume is the amplifier.** Every hour above 30 ms/token had n=1 or n=3; all 13 runs above
  30 were small-output runs where a second of jitter moves the ratio ~9 points.
- **Monitor bug found:** the alert message says "~2 calls per 15 min, *which is why the window is
  1h*" — but the query is `avg(last_15m)`. The stated mitigation was never implemented.

## Checklist for the next one

1. Discover the observation name — never guess it from the code's enum.
2. Read one row; note which observation holds metadata and which holds tokens.
3. Pin `environment = prod`.
4. Aggregate first; look for multiple populations before explaining an average.
5. Verify coverage (child count vs parent count) and run a bogus-value control.
6. Use ms/token, not raw latency, whenever output size varies.
7. Route raw rows to files; do arithmetic in Python.
8. Anchor against an independent number (a monitor's stated baseline) before trusting the result.
