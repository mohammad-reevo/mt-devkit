"""Authenticated caller for the LOCAL Reevo backend (localhost only).

Reads the identity from identity.json (next to this file), mints a short-lived
JWT via `uv run reevo --user-id .. --org-id .. token generate`, caches it until
near expiry, and sends it as `Bearer` + `x-reevo-*` headers — the same local-dev
session override the frontend uses. Local-only by design: it refuses any
non-localhost base_url and has no signing key for dev/prod.

Self-contained (no devkit dependency; devkit's backend-request was reference only).

Usage:
    python rcall.py GET  /api/v1/monitoring/health
    python rcall.py POST /api/v1/some/endpoint --body '{"k": "v"}'
    python rcall.py POST /api/v1/some/endpoint --body-file req.json --repeat 5
    python rcall.py GET  /api/v1/items --query status=active --query limit=10

Response JSON -> stdout; HTTP status + timing + diagnostics -> stderr.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
IDENTITY = SKILL_DIR / "identity.json"
# SKILL_DIR = <root>/.claude/skills/backend-request  ->  parents[2] = <root>
_ROOT = SKILL_DIR.parents[2]
_PRIMARY_BE = Path("/Users/mohammad/Desktop/code/mt-devkit/salestech-be")
_CACHE = Path.home() / ".claude" / "tmp" / "backend-request" / "token.json"
_JWT = re.compile(r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$")
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def load_identity() -> dict:
    if not IDENTITY.exists():
        sys.exit(f"identity.json not found at {IDENTITY}")
    cfg = json.loads(IDENTITY.read_text())
    for key in ("user_id", "org_id"):
        if not cfg.get(key):
            sys.exit(f"identity.json is missing '{key}'")
    cfg.setdefault("base_url", "http://localhost:8000")
    return cfg


def backend_dir() -> Path:
    """salestech-be used only to mint a token (local signing key is shared)."""
    for cand in (_ROOT / "salestech-be", _PRIMARY_BE):
        if (cand / "pyproject.toml").exists():
            return cand
    sys.exit("could not locate salestech-be to mint a token")


def _jwt_exp(token: str) -> float | None:
    parts = token.split(".")
    if len(parts) != 3:
        return None
    payload = parts[1] + "=" * (-len(parts[1]) % 4)
    try:
        return json.loads(base64.urlsafe_b64decode(payload)).get("exp")
    except Exception:
        return None


def _expired(token: str) -> bool:
    exp = _jwt_exp(token)
    # 30s buffer; no exp claim -> treat as usable (mirrors devkit behavior).
    return exp is not None and time.time() > (exp - 30)


def _mint(user_id: str, org_id: str) -> str:
    cmd = ["uv", "run", "reevo", "--user-id", user_id, "--org-id", org_id, "token", "generate"]
    print(f"minting token: {' '.join(cmd[2:])}", file=sys.stderr)
    result = subprocess.run(
        cmd, cwd=backend_dir(), capture_output=True, text=True, timeout=120, check=False
    )
    if result.returncode != 0:
        sys.exit(f"`reevo token generate` failed (exit {result.returncode}):\n{result.stderr.strip()}")
    for line in reversed([ln.strip() for ln in result.stdout.splitlines() if ln.strip()]):
        if _JWT.match(line):
            return line
    sys.exit("could not parse a JWT from `reevo token generate` output")


def get_token(user_id: str, org_id: str) -> str:
    """Cached JWT: reuse until ~30s before expiry; re-mint on expiry or identity change."""
    if _CACHE.exists():
        try:
            cached = json.loads(_CACHE.read_text())
            if (
                cached.get("user_id") == user_id
                and cached.get("org_id") == org_id
                and cached.get("token")
                and not _expired(cached["token"])
            ):
                return cached["token"]
        except Exception:
            pass  # Legit business flow: a corrupt/absent cache just means we mint fresh.
    token = _mint(user_id, org_id)
    _CACHE.parent.mkdir(parents=True, exist_ok=True)
    _CACHE.write_text(json.dumps({"user_id": user_id, "org_id": org_id, "token": token}))
    return token


def health(base: str) -> bool:
    try:
        with urllib.request.urlopen(f"{base}/api/v1/monitoring/health", timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False


def main() -> None:
    ap = argparse.ArgumentParser(description="Authenticated LOCAL Reevo backend caller")
    ap.add_argument("method", choices=["GET", "POST", "PUT", "PATCH", "DELETE"])
    ap.add_argument("path", help="API path, e.g. /api/v1/users")
    ap.add_argument("--body", help="inline JSON body")
    ap.add_argument("--body-file", help="path to a JSON body file (for large payloads)")
    ap.add_argument("--query", action="append", metavar="KEY=VAL", help="repeatable")
    ap.add_argument("--repeat", type=int, default=1, help="timed calls; token minted once")
    ap.add_argument("--skip-health-check", action="store_true")
    args = ap.parse_args()

    if not args.path.startswith("/api/"):
        sys.exit(f"path should start with /api/ (got '{args.path}')")

    cfg = load_identity()
    base = cfg["base_url"].rstrip("/")
    host = urllib.parse.urlparse(base).hostname or ""
    if host not in _LOCAL_HOSTS:
        sys.exit(f"refusing non-local base_url '{base}' — this skill is local-only")

    token = get_token(cfg["user_id"], cfg["org_id"])
    headers = {
        "Authorization": f"Bearer {token}",
        "x-reevo-user-id": cfg["user_id"],
        "x-reevo-org-id": cfg["org_id"],
        "Content-Type": "application/json",
    }

    if not args.skip_health_check and not health(base):
        sys.exit(f"backend not reachable at {base} — is it running? (start it via env-manager)")

    url = f"{base}{args.path}"
    if args.query:
        pairs = []
        for q in args.query:
            if "=" not in q:
                sys.exit(f"invalid --query (want KEY=VAL): {q}")
            pairs.append(tuple(q.split("=", 1)))
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(pairs)

    data = None
    if args.body_file:
        data = Path(args.body_file).read_bytes()
    elif args.body:
        json.loads(args.body)  # validate JSON before sending
        data = args.body.encode()

    latencies: list[float] = []
    body = ""
    status = 0
    for i in range(args.repeat):
        req = urllib.request.Request(url, data=data, headers=headers, method=args.method)
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = resp.read().decode()
                status = resp.status
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            status = e.code
        except urllib.error.URLError as e:
            sys.exit(f"connection failed: {e.reason}")
        elapsed_ms = (time.perf_counter() - started) * 1000
        latencies.append(elapsed_ms)
        print(f"  call {i + 1}/{args.repeat}: HTTP {status}  {elapsed_ms:.0f} ms", file=sys.stderr)

    if args.repeat > 1:
        print(
            f"latency ms -> min {min(latencies):.0f} | "
            f"median {statistics.median(latencies):.0f} | max {max(latencies):.0f}",
            file=sys.stderr,
        )
    if status == 401:
        print("HTTP 401 — token rejected; clearing cache so the next call re-mints.", file=sys.stderr)
        _CACHE.unlink(missing_ok=True)

    try:
        print(json.dumps(json.loads(body), indent=2))
    except json.JSONDecodeError:
        print(body)


if __name__ == "__main__":
    main()
