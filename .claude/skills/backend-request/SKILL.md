---
name: backend-request
description: Make authenticated HTTP requests to the Reevo backend from my personal harness — LOCAL (localhost:8000) by default, or the deployed DEV backend with `--dev`. Self-contained (no devkit) — reads user/org id from identity.json / identity.dev.json, mints + caches a short-lived JWT via `reevo token generate`, and sends Bearer + x-reevo-* headers. Local and dev only; prod is structurally unreachable. Use to call/verify a backend endpoint, replay a captured request, or benchmark endpoint latency. Triggers on "call the local API", "hit the backend endpoint", "call the dev API", "make a backend request", "replay this API request", "check this endpoint locally", "/backend-request".
allowed-tools: Bash, Read
---

# backend-request — authenticated API caller (local + dev)

Run `rcall.py` (in this skill's directory) to call the backend with auth handled for you.

```bash
python <this-skill-dir>/rcall.py GET  /api/v1/monitoring/health
python <this-skill-dir>/rcall.py POST /api/v1/some/endpoint --body '{"k": "v"}'
python <this-skill-dir>/rcall.py POST /api/v1/some/endpoint --body-file req.json --repeat 5
python <this-skill-dir>/rcall.py GET  /api/v1/items --query status=active --query limit=10

python <this-skill-dir>/rcall.py --dev GET /api/v1/flow/user_flow/list
python <this-skill-dir>/rcall.py --dev --write DELETE /api/v1/flow/user_flow/<id>
```

Response JSON → **stdout**; HTTP status + per-call timing + diagnostics → **stderr**. Big responses can bury the timing lines — send stdout to a file (`> resp.json`) to read the latency on stderr.

- `--body-file` for large payloads (avoids shell-quoting a big blob); `--body` for small inline JSON.
- `--repeat N` mints the token **once** and fires N timed calls, reporting `min | median | max` ms — use it to benchmark an endpoint.
- `--query KEY=VAL` (repeatable); `--skip-health-check` to skip the pre-flight `/monitoring/health` probe.

## Targets

| | local (default) | dev (`--dev`) |
|---|---|---|
| base URL | `http://localhost:8000` | `https://api-ng-private-dev.reevo.ai` |
| identity | `identity.json` | `identity.dev.json` |
| signing key | local dev default | `reevo-be-dev` chamber |
| token cache | `~/.claude/tmp/backend-request/token.json` | `…/token.dev.json` |
| prereqs | backend running locally | **Tailscale** + **chamber** + AWS SSO |

**The dev API host is the *private* one.** `api-ng-dev.reevo.ai` is a different ALB group (public webhook intake) and 404s every `/api` route; the API ingress is `api-ng-private-dev.reevo.ai`, restricted by security group to Tailscale / office / Vercel IPs.

## Auth — how it works
- **Identity** comes from `identity.json` (or `identity.dev.json` with `--dev`): `user_id`, `org_id`, `base_url`.
- It mints a short-lived (4 h) JWT via `uv run reevo --user-id .. --org-id .. token generate`, run in `salestech-be` (resolved from the current worktree, falling back to the primary checkout), **caches** it per target, and reuses it until ~30 s before expiry. It re-mints on expiry, on identity change, or after a `401` (which busts the cache).
- Sends `Authorization: Bearer <jwt>` + `x-reevo-user-id` / `x-reevo-org-id`. When a Bearer token is present the server uses it and ignores the headers; the headers are only a fallback for unauthenticated identity resolution. Token caches live outside the repo and are never committed.
- The CLI's default permission claim is `admin:*`, which clears the `require_*_access` gates. `--super-admin` is fingerprint-locked to the local E2E secret and is neither available nor needed for dev.

### What `--dev` actually swaps
Dev uses the **same symmetric HS256 scheme** as local — Auth0 is only the upstream login IdP, and the backend mints its own HS256 token afterwards. So a locally-minted token is valid on dev given the right inputs, read from the `reevo-be-dev` chamber namespace:

- `salestech_be_jwt_secret` — the signing key. **Must be passed via env**: the CLI's `--jwt-secret` flag is parsed but never applied (signing reads `settings.jwt_secret`).
- `salestech_be_jwt_issuer` / `salestech_be_jwt_audience` — `jwt.decode` validates `iss`/`aud`, so a mismatch is a hard reject. These *are* read from argv.
- `salestech_be_jwt_minimum_required_token_version` — `ReevoJWTClaims.version` defaults to the **client's** setting, and the server rejects `version <` its own minimum with `401 "token refresh required"`. Local defaults to 0, dev requires 1.
- `salestech_be_db_pass` + the dev Aurora host — minting reads the user's current `jwt_version` from the database and stamps it into the claim. It must read the **dev** DB (hence Tailscale); a token signed with the dev key but stamped from the local DB is a valid signature with the wrong `jwt_ver`, rejected as `401 "token has been invalidated"`.

## Change org / user
Edit the relevant identity file (change `user_id` **and** `org_id` together — the user must belong to the org). The cache re-mints automatically when the identity no longer matches.

## Guardrails
- **Host allowlist.** Local target accepts only `localhost` / `127.0.0.1` / `::1`; dev target accepts only `api-ng-private-dev.reevo.ai`. Any other host is refused, so **prod is structurally unreachable** — there is no flag that reaches it.
- **Writes on dev require `--write`.** Any non-GET method with `--dev` is refused without it. Dev is shared, real data that other people depend on — the flag is the deliberate pause.
- If the backend isn't up locally, the health check says so — start it via the `env-manager` skill (`run backend`). On dev, a failed health check usually means Tailscale is disconnected.
- If a chamber read fails with an SSO/credentials error, run `aws sso login` and retry.
