# Regenerate the OpenAPI client after backend API changes

## When to Apply
After any backend API change — a new or changed endpoint, a schema/model
change, or an altered request/response shape. The usual trigger moment is a
merge to `main` that touches the API, or just before frontend work that will
consume the changed endpoint.

## Rule

Keep the frontend in sync with the backend contract by regenerating in two
steps, backend first:

1. **Backend spec** — regenerate `openapi.json` from the backend routes/models
   via env-manager's *"generate backend openapi spec"* (alias `gen-be` →
   `uv run generate_openapi.py`, run in `salestech-be/`). Commit the updated
   `salestech-be/openapi.json` as part of the normal backend flow.
2. **Frontend client** — regenerate the typed client from a live backend via
   env-manager's *"generate frontend openapi spec"* (alias `gen-fe` →
   `pnpm generate-openapi-client:local`, run in `frontend-monorepo/`). This
   emits the generated client under
   `frontend-monorepo/packages/openapi-client/generated/`.

## Never hand-push the generated frontend client

The generated files under
`frontend-monorepo/packages/openapi-client/generated/` are **regenerated
locally, never hand-edited and never included as a diff in a push**. They are
produced from whatever backend is running locally, so pushing them from a
feature branch leaks in-flight backend state into frontend history and breaks
the API contract for unrelated frontend PRs that merge first.

- **Local regen is fine** — regenerating to type-check against an in-flight
  backend change, and committing locally for your own history, is the common
  case. Just don't include the generated files in a push. If `git add -A` would
  stage them, unstage with
  `git restore --staged packages/openapi-client/generated/`.
- **Rare exception:** pushing a regen in fast succession *after* a backend
  change has already merged and deployed. Surface it in conversation first and
  wait for explicit approval — never push generated openapi files silently.

The backend spec (`salestech-be/openapi.json`) is out of scope for this
restriction — that file is regenerated and committed as part of the normal
backend flow.

This applies across all repositories and projects.
