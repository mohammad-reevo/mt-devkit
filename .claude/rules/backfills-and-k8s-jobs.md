# Backfills and K8s one-off jobs: ask before every run

## When to Apply
Running a backfill or data-migration script (e.g. salestech-be `scripts/gha_workflows/*`), or
triggering the "Run K8s One-Off Job" workflow (`gh workflow run "Run K8s One-Off Job"`,
`run-k8s-job.yml`) in any environment.

## Rule
- **Dry run first, always.** Summarize what it would do (counts, skipped or unmappable rows),
  then stop. Never `--execute` — local, dev or prod — without my explicit go for that run.
- **A K8s one-off job always needs my go first** — dev or prod, dry run or not. Propose the exact
  command (env, ref, entrypoint, memory) and wait. The workflow's `confirm_prod` input is not my
  approval; never fill it in on your own.
- **Approval covers only the run it was given for**: local ≠ dev ≠ prod, dry run ≠ execute, and an
  earlier go never carries over. A local dry run against the local DB needs no go.

## Why
On 2026-11-02 an agent triggered a prod `--all-orgs` dry run on its own. It was read-only, but an
unexpected prod job is alarming whatever it does, and a script without a dry-run default would
have written to prod.

This applies across all sessions working in this workspace.
