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
   `frontend-monorepo/packages/openapi-client/client/` — **not** `generated/`,
   which holds only the gitignored fetched spec and `urlToHookMapping.json`.

## Push the source, never the generated client

**The hand-written frontend code is committed and pushed as normal** — a cross-repo
change is not a reason to hold the branch back. Only the regenerated client is held
back. Stage by path (`git add <source paths>`), never `git add -A`, and confirm the
generated set is absent from what you're about to push:

```bash
git diff --name-only origin/main...HEAD -- \
  'packages/openapi-client/client/*.gen.ts' \
  'packages/openapi-client/client/services/' \
  'packages/openapi-client/client/core/' \
  'packages/openapi-client/client/clientFetch/' \
  'packages/openapi-client/client/@tanstack/services/' \
  'packages/openapi-client/client/@tanstack/createApiClient.ts' \
  'packages/openapi-client/generated/urlToHookMapping.json'
```

Empty output means the push is clean. Don't widen it to `-- packages/openapi-client`:
`client/serverClient.ts`, `client/resourceMapping.ts` and most of `client/@tanstack/`
are hand-authored and are often exactly what you *are* pushing.

**Pushing is not merging.** `openapi-input-output-model-split.md` describes a real
deadlock — the backend can't merge until the deployed frontend tolerates the change,
and the frontend client can't be regenerated until the backend deploys. That deadlock
governs **merge order** only. It does not stop either side being committed, pushed, or
opened as a PR. Fusing the two into "the branch can't move at all" strands finished,
reviewable work in a worktree working tree — where `/done` destroys it on teardown —
and reports the PR as stalled when it isn't.

The frontend PR's `type-check` stays red until the backend merges and deploys. That is
the expected mechanism (see the last paragraph of this file), not a reason to withhold
the push.

The generated files under `frontend-monorepo/packages/openapi-client/` are
**regenerated locally, never hand-edited and never included as a diff in a
push**. They are produced from whatever backend is running locally, so pushing
them from a feature branch leaks in-flight backend state into frontend history
and breaks the API contract for unrelated frontend PRs that merge first.

- **Local regen is fine** — regenerating to type-check against an in-flight
  backend change, and committing locally for your own history, is the common
  case. Just don't include the generated files in a push. **`client/` mixes
  generated and hand-authored code**, so there is no single directory to
  unstage — the generated set is `client/*.gen.ts`, `client/services/`,
  `client/core/`, `client/clientFetch/`, `client/@tanstack/services/`,
  `client/@tanstack/createApiClient.ts`, and `generated/urlToHookMapping.json`,
  while `client/serverClient.ts`, `client/resourceMapping.ts` and the rest of
  `client/@tanstack/` are hand-authored and may be part of your actual change.
  Read `git status --short packages/openapi-client/` and unstage only what the
  regen wrote.
- **Rare exception:** pushing a regen in fast succession *after* a backend
  change has already merged and deployed. Surface it in conversation first and
  wait for explicit approval — never push generated openapi files silently.

The backend spec (`salestech-be/openapi.json`) is out of scope for this
restriction — that file is regenerated and committed as part of the normal
backend flow.

## Generating against a backend branch that isn't deployed yet

The common cross-repo case: the frontend PR needs a type the backend added on a
branch that hasn't merged, let alone deployed. `gen-fe` does not work for this,
for a reason its error message actively hides.

**Why `gen-fe` 404s against a local backend.** `generate-openapi-client:local`
points at `http://localhost:8000/api/openapi.json`, but the local app is built
by `get_app()` with `enable_api_docs=False` (the default), which passes
`openapi_url=None` to FastAPI — the route does not exist. The failure prints
"ensure your backend is running on http://localhost:8000", which sends you
hunting a backend that is up and healthy.

**The recipe.** It needs no running backend at all — `generate_openapi.py`
builds the app in-process and writes the spec to a file.

1. Regenerate the backend spec on your branch (normal backend flow, `gen-be`):
   ```bash
   cd <worktree>/salestech-be && uv run generate_openapi.py
   ```
2. Serve that file over HTTP — this is the step that works around the 404:
   ```bash
   python3 -m http.server 8899 --directory <worktree>/salestech-be
   ```
   Start it **before** step 3 and confirm it answers. `validateApiEndpoint.ts`
   treats a connection error as retryable and backs off 5, 10, then 15 minutes,
   so a not-yet-started server or a typo'd port hangs for half an hour rather
   than failing. (A 404 is non-retryable and aborts at once.)
3. Generate the client against it, overriding the URL the alias hardcodes:
   ```bash
   cd <worktree>/frontend-monorepo/packages/openapi-client
   OPENAPI_URL=http://localhost:8899/openapi.json pnpm run generate-react-query-openapi-client
   ```
   `gen-fe` is `cross-env OPENAPI_URL=... generate-react-query-openapi-client`,
   so the base script honours whatever `OPENAPI_URL` you set. Kill the static
   server afterwards.
4. Write the frontend PR against the regenerated types. Commit and push the
   hand-written source as normal; leave only the regenerated client dirty — it is
   tracked, so the push rule above still applies.

**Don't hand-write or widen the type instead.** Reaching for a local
`SomeGeneratedType & { new_prop?: ... }` on the theory that a regen would drag
in every backend change since the last one is usually wrong: when FE `main` has
a recent client regen and the backend branch is `main` plus your change, the
regen delta *is* your change. Measure it before assuming —
`git diff --stat packages/openapi-client/`.

**Expect the frontend PR's `type-check` to be red until FE `main` has the new
client.** That is the mechanism, not a failure to fix: it clears once the
backend merges and deploys and the client regen lands on FE `main`, after which
merging `main` into the frontend branch turns it green.

This applies across all repositories and projects.
