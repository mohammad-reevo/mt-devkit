# Sub-repo skills worth using

## When to Apply
Scoping, planning, or implementing salestech-be or frontend-monorepo work. Sessions run from the
mt-devkit root, so Claude Code never loads the sub-repos' skills on its own. When one below fits the
work, read its `<repo>/.claude/skills/<name>/SKILL.md` and follow it; a plan task names it in `Follows:`.

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

## frontend-monorepo (last updated 2026-09-30)
- `flow-verify-node` — checks a workflow node is complete on the FE: registration, fields, run details, rendering.
- `flow-verify-trigger` — checks a workflow trigger is complete on the FE: event registration, records, fields, rendering.
- `using-ui-new` — building or changing CRM UI with `@reevoai/ui-new`: package access, design opinions, gap escalation.
- `using-design-system` — tokens, typography, components, and icons; the positive side of `frontend-no-hardcoded-colors.md`.
- `react-component-patterns` — house conventions for component size, composition, hooks, and TypeScript.
- `page-implementation` — new settings, list, detail, or simple pages: auth, breadcrumbs, layout.
- `object-view-schema` — the CRM field schema system; required when touching field rendering, editing, or filtering.
- `form-with-validation` — forms with React Hook Form + Zod.
- `modal-pattern` — modal dialogs via `useModal`.
- `sheet-pattern` — slide-in side panels via `showSheet` / `hideSheet`.
- `alert-pattern` — confirmation dialogs for destructive actions.
- `api-client-patterns` — house way to use the React Query hooks and service calls: pagination, filters, `record_id`.
- `add-resource-mapping` — resource mappings + cache-invalidation hooks for an endpoint (pairs with `openapi-regen.md`).
- `state-management` — picks Zustand, Context, nuqs, or React Query for a feature's state.
- `url-state-nuqs` — shareable page state (tabs, filters, view modes) in the URL.
- `query-polling` — polling via `refetchInterval`, or job tracking via `useJobPollingStore`.
- `feature-flag-setup` — a new flag end to end: PostHog config, enum, gating, sidebar entry.
- `cleanup-feature-flag` — removing a rolled-out flag and the dead code behind it.
- `analytics-instrumentation` — wiring tracking into components: one-shot guards, debouncing, mutation-success timing.
- `unit-tests` — house guidance for unit tests.

Every other sub-repo skill was triaged out: `.claude/references/subrepo-skills-unused.md`.
Assimilation Harness skills are governed by `assimilation-harness.md`.

This applies across all sessions working in this workspace.
