# Local Service Logs

## When to Apply
When the user reports an error in a locally running service ("we got an error", a 500, a crash, a stack trace) or when debugging local runtime behavior. Check the logs FIRST — before re-running services or speculating about the cause.

## Where Logs Live
Every repo writes its local service logs to a `logs/` directory at the repo root. The `env-manager` skill creates these when starting services.

| Location | File | Process |
|---|---|---|
| `salestech-be/logs/` | `backend_logs.txt` | API server (localhost:8000) |
| | `integrity_job_logs.txt`, `chat_worker_logs.txt` | Temporal workers |
| | `flow-engine-worker.log` | Flow engine worker |
| | `cdc-*.log` | CDC consumers (debezium mapper, partitioner, flow change) |
| | `falkor-*.log` | Falkor CDC event consumers (cdc / index / write) |
| | `falkor_workflow_logs.txt`, `falkor_activity_logs.txt` | Falkor temporal workers (manually started only) |
| `frontend-monorepo/logs/` | `frontend_logs.txt` | Next.js webapp (localhost:3000) |
| `reevo-realtime/logs/` | `dev.log` | PartyKit realtime server (:8787) |

The authoritative process → log mapping is in the `env-manager` skill — consult it if a file listed here doesn't match what's on disk.

## How to Check
- Start with the log of the service the error points at. If unclear which service, `ls -lt <repo>/logs/` and look at the most recently modified files.
- Logs append across restarts and get large — never read a whole log file. Use `tail -n 200` and `grep` for `Traceback`, `ERROR`, `Exception` around the reported time.
- An error surfacing in the frontend is often caused by the backend — if `frontend_logs.txt` shows a failed API call, follow it into `salestech-be/logs/backend_logs.txt`.
