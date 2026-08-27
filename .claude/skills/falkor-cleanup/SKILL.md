---
name: falkor-cleanup
description: Reap the local FalkorDB org graphs that integration tests leave behind, keeping only the org(s) I actually use. Each org graph costs ~20 MB of index scaffolding regardless of data, so a few hundred test orgs fill the Docker VM and the host OOM killer takes out vite and the backend. Targets graphs only — never Postgres, never Kafka. Runs as a step of `run docker`, and standalone when a test sweep has just bloated things. Also owns the diagnosis path for local Falkor OOM symptoms (empty accounts page, BusyLoadingError, unexplained `Killed: 9`). Triggers on "clean up falkor", "reap falkor graphs", "falkor is bloated", "prune the falkor graphs", "/falkor-cleanup".
---

# falkor-cleanup — reap local FalkorDB org graphs

> Personal harness skill, self-contained. Supersedes the old
> `local-falkordb-graph-bloat` rule and its Postgres-cascade purge script, both of
> which attacked the wrong layer.

## The mechanism — why graphs, not Postgres

FalkorDB is a Redis module. **One org's entire graph is a single Redis key** —
`org_<uuid-hex>`, type `graphdata`. There is no grouping above it: every graph sits
side by side in the Redis keyspace (`db0`). A FalkorDB graph is closer to a whole
Postgres *database* than to a table.

On an org's **INSERT** CDC event, `organization_mapper` emits `GRAPH_CREATE`, and the
indexer provisions **one index per standard object in the schema — 182 of them**
(`create_graph_indexes` → `all_std_object_default_descriptors()`). Measured cost:

| | |
|---|---|
| per org graph | **~20 MB** (182 indexes; a live sample held 27 nodes) |
| Docker VM | ~10.5 GB → dies somewhere around 300–500 orgs |
| one integration test | **one org** — `random_organization` is function-scoped with no teardown |
| a bulk-update test file | 100+ orgs ≈ 2 GB |

So the cost is entirely in the graphs. The org rows in Postgres are kilobytes.
**Reap graphs; leave Postgres and Kafka alone.**

## Reap

```bash
bash $HOME/Desktop/code/mt-devkit/.claude/skills/falkor-cleanup/falkor_reap.sh [--dry-run] [--keep <org-uuid>]...
```

- Default keep-list is the local dev-seed org `00000000-0000-4000-a000-000000000001`.
  Passing `--keep` **replaces** that default; repeat the flag for several orgs.
- `--dry-run` lists what would go and deletes nothing. Use it whenever the keep-list
  isn't the default.
- Allowlist by **org id only**. Test orgs carry faker names (`Williams Group`) and
  blank names indistinguishable from real ones — never filter by name.
- Typical run: `242 → 1 graph(s), 4.81G → 32.96M` in about 6 seconds.

The script skips quietly when the daemon or container is down, so it is safe as an
unconditional step in a startup sequence.

## When to run it

**The window is after `d-up` and before `run-be`.** `make docker-start-dep` ends in
`docker compose ... up --detach --wait`, so when it returns FalkorDB is healthy — and
the CDC consumers, which are backend processes, are not up yet. Nothing is mid-write.

`env-manager`'s **run docker** row calls this as its final step. Run it standalone
after a heavy test sweep: daily cadence is not enough on a day with three integration
runs, since one file can add 2 GB.

Reaping while the backend is up is not corrupting, just untidy — an in-flight write
can implicitly recreate a graph (without its indexes, so ~0.4 MB). The script warns
if something is listening on `:8000`.

## Why the reap is durable

A deleted graph stays deleted. Nothing re-provisions it:

- `GRAPH_CREATE` fires **only** on an org's INSERT event, which is already consumed —
  the `falkor_fan_out` / `falkor_indexer` / `falkor_writer` groups sit at lag 0 with
  offsets at the log head, so a restart replays nothing.
- The Temporal `create_organization_graph_index_activity` needs the falkor workers,
  which `run-be` deliberately does not start.
- `index_all_organizations` has no callers.

Verified end to end: reap → `BGSAVE ok` → container restart → still 1 graph.

**This corrects the old rule's central claim.** "Pruning is not durable, the consumers
replay Kafka and rebuild" was true only while a large *unconsumed* backlog existed.
Once offsets are at the head, pruning holds — which is why the Postgres cascade delete,
replication-slot advance, and Debezium force-recreate are all unnecessary.

## When the reaper can't save you

**FalkorDB loads the whole dump into memory at container start.** If it is already
past the line, the load itself can OOM before the reaper gets a turn. Escape hatch —
delete the dump with the container stopped, then start clean:

```bash
docker stop salestech-be-salestech_be-falkordb-1
docker run --rm -v falkordb_data:/data alpine sh -c 'rm -f /data/dump.rdb /data/temp-*.rdb'
docker start salestech-be-salestech_be-falkordb-1
```

The volume is **`falkordb_data`**, not `salestech-be_falkordb_data` — the prefixed name
silently creates a new empty volume, so the fix "verifies" against nothing.

Afterwards the keep-org has no graph. Re-index it with the falkor Temporal workers
running (`run-be` does not start them):

```bash
uv run python -m salestech_be.temporal.workers.falkor --worker workflow &!
uv run python -m salestech_be.temporal.workers.falkor --worker activity &!
uv run python salestech_be/temporal/local_test_helpers/trigger_specific_organization_indexing.py \
  --organization-id 00000000-0000-4000-a000-000000000001
```

## The one case that needs a Kafka purge

Kafka retains 7 days (`log.retention.hours=168`) and the consumers use
`auto_offset_reset=EARLIEST`. If the backend stays off long enough for the consumer
groups' offsets to expire, they reset to earliest and **replay everything retained**,
recreating graphs wholesale. Rare. Recovery is a one-time purge of the CDC/falkor
topics (`debezium_server.salestech_be.change_events{,_v2}`,
`debezium.salestech_be.change_events_partitioned`,
`salestech_be.domain_change_events_v2`,
`salestech_be.falkor.{write_events,write_events_priority,index_events}`) via
`kafka-delete-records.sh --offset-json-file`, leaving `salestech_be.falkor.ci_test`
alone. `kafka-delete-records` moves the low watermark immediately; the log cleaner
reclaims disk later, so a still-large `du` is not a failed purge.

Do **not** reach for this routinely. It is the recovery path for a replay, not the
cleanup path — the reaper is the cleanup path.

## Diagnosis — reaching this skill from the symptoms

The chain never names Falkor until the end, which is why it costs a fresh
investigation every time. Any of these should land here:

- Accounts / contacts / opportunities pages empty though Postgres has the rows; a
  newly created record never appears.
- `redis.exceptions.BusyLoadingError`, or the falkor write consumer dying with
  `ConnectionError: Connection closed by server`.
- Temporal RPC timeouts (`GetTimerTasks operation failed`, `matching.Poll*TaskQueue`),
  `StartWorkflowExecution` hanging, chat `_connect` 500s, realtime `AGENT_TRIGGER_FAILED`.
- **Something unrelated dying** — `vite dev` killed with `Killed: 9` / exit 137, backend
  startup aborting. That is the *host* OOM killer; no `mem_limit` is set on the service,
  so the cgroup killer can't fire and `OOMKilled` reads `false`, proving nothing.

Three commands:

```bash
docker exec salestech-be-salestech_be-falkordb-1 redis-cli INFO memory | grep used_memory_human
docker exec salestech-be-salestech_be-falkordb-1 redis-cli GRAPH.LIST | grep -c .
docker exec salestech-be-salestech_be-db-1 psql -U salestech_be -d salestech_be -tAc "select count(*) from organization;"
```

Count graphs, never rows — a 23 MB `dump.rdb` on disk is perfectly consistent with a
9 GB resident set. If `GRAPH.LIST` hangs or resets the connection, the server is
thrashing; use the dump-deletion escape hatch above.

## Prevention (context, not steps)

The generator is that `salestech_be-db` is shared by profiles `[local-deps,
integration-tests, smoke-tests, usecase-tests]` with a single database
(`settings.db_base`) and no per-test DB, so every integration/usecase/smoke run seeds
orgs into the dev DB and CDC indexes each one. Real prevention is upstream (a separate
test database, or test teardown deleting its orgs so the existing `GRAPH_DELETE` path
fires). Until then this skill is the containment, and `local-test-scope.md` limits how
much gets generated.

Seed local with `spinup-local-db` (one synthetic org), never `populate-dev-data`
(a ~1000-org dev restore) — that alone is 20 GB of graphs.
