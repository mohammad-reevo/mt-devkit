"""Authenticated caller for the Reevo backend — LOCAL by default, dev with --dev.

Reads the identity from identity.json (or identity.dev.json with --dev), mints a
short-lived JWT via `uv run reevo --user-id .. --org-id .. token generate`, caches
it until near expiry, and sends it as `Bearer` + `x-reevo-*` headers.

Two targets, allowlisted by host — prod is structurally unreachable:
  * local (default): localhost/127.0.0.1, signed with the local dev key.
  * dev (--dev): https://api-ng-private-dev.reevo.ai, signed with the dev key read from
    the `reevo-be-dev` chamber namespace. Requires Tailscale + AWS SSO, because
    minting reads the user's current `jwt_version` from the dev database.

Self-contained (no devkit dependency; devkit's backend-request was reference only).

Usage:
    python rcall.py GET  /api/v1/monitoring/health
    python rcall.py POST /api/v1/some/endpoint --body '{"k": "v"}'
    python rcall.py POST /api/v1/some/endpoint --body-file req.json --repeat 5
    python rcall.py GET  /api/v1/items --query status=active --query limit=10
    python rcall.py --dev GET /api/v1/flow/user_flow
    python rcall.py --dev --write DELETE /api/v1/flow/user_flow/<id>

Response JSON -> stdout; HTTP status + timing + diagnostics -> stderr.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
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
IDENTITY_DEV = SKILL_DIR / "identity.dev.json"
# SKILL_DIR = <root>/.claude/skills/backend-request  ->  parents[2] = <root>
_ROOT = SKILL_DIR.parents[2]
_PRIMARY_BE = Path("/Users/mohammad/Desktop/code/mt-devkit/salestech-be")
_CACHE_DIR = Path.home() / ".claude" / "tmp" / "backend-request"
_JWT = re.compile(r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$")

_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
# The dev API ingress is the PRIVATE host, restricted by security group to
# Tailscale / office / Vercel IPs. api-ng-dev.reevo.ai is a different ALB group
# (public webhook intake) and 404s every /api route.
_DEV_HOSTS = {"api-ng-private-dev.reevo.ai"}

# Chamber namespace holding the dev signing key and dev DB password.
_CHAMBER_NS = "reevo-be-dev"

# Minting against dev must read `user.jwt_version` from the DEV database — a token
# signed with the dev key but stamped from the local DB yields a valid signature
# with the wrong jwt_ver, which the server rejects as 401 "token invalidated".
_DEV_DB_ENV = {
    "SALESTECH_BE_DB_HOST": (
        "reevo-dev-v2-aurora-rds.cluster-cjg208q4q0s8.us-west-2.rds.amazonaws.com"
    ),
    "SALESTECH_BE_DB_PORT": "5432",
    "SALESTECH_BE_DB_BASE": "reevo_main",
    "SALESTECH_BE_DB_USER": "reevo_db_user",
}


def load_identity(dev: bool) -> dict:
    path = IDENTITY_DEV if dev else IDENTITY
    if not path.exists():
        sys.exit(f"{path.name} not found at {path}")
    cfg = json.loads(path.read_text())
    for key in ("user_id", "org_id"):
        if not cfg.get(key):
            sys.exit(f"{path.name} is missing '{key}'")
    cfg.setdefault(
        "base_url", "https://api-ng-private-dev.reevo.ai" if dev else "http://localhost:8000"
    )
    return cfg


def backend_dir() -> Path:
    """salestech-be is used only to run the token-minting CLI."""
    for cand in (_ROOT / "salestech-be", _PRIMARY_BE):
        if (cand / "pyproject.toml").exists():
            return cand
    sys.exit("could not locate salestech-be to mint a token")


def _chamber(key: str) -> str:
    """Read one value from the dev chamber namespace. Values are never printed."""
    result = subprocess.run(
        ["chamber", "read", _CHAMBER_NS, key, "-q"],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if result.returncode != 0:
        sys.exit(
            f"chamber read {_CHAMBER_NS}/{key} failed (exit {result.returncode}):\n"
            f"{result.stderr.strip()}\n"
            "If this is an SSO/credentials error, run `aws sso login` and retry."
        )
    value = result.stdout.strip()
    if not value:
        sys.exit(f"chamber read {_CHAMBER_NS}/{key} returned an empty value")
    return value


def dev_mint_env() -> dict[str, str]:
    """Environment for minting a dev-valid token.

    The CLI's --jwt-secret flag is parsed but never applied (signing reads
    settings.jwt_secret), so the secret must arrive through the environment.
    """
    env = dict(os.environ)
    env.update(_DEV_DB_ENV)
    env["SALESTECH_BE_JWT_SECRET"] = _chamber("salestech_be_jwt_secret")
    env["SALESTECH_BE_JWT_ISSUER"] = _chamber("salestech_be_jwt_issuer")
    env["SALESTECH_BE_JWT_AUDIENCE"] = _chamber("salestech_be_jwt_audience")
    # ReevoJWTClaims.version defaults to the CLIENT's setting (types.py:88), while the
    # server rejects `version < settings.jwt_minimum_required_token_version` as
    # "token refresh required". Local defaults to 0, dev requires 1 — so mint with dev's.
    env["SALESTECH_BE_JWT_MINIMUM_REQUIRED_TOKEN_VERSION"] = _chamber(
        "salestech_be_jwt_minimum_required_token_version"
    )
    env["SALESTECH_BE_DB_PASS"] = os.environ.get("DB_PASSWORD") or _chamber(
        "salestech_be_db_pass"
    )
    return env


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


def _mint(user_id: str, org_id: str, dev: bool) -> str:
    cmd = ["uv", "run", "reevo", "--user-id", user_id, "--org-id", org_id]
    env = None
    if dev:
        env = dev_mint_env()
        # generate_jwt reads iss/aud from argv, not from settings.
        cmd += [
            "--jwt-issuer",
            env["SALESTECH_BE_JWT_ISSUER"],
            "--jwt-audience",
            env["SALESTECH_BE_JWT_AUDIENCE"],
        ]
    cmd += ["token", "generate"]
    target = "dev" if dev else "local"
    print(f"minting {target} token for user {user_id} org {org_id}", file=sys.stderr)
    result = subprocess.run(
        cmd, cwd=backend_dir(), capture_output=True, text=True, timeout=180, check=False, env=env
    )
    if result.returncode != 0:
        hint = ""
        if dev:
            hint = "\nDev minting needs Tailscale (to reach the dev DB) and `aws sso login`."
        sys.exit(
            f"`reevo token generate` failed (exit {result.returncode}):\n"
            f"{result.stderr.strip()}{hint}"
        )
    for line in reversed([ln.strip() for ln in result.stdout.splitlines() if ln.strip()]):
        if _JWT.match(line):
            return line
    sys.exit("could not parse a JWT from `reevo token generate` output")


def cache_path(dev: bool) -> Path:
    """Separate cache per target — a local-signed token must never reach dev."""
    return _CACHE_DIR / ("token.dev.json" if dev else "token.json")


def get_token(user_id: str, org_id: str, dev: bool) -> str:
    """Cached JWT: reuse until ~30s before expiry; re-mint on expiry or identity change."""
    cache = cache_path(dev)
    if cache.exists():
        try:
            cached = json.loads(cache.read_text())
            if (
                cached.get("user_id") == user_id
                and cached.get("org_id") == org_id
                and cached.get("token")
                and not _expired(cached["token"])
            ):
                return cached["token"]
        except Exception:
            pass  # Legit business flow: a corrupt/absent cache just means we mint fresh.
    token = _mint(user_id, org_id, dev)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"user_id": user_id, "org_id": org_id, "token": token}))
    return token


def health(base: str) -> bool:
    try:
        with urllib.request.urlopen(f"{base}/api/v1/monitoring/health", timeout=10) as resp:
            return resp.status == 200
    except Exception:
        return False


def main() -> None:
    ap = argparse.ArgumentParser(description="Authenticated Reevo backend caller")
    ap.add_argument("method", choices=["GET", "POST", "PUT", "PATCH", "DELETE"])
    ap.add_argument("path", help="API path, e.g. /api/v1/users")
    ap.add_argument("--dev", action="store_true", help="target the deployed dev backend")
    ap.add_argument(
        "--write",
        action="store_true",
        help="required on --dev for any non-GET method (dev is shared, real data)",
    )
    ap.add_argument("--body", help="inline JSON body")
    ap.add_argument("--body-file", help="path to a JSON body file (for large payloads)")
    ap.add_argument("--query", action="append", metavar="KEY=VAL", help="repeatable")
    ap.add_argument("--repeat", type=int, default=1, help="timed calls; token minted once")
    ap.add_argument("--skip-health-check", action="store_true")
    args = ap.parse_args()

    if not args.path.startswith("/api/"):
        sys.exit(f"path should start with /api/ (got '{args.path}')")

    cfg = load_identity(args.dev)
    base = cfg["base_url"].rstrip("/")
    host = urllib.parse.urlparse(base).hostname or ""
    allowed = _DEV_HOSTS if args.dev else _LOCAL_HOSTS
    if host not in allowed:
        target = "dev" if args.dev else "local"
        sys.exit(
            f"refusing base_url '{base}' — {target} target allows only "
            f"{sorted(allowed)}. This skill reaches local and dev only, never prod."
        )

    if args.dev and args.method != "GET" and not args.write:
        sys.exit(
            f"refusing {args.method} on dev without --write — dev is shared data. "
            "Re-run with --write once you're sure."
        )

    token = get_token(cfg["user_id"], cfg["org_id"], args.dev)
    headers = {
        "Authorization": f"Bearer {token}",
        "x-reevo-user-id": cfg["user_id"],
        "x-reevo-org-id": cfg["org_id"],
        "Content-Type": "application/json",
    }

    if not args.skip_health_check and not health(base):
        hint = (
            "check Tailscale / the dev deployment"
            if args.dev
            else "is it running? (start it via env-manager)"
        )
        sys.exit(f"backend not reachable at {base} — {hint}")

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
        cache_path(args.dev).unlink(missing_ok=True)

    try:
        print(json.dumps(json.loads(body), indent=2))
    except json.JSONDecodeError:
        print(body)


if __name__ == "__main__":
    main()
