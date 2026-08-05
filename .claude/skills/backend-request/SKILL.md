---
name: backend-request
description: Make authenticated HTTP requests to the LOCAL Reevo backend (localhost:8000) from my personal harness. Self-contained (no devkit) — reads user/org id from identity.json, mints + caches a short-lived JWT via `reevo token generate`, and sends Bearer + x-reevo-* headers (the same local-dev session override the frontend uses). Local-only (refuses non-localhost). Use to call/verify a backend endpoint, replay a captured request, or benchmark endpoint latency. Triggers on "call the local API", "hit the backend endpoint", "make a backend request", "replay this API request", "check this endpoint locally", "/backend-request".
allowed-tools: Bash, Read
---

# backend-request — authenticated local API caller

Run `rcall.py` (in this skill's directory) to call the local backend with auth handled for you.

```bash
python <this-skill-dir>/rcall.py GET  /api/v1/monitoring/health
python <this-skill-dir>/rcall.py POST /api/v1/some/endpoint --body '{"k": "v"}'
python <this-skill-dir>/rcall.py POST /api/v1/some/endpoint --body-file req.json --repeat 5
python <this-skill-dir>/rcall.py GET  /api/v1/items --query status=active --query limit=10
```

Response JSON → **stdout**; HTTP status + per-call timing + diagnostics → **stderr**. Big responses can bury the timing lines — send stdout to a file (`> resp.json`) to read the latency on stderr.

- `--body-file` for large payloads (avoids shell-quoting a big blob); `--body` for small inline JSON.
- `--repeat N` mints the token **once** and fires N timed calls, reporting `min | median | max` ms — use it to benchmark an endpoint.
- `--query KEY=VAL` (repeatable); `--skip-health-check` to skip the pre-flight `/monitoring/health` probe.

## Auth — how it works
- **Identity** comes from `identity.json` in this directory: `user_id`, `org_id`, `base_url`.
- It mints a short-lived JWT via `uv run reevo --user-id .. --org-id .. token generate` (run in `salestech-be` — resolved from the current worktree, falling back to the primary checkout; the local JWT signing key is shared across checkouts), **caches** it at `~/.claude/tmp/backend-request/token.json`, and reuses it until ~30 s before expiry. It re-mints on expiry, on identity change, or after a `401` (which busts the cache).
- Sends `Authorization: Bearer <jwt>` + `x-reevo-user-id` / `x-reevo-org-id` — the same local-dev session override the frontend uses. The token cache lives outside the repo and is never committed.

## Change org / user
Edit `identity.json` (change `user_id` **and** `org_id` together — the user must belong to the org). The cache re-mints automatically when the identity no longer matches.

## Local-only, by design
Refuses any `base_url` that isn't `localhost` / `127.0.0.1`. This has **no** signing key for dev/prod and is not a path to reach them. If the backend isn't up, the health check says so — start it via the `env-manager` skill (`run backend`).
