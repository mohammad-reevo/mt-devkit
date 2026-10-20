"""Authenticated caller for the Reevo backend — LOCAL by default, dev with --dev.

Reads the identity from identity.json (or identity.dev.json with --dev), mints a
short-lived JWT via `uv run reevo --user-id .. --org-id .. token generate`, caches
it until near expiry, and sends it as `Bearer` + `x-reevo-*` headers.

Three targets, allowlisted by host — prod is structurally unreachable:
  * local (default): localhost/127.0.0.1, signed with the local dev key.
  * stack (--stack [--worktree <name>]): a numbered `local-stack` backend on localhost:8000+slot,
    as that stack's pool-org admin. Port and org come from salestech-be's instance
    registry; the token from `seed_dev_data --token`, the same one `local-stack up`
    writes for the stack's frontend. No identity file.
  * dev (--dev): https://api-ng-private-dev.reevo.ai, signed with the dev key read via
    chamber from the dev-v2 AWS account. Requires Tailscale + AWS SSO, because
    minting reads the user's current `jwt_version` from the dev database.

Self-contained (no devkit dependency; devkit's backend-request was reference only).

Usage:
    python rcall.py GET  /api/v1/monitoring/health
    python rcall.py POST /api/v1/some/endpoint --body '{"k": "v"}'
    python rcall.py POST /api/v1/some/endpoint --body-file req.json --repeat 5
    python rcall.py GET  /api/v1/items --query status=active --query limit=10
    python rcall.py --stack GET /api/v1/monitoring/health
    python rcall.py --stack --worktree my-worktree POST /api/v1/some/endpoint --body '{"k": "v"}'
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

# Dev secrets live in the dev-v2 AWS account; the shell's default profile holds prod keys
# only. Plain config (JWT issuer/audience/min version, DB user) sits in `reevo-be-dev`,
# secrets (JWT signing key, DB password) in `secrets-reevo-be-dev`.
_AWS_PROFILE = "dev-v2"
_CHAMBER_NS = "reevo-be-dev"
_CHAMBER_SECRETS_NS = "secrets-reevo-be-dev"

# Minting against dev must read `user.jwt_version` from the DEV database — a token
# signed with the dev key but stamped from the local DB yields a valid signature
# with the wrong jwt_ver, which the server rejects as 401 "token invalidated".
_DEV_DB_ENV = {
    "SALESTECH_BE_DB_HOST": (
        "reevo-dev-v2-aurora-rds.cluster-cjg208q4q0s8.us-west-2.rds.amazonaws.com"
    ),
    "SALESTECH_BE_DB_PORT": "5432",
    "SALESTECH_BE_DB_BASE": "reevo_main",
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


def _chamber(key: str, namespace: str = _CHAMBER_NS) -> str:
    """Read one value from a dev chamber namespace. Values are never printed."""
    result = subprocess.run(
        ["chamber", "read", namespace, key, "-q"],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
        env=dict(os.environ, AWS_PROFILE=_AWS_PROFILE),
    )
    if result.returncode != 0:
        sys.exit(
            f"chamber read {namespace}/{key} failed (exit {result.returncode}):\n"
            f"{result.stderr.strip()}\n"
            f"If this is an SSO/credentials error, run `aws sso login --profile {_AWS_PROFILE}` "
            "and retry."
        )
    value = result.stdout.strip()
    if not value:
        sys.exit(f"chamber read {namespace}/{key} returned an empty value")
    return value


def dev_mint_env() -> dict[str, str]:
    """Environment for minting a dev-valid token.

    The CLI's --jwt-secret flag is parsed but never applied (signing reads
    settings.jwt_secret), so the secret must arrive through the environment.
    """
    env = dict(os.environ)
    env.update(_DEV_DB_ENV)
    env["SALESTECH_BE_JWT_SECRET"] = _chamber("salestech_be_jwt_secret", _CHAMBER_SECRETS_NS)
    env["SALESTECH_BE_JWT_ISSUER"] = _chamber("salestech_be_jwt_issuer")
    env["SALESTECH_BE_JWT_AUDIENCE"] = _chamber("salestech_be_jwt_audience")
    # ReevoJWTClaims.version defaults to the CLIENT's setting (types.py:88), while the
    # server rejects `version < settings.jwt_minimum_required_token_version` as
    # "token refresh required". Local defaults to 0, dev requires 1 — so mint with dev's.
    env["SALESTECH_BE_JWT_MINIMUM_REQUIRED_TOKEN_VERSION"] = _chamber(
        "salestech_be_jwt_minimum_required_token_version"
    )
    env["SALESTECH_BE_DB_USER"] = _chamber("salestech_be_db_user")
    env["SALESTECH_BE_DB_PASS"] = os.environ.get("DB_PASSWORD") or _chamber(
        "salestech_be_db_pass", _CHAMBER_SECRETS_NS
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


def cache_path(target: str) -> Path:
    """Separate cache per target — a local-signed token must never reach dev."""
    return _CACHE_DIR / {"local": "token.json", "dev": "token.dev.json", "stack": "token.stack.json"}[target]


def get_token(user_id: str, org_id: str, dev: bool) -> str:
    """Cached JWT: reuse until ~30s before expiry; re-mint on expiry or identity change."""
    cache = cache_path("dev" if dev else "local")
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


def stack_worktree(name: str) -> Path:
    """The worktree a stack runs from: <main>/worktrees/<name>, else the one cwd sits in."""
    if name:
        return _PRIMARY_BE.parent / "worktrees" / name
    for cand in (Path.cwd(), *Path.cwd().parents):
        if (cand / "salestech-be").is_dir() and (cand / "frontend-monorepo").is_dir():
            return cand
    sys.exit("not inside a worktree — pass --stack <worktree>")


# Run inside the stack's own salestech-be, so slot -> port and slot -> org are read from the
# backend's instance-isolation contract rather than re-derived here.
_STACK_LOOKUP = """
import sys
from pathlib import Path
from scripts.local_dev.instance_isolation import InstanceRegistry, org_id_for

workspace = str(Path(sys.argv[1]).resolve())
for record in InstanceRegistry().list_all():
    if record.workspace_path == workspace:
        print(record.app_port, org_id_for(record.index))
        break
else:
    raise SystemExit(f"no local stack registered for {workspace} — run `local-stack up` first")
"""


def _run_in(be_dir: Path, cmd: list[str], *, what: str) -> str:
    result = subprocess.run(
        cmd, cwd=be_dir, capture_output=True, text=True, timeout=180, check=False
    )
    if result.returncode != 0:
        sys.exit(f"{what} failed (exit {result.returncode}):\n{result.stderr.strip()}")
    return result.stdout


def stack_target(name: str) -> tuple[str, str, str, str]:
    """(base_url, user_id, org_id, token) for a numbered local stack, token cached per org."""
    be_dir = stack_worktree(name) / "salestech-be"
    if not (be_dir / "pyproject.toml").exists():
        sys.exit(f"no salestech-be at {be_dir}")
    port, org_id = _run_in(
        be_dir,
        ["uv", "run", "python", "-c", _STACK_LOOKUP, str(be_dir)],
        what="stack lookup",
    ).split()
    base = f"http://localhost:{port}"
    cache = cache_path("stack")
    if cache.exists():
        try:
            cached = json.loads(cache.read_text())
            if (
                cached.get("org_id") == org_id
                and cached.get("user_id")
                and cached.get("token")
                and not _expired(cached["token"])
            ):
                return base, cached["user_id"], org_id, cached["token"]
        except Exception:
            pass  # Legit business flow: a corrupt/absent cache just means we mint fresh.
    print(f"minting stack token for pool org {org_id}", file=sys.stderr)
    out = _run_in(
        be_dir,
        ["uv", "run", "python", "-m", "scripts.seed_dev_data", "--org-id", org_id, "--token"],
        what="`seed_dev_data --token` (is the pool org seeded? see local-stack seed-pool)",
    )
    found = dict(
        line.split("=", 1) for line in out.splitlines() if line.startswith("LOCAL_SESSION_OVERRIDE_")
    )
    # The block is .env-formatted, so every value arrives double-quoted.
    user_id = found.get("LOCAL_SESSION_OVERRIDE_USER_ID", "").strip().strip('"')
    token = found.get("LOCAL_SESSION_OVERRIDE_ACCESS_TOKEN", "").strip().strip('"')
    if not user_id or not _JWT.match(token):
        sys.exit("could not parse the admin user id and token from `seed_dev_data --token`")
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"user_id": user_id, "org_id": org_id, "token": token}))
    return base, user_id, org_id, token


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
    target_group = ap.add_mutually_exclusive_group()
    target_group.add_argument("--dev", action="store_true", help="target the deployed dev backend")
    target_group.add_argument(
        "--stack",
        action="store_true",
        help="target a numbered local-stack backend as its pool-org admin",
    )
    ap.add_argument(
        "--worktree",
        default="",
        help="with --stack: the worktree whose stack to call (default: the one cwd sits in)",
    )
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

    if args.worktree and not args.stack:
        sys.exit("--worktree only applies with --stack")
    target = "dev" if args.dev else "stack" if args.stack else "local"
    if target == "stack":
        base, user_id, org_id, token = stack_target(args.worktree)
    else:
        cfg = load_identity(args.dev)
        base = cfg["base_url"].rstrip("/")
        user_id, org_id = cfg["user_id"], cfg["org_id"]
    host = urllib.parse.urlparse(base).hostname or ""
    allowed = _DEV_HOSTS if args.dev else _LOCAL_HOSTS
    if host not in allowed:
        sys.exit(
            f"refusing base_url '{base}' — {target} target allows only "
            f"{sorted(allowed)}. This skill reaches local and dev only, never prod."
        )

    if args.dev and args.method != "GET" and not args.write:
        sys.exit(
            f"refusing {args.method} on dev without --write — dev is shared data. "
            "Re-run with --write once you're sure."
        )

    if target != "stack":
        token = get_token(user_id, org_id, args.dev)
    headers = {
        "Authorization": f"Bearer {token}",
        "x-reevo-user-id": user_id,
        "x-reevo-org-id": org_id,
        "Content-Type": "application/json",
    }

    if not args.skip_health_check and not health(base):
        hint = {
            "dev": "check Tailscale / the dev deployment",
            "stack": "is the stack up? (`local-stack list`)",
            "local": "is it running? (start it via env-manager)",
        }[target]
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
        cache_path(target).unlink(missing_ok=True)

    try:
        print(json.dumps(json.loads(body), indent=2))
    except json.JSONDecodeError:
        print(body)


if __name__ == "__main__":
    main()
