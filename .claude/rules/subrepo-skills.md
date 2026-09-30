# Sub-repo skills worth using

## When to Apply
Scoping, planning, or implementing salestech-be work. Sessions run from the mt-devkit root, so
Claude Code never loads salestech-be's skills on its own. When one below fits the work, read its
`salestech-be/.claude/skills/<name>/SKILL.md` and follow it; a plan task names it in `Follows:`.

## salestech-be (last updated 2026-09-30)
- `flow-trigger-create` — new workflow trigger event: payload, UI filter conditions, registration.
- `flow-verify-trigger` — checks a trigger has all its files, config, registrations, and tests.
- `flow-node-create` — new customer-facing workflow node: config + UI rendering, executor, wiring.
- `flow-verify-node` — checks a node has all its files, config, registrations, and tests.
- `flow-node-agent-create` — new Flow Builder node agent: signature, examples, registration, training.
- `flow-node-agent-ship` — build, train, audit, and ship a node agent end to end.
- `flow-template-create` — new workflow template, from a flow saved in dev or from scratch.
- `create-or-modify-api` — house conventions for any change under `salestech_be/web/api/`.
- `create-or-modify-service` — house conventions for creating or changing a `salestech_be/core/` service.
- `add-domain-model-field` — adding fields or nested types to ContactV2, AccountV2, etc.
- `reporting-field-replication` — whether a new domain-model field replicates to reporting.
- `temporal-workflow-patching` — required for any edit under `temporal/workflows/` (replay safety).
- `sequence-step-type-create` — new sequence step type: enums, content, dispatch, schema, registration.
- `clean-feature-flag` — removing a fully rolled-out flag: enum entry, checks, branches, test mocks.
- `writing-unit-tests` — house conventions for unit tests.
- `writing-integration-tests` — house conventions for repository, service, and endpoint integration tests.
- `cleanup-flow-db` — finds and fixes corrupt flow definitions in dev or prod.
- `temporal-debug` — read-only investigation of Temporal workflow failures and timeouts.
- `investigate-prod` — starting point for a prod issue spanning Sentry, Langfuse, Temporal, Datadog, Postgres.
- `linearize-migrations` — fixes Alembic migration-chain conflicts on merge.

Every other salestech-be skill was triaged out: `.claude/references/subrepo-skills-unused.md`.
Assimilation Harness skills are governed by `assimilation-harness.md`.

This applies across all sessions working in this workspace.
