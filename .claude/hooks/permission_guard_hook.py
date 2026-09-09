#!/usr/bin/env python3
"""Allow-by-default permission guard + secret guard (PreToolUse: Bash|Read|Edit|Write).

Philosophy: allow everything except a small, curated set of dangerous shapes.
This replaces the earlier prove-then-allow hook, which prompted on everything it
couldn't positively prove safe -> constant interruptions. Here the default is
ALLOW, and a hook `allow` decision blankets over ALL of Claude Code's built-in
Bash structural guards (cd&&git, $VAR, cd-with-redirect, brace-with-quote) at
once -- so those never prompt. Safety lives entirely in the deny/ask lists below.

Outcomes (strictest wins across a compound command; deny > ask > allow):
  - deny  -> hard block.
  - ask   -> emit nothing -> the normal prompt appears (the pressure valve).
  - allow -> emit allow -> runs with no prompt, built-in guards suppressed.

Bash: allow-by-default; ask/deny only for the curated patterns (network->shell,
  sudo/eval, destructive git, recursive rm, gh merge/review, raw-disk writes,
  and whole-file secret dumps like `cat .env`). `bash -c`/`zsh -ic` payloads are
  classified recursively, so env-manager aliases (`zsh -ic 'kill-be-f'`) stay
  allowed while `bash -c "rm -rf ~"` is caught. Running a script file
  (`bash foo.sh`) is allowed when the script sits under a trusted root
  (~/.claude, ~/Desktop/code -- your config + dev tree); a script anywhere else
  (~/Downloads, /tmp) still prompts, since its contents are opaque. Reading a
  secret file is denied for every reader that can print its content -- grep, sed,
  awk, head and friends as well as cat, since `grep '' .env` dumps a file just as
  thoroughly. Invocations that provably print none (`grep -q/-c/-l`, `sed -i`)
  pass. Shell rc + credential files (~/.zshrc, ~/.netrc, ~/.secrets.zsh) are
  covered alongside .env and key material: they carry keys and tokens amid
  ordinary config, so `cat ~/.zshrc` leaks them into the transcript.
Cloud: the same secret arriving from an API instead of a disk. A session
  inherits the operator's live AWS SSO / gcloud / kube credentials, so
  `aws ssm get-parameter --with-decryption` runs with their full
  entitlements and prints a decrypted value straight into the transcript --
  no local artifact, and the blast radius is the account rather than the
  laptop. Value-bearing shapes are denied (ssm get-parameter* with
  --with-decryption, secretsmanager get-secret-value, gcloud secrets
  versions access, vault read / kv get, kubectl get secret -o yaml|json,
  gh variable get). Metadata stays free -- names, types, versions and dates
  are what diagnosis actually needs and carry no secret, so
  describe-parameters, list-secrets, `gh secret list` and an aws `--query`
  projecting only metadata all pass. A production namespace is denied
  outright, metadata included.
Grep: a `content`-mode grep of a secret file -> deny. files_with_matches and
  count print no file content, so they pass.
Read/Edit/Write: hands-off (emit nothing, so native permissions + the worktree
  gate keep working) EXCEPT secret files (.env, keys) -> deny, an unscoped
  `Read` of a shell rc / credential file -> deny (offset+limit passes), and
  Edit/Write of a `.claude/` config path -> allow. The latter overrides Claude Code's built-in
  "edit its own settings" prompt, which fires on any `.claude/` write and which
  the permissions.allow list cannot suppress -- only a hook allow can. This
  subsumes the separate env-guard.

permissions.deny (rm -rf /, force-push) stays the native hard floor -- Claude
Code evaluates deny over a hook allow, so it still applies.

Fail-safe: any error -> emit nothing -> normal prompt (a bug degrades to
prompting, never to silently allowing something dangerous).

Bypass: MT_GUARD=0 in the environment (whole session), or a literal
`MT_GUARD=0 ` prefix on a single Bash command.

Runs under /usr/bin/python3 (macOS system Python 3.9): keep 3.9-compatible
(no PEP 604 unions, no match/case).
"""
from __future__ import annotations

import json
import os
import re
import shlex
import sys

ALLOW, ASK, DENY = "allow", "ask", "deny"
_RANK = {ALLOW: 0, ASK: 1, DENY: 2}

# Decision applied to secret-file access (Read/Edit/Write of a secret, or a
# whole-file dump like `cat .env`). DENY hard-blocks reading secrets into the
# transcript; flip to ASK for a prompt instead.
_SECRET_DECISION = DENY


def _emit(decision, reason):
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": decision,
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
    )
    sys.exit(0)


def _nothing():
    # Emit no decision -> normal permission flow (prompt / native rules) applies.
    sys.exit(0)


# --------------------------------------------------------------------------- #
# Secret-file detection -- shared by Bash tokens and Read/Edit/Write file paths
# --------------------------------------------------------------------------- #
# `.env`, `.env.local`, `.env.test` are secrets; `.env.example`/`.env.sample`/
# `.environment`/`foo.env` are not.
_ENV_RE = re.compile(
    r"^\.env(\.(?!example$|sample$|template$|dist$|defaults$)[A-Za-z0-9_.-]+)?$"
)
_KEY_BASENAME_RE = re.compile(r"^id_(rsa|dsa|ecdsa|ed25519)$")


def _is_secret_path(path):
    if not path:
        return False
    p = os.path.expanduser(os.path.expandvars(path)).replace("\\", "/")
    base = os.path.basename(p.rstrip("/"))
    if _ENV_RE.match(base):
        return True
    if _KEY_BASENAME_RE.match(base):
        return True
    if base.endswith(".pem") or base.endswith(".key"):
        return True
    if "/.ssh/" in p or p.endswith("/.ssh"):
        return True
    if "/.aws/credentials" in p or "/.gnupg/" in p:
        return True
    return False


# Shell rc + credential files. A whole-file dump leaks the keys and tokens these
# carry, but unlike a `.env` they are mostly ordinary config (aliases, exports,
# PATH) and are legitimately edited -- so they get a narrower treatment than
# `_is_secret_path`: whole-file reads denied, line-scoped reads (grep/sed, or a
# `Read` with offset+limit) allowed, Edit/Write untouched.
# Basename-matched, like the rules above: a Bash token carries no reliable cwd to
# resolve a relative path against.
_RC_SECRET_BASENAMES = frozenset(
    {
        ".zshrc",
        ".zshenv",
        ".zprofile",
        ".zlogin",
        ".bashrc",
        ".bash_profile",
        ".bash_login",
        ".profile",
        ".netrc",
        "_netrc",
        ".secrets.zsh",
        ".secrets.sh",
    }
)


def _is_rc_secret_path(path):
    if not path:
        return False
    p = os.path.expanduser(os.path.expandvars(path)).replace("\\", "/")
    return os.path.basename(p.rstrip("/")) in _RC_SECRET_BASENAMES


def _is_claude_config_path(path):
    """True if the path lives inside a `.claude/` config directory (user or
    project). Claude Code always prompts on writes there ("edit its own
    settings"); an explicit hook allow is the only way to suppress that."""
    if not path:
        return False
    p = os.path.expanduser(os.path.expandvars(path)).replace("\\", "/")
    return ".claude" in p.split("/")


# Roots under which running a script file (`bash foo.sh`) is auto-allowed: your
# own config and dev tree. A script outside these (e.g. ~/Downloads, /tmp) still
# prompts -- its contents are opaque, so the trust comes from where it lives.
_TRUSTED_SCRIPT_ROOTS = (
    os.path.expanduser("~/.claude"),
    os.path.expanduser("~/Desktop/code"),
)


def _is_trusted_script(path):
    """True if `path` resolves inside a trusted script root. Lexical (no FS
    access), with a path-boundary check so `~/.claude-evil` can't match
    `~/.claude`. A relative path can't be resolved without a reliable cwd, so it
    returns False -> the normal prompt still applies."""
    if not path:
        return False
    p = os.path.expanduser(os.path.expandvars(path)).replace("\\", "/")
    if not p.startswith("/"):
        return False
    p = os.path.normpath(p)
    return any(p == root or p.startswith(root + "/") for root in _TRUSTED_SCRIPT_ROOTS)


# --------------------------------------------------------------------------- #
# Bash classification
# --------------------------------------------------------------------------- #
_SHELL_INTERPRETERS = {"bash", "sh", "zsh", "dash", "ksh"}
# Tools that dump a whole file to stdout -- reading a secret with one of these
# leaks it into the transcript.
_WHOLE_FILE_READERS = {"cat", "less", "more", "bat", "view", "xxd", "od", "strings", "nl", "tac"}

# Tools that read a file and can print part of it. These were once excluded as
# "line-scoped -- env-manager's legit access", but that reasoning checked the
# binary and never the arguments: `grep '' .env`, `sed -n '1,$p'`, `awk '{print}'`
# and a bare `head` on a short file each dump the whole file. Nothing in the
# harness actually reads a secret to stdout -- env-manager rewrites with `sed -i`
# (a write) and worktree_setup uses `cp` -- and a script run under a trusted root
# is exempt regardless, so covering them costs nothing real.
_SCOPED_READERS = {
    "grep",
    "egrep",
    "fgrep",
    "rg",
    "ag",
    "ack",
    "sed",
    "awk",
    "gawk",
    "mawk",
    "head",
    "tail",
    "cut",
    "rev",
    "fold",
    "expand",
    "unexpand",
    "colrm",
    "diff",
    "pr",
}
_FILE_READERS = _WHOLE_FILE_READERS | _SCOPED_READERS

# Flags that suppress file content: -q/--quiet/--silent print nothing, -c/--count
# a number, -l/-L filenames. `sed -i` is an in-place write, which is what
# env-manager actually does to a .env.
_GREP_FAMILY = {"grep", "egrep", "fgrep", "rg", "ag", "ack"}
_GREP_SILENT_SHORT = frozenset("qclL")
_GREP_SILENT_LONG = frozenset(
    {
        "--quiet",
        "--silent",
        "--count",
        "--files-with-matches",
        "--files-without-match",
    }
)


def _has_short_flag(args, letters):
    """True if any short-flag token (`-c`, or a cluster like `-ic`) carries one of
    `letters`. Long flags (`--count`) are matched separately, by exact name."""
    for a in args:
        if a.startswith("-") and not a.startswith("--") and len(a) > 1:
            if any(ch in letters for ch in a[1:]):
                return True
    return False


def _prints_no_content(binary, args):
    """True when this invocation provably prints no file content, so it may read a
    secret path. Deliberately narrow: anything not proven silent is denied."""
    if binary == "sed":
        return any(a.startswith("-i") or a.startswith("--in-place") for a in args)
    if binary in _GREP_FAMILY:
        if any(a in _GREP_SILENT_LONG for a in args):
            return True
        return _has_short_flag(args, _GREP_SILENT_SHORT)
    return False

# --------------------------------------------------------------------------- #
# Cloud secret-store detection (Bash)
# --------------------------------------------------------------------------- #
# The tier above stops `cat .env`; this one stops the same secret arriving over
# an API with the operator's inherited credentials. Only value-bearing shapes
# are denied -- metadata (names, types, versions, dates) is what diagnosis
# actually needs, and it carries no secret.

# Reason for a pending deny, set by this tier so `_run` can name the store that
# was touched. Left None by the file tier, which keeps the generic message.
_DENY_REASON = None


def _flag_value(args, names):
    """Value of `--flag X` or `--flag=X` for any flag in `names`, else None."""
    for i, a in enumerate(args):
        for n in names:
            if a == n:
                return args[i + 1] if i + 1 < len(args) else ""
            if a.startswith(n + "="):
                return a[len(n) + 1:]
    return None


# A `--query` naming only metadata fields prints no secret -- the shape this
# guard's originating session actually needed was
# `--query Parameter.[Type,Version,LastModifiedDate]`. Narrow by design: a bare
# container renders Value along with everything else, so it does not qualify.
_AWS_VALUE_FIELDS = ("value", "secretstring", "secretbinary")
_AWS_BARE_CONTAINERS = frozenset(
    {"@", "parameter", "parameters", "parameters[]", "parameters[*]", "secretlist"}
)


def _aws_query_hides_value(args):
    """True when an explicit `--query` provably projects no secret value."""
    q = _flag_value(args, ("--query",))
    if not q:
        return False
    s = q.strip().strip("'\"").lower()
    if not s or s in _AWS_BARE_CONTAINERS:
        return False
    return not any(f in s for f in _AWS_VALUE_FIELDS)


# `-o yaml|json|jsonpath|go-template|custom-columns` renders a Secret's `data`
# block (base64 is an encoding, not a protection). `-o name` / `-o wide` and the
# default table print names and types only.
_KUBECTL_VALUE_OUTPUTS = (
    "yaml",
    "json",
    "jsonpath",
    "go-template",
    "template",
    "custom-columns",
)


def _kubectl_prints_secret_values(args):
    out = _flag_value(args, ("-o", "--output"))
    if out is None:
        return False
    o = out.strip().strip("'\"").lower()
    return any(o.startswith(p) for p in _KUBECTL_VALUE_OUTPUTS)


# A path segment that is exactly `prod`/`production`, or ends in `-prod`/`_prod`.
# Matches /secrets-reevo-be-prod/..., /reevo-be-prod, /salestech-be/prod/... and
# --secret=my-app-prod, while leaving /reevo-be-dev/... and `reproduction` alone.
_PROD_SEGMENT_RE = re.compile(r"(?:^|[-_.])prod(?:uction)?$")


def _names_prod_namespace(args):
    for a in args:
        for seg in re.split(r"[/=,:]", a):
            if _PROD_SEGMENT_RE.search(seg.strip().lower()):
                return True
    return False


def _cloud_secret_store(binary, args):
    """Name of the store this invocation reads a *value* out of, or None.
    Metadata-only subcommands return None and stay allowed."""
    sub = [a for a in args if not a.startswith("-")]

    if binary == "aws":
        if sub[:1] == ["ssm"] and len(sub) >= 2:
            if sub[1] in ("get-parameter", "get-parameters", "get-parameters-by-path"):
                # Without --with-decryption a SecureString comes back as
                # ciphertext, and the plain String parameters it does return are
                # config by definition. The decrypt flag is what declares intent.
                if "--with-decryption" in args:
                    return "AWS SSM Parameter Store"
            return None
        if sub[:2] == ["secretsmanager", "get-secret-value"]:
            return "AWS Secrets Manager"
        return None

    if binary == "gcloud":
        if sub[:3] == ["secrets", "versions", "access"]:
            return "Google Secret Manager"
        return None

    if binary == "vault":
        if sub[:1] == ["read"] or sub[:2] == ["kv", "get"]:
            return "HashiCorp Vault"
        return None

    if binary == "kubectl":
        if sub[:1] == ["get"] and len(sub) >= 2 and sub[1] in ("secret", "secrets"):
            if _kubectl_prints_secret_values(args):
                return "Kubernetes Secret"
        return None

    if binary == "gh":
        # GitHub never returns a secret's value over the API, so `gh secret list`
        # is metadata. Actions *variables* do carry their value.
        if sub[:2] == ["variable", "get"]:
            return "GitHub Actions variable"
        if sub[:2] == ["variable", "list"]:
            j = _flag_value(args, ("--json",))
            if j and "value" in j.lower():
                return "GitHub Actions variable"
        return None

    return None


def _classify_cloud_secret(binary, args):
    """DENY when this invocation extracts a secret value from a cloud store, or
    None when it is not a secret-store read at all (caller keeps classifying)."""
    global _DENY_REASON
    store = _cloud_secret_store(binary, args)
    if store is None:
        return None
    if _names_prod_namespace(args):
        # Prod is denied ahead of the metadata carve-out: a dev session has no
        # business holding a prod secret, and "I only wanted the type" is not
        # worth trusting a query parse for. The operator's own terminal is the
        # right place for a genuine prod read.
        _DENY_REASON = (
            "Blocked: reads a PRODUCTION secret from {} with your inherited "
            "credentials. Run it in your own terminal, or -- if you truly mean "
            "to pull prod into this session -- prefix with MT_GUARD=0.".format(store)
        )
        return DENY
    if _aws_query_hides_value(args):
        return None  # projects metadata only; no value is printed
    _DENY_REASON = (
        "Blocked: prints a secret value from {} into the transcript. Metadata "
        "reads still pass -- names, types, versions and dates (e.g. "
        "`--query Parameter.[Type,Version]`, `describe-parameters`, "
        "`list-secrets`, `gh secret list`). To read the value anyway, prefix the "
        "command with MT_GUARD=0.".format(store)
    )
    return DENY


# curl/wget piped straight into a shell/interpreter -- the classic RCE vector.
_NET_SHELL_RE = re.compile(
    r"\b(?:curl|wget|fetch)\b[^|]*\|\s*(?:sudo\s+)?"
    r"(?:bash|sh|zsh|dash|python3?|node|perl|ruby)\b"
)
# `$(curl ...)` / `` `curl ...` `` used as a command source.
_SUBST_NET_RE = re.compile(r"[$`]\(?[^)]*\b(?:curl|wget|fetch)\b")
# Writing to a raw disk device -- catastrophic, never legitimate here.
_DISK_WRITE_RE = re.compile(r">\s*/dev/(?:sd[a-z]|disk\d|nvme\d|rdisk\d|hd[a-z])")
_DD_DEVICE_RE = re.compile(r"of=/dev/(?:sd[a-z]|disk\d|nvme\d|rdisk\d|hd[a-z])")


_GUARD_OFF_PREFIX_RE = re.compile(r"^\s*MT_GUARD=0\s+\S")


def _split_segments(command):
    """Split into segments on &&, ||, ;, |, and newlines (same approach as the
    branch guard) so each invocation's leading binary can be inspected.

    `$(` and a backtick also open a segment, so the command inside a
    substitution is classified rather than swallowed into its assignment:
    `KEY=$(aws ssm get-parameter ... --with-decryption)` otherwise parses as
    the single token `KEY=$(aws`, and the guard never sees the `aws`
    invocation at all. The closing paren stays attached to the last token --
    harmless here, and not splitting on `)` keeps `find \\( ... \\)` and
    quoted parens intact."""
    tmp = command.replace("\n", ";").replace("$(", ";").replace("`", ";")
    for op in ("&&", "||"):
        tmp = tmp.replace(op, ";")
    tmp = tmp.replace("|", ";")
    return [s.strip() for s in tmp.split(";") if s.strip()]


def _real_binary(tokens):
    """First token that is the actual command, skipping leading `VAR=val` inline
    env assignments (e.g. `CLAUDE_ENV_GUARD=0 bash -c ...`). Returns (name, args)
    or (None, [])."""
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if "=" in t and not t.startswith("-") and "/" not in t.split("=", 1)[0]:
            i += 1
            continue
        return os.path.basename(t), tokens[i + 1:]
    return None, []


def _dash_c_payload(args):
    """Return the payload string of a `-c`/`-ic`/`-lc` shell flag, or None."""
    for i, a in enumerate(args):
        if a.startswith("-") and "c" in a.lstrip("-") and not a.startswith("--"):
            return args[i + 1] if i + 1 < len(args) else None
    return None


def _classify_git(args):
    rest = [a for a in args if a not in ("--no-pager",)]
    sub = next((a for a in rest if not a.startswith("-")), None)
    if sub == "push":
        if "--no-verify" in rest or "--force" in rest or "-f" in rest:
            return ASK
        if any(a in ("main", "master") for a in rest):
            return ASK
        return ALLOW
    if sub == "reset" and "--hard" in rest:
        return ASK
    if sub == "clean" and any(a.startswith("-") and "f" in a for a in rest):
        return ASK
    return ALLOW


def _classify_gh(args):
    if len(args) >= 2 and args[0] == "pr":
        if args[1] in ("merge", "review"):
            return ASK
        if args[1] == "edit" and any(
            a in ("--add-reviewer", "--reviewer") for a in args
        ):
            return ASK
    return ALLOW


def _classify_segment(tokens, depth):
    if not tokens:
        return ALLOW

    binary, args = _real_binary(tokens)
    if binary is None:
        return ALLOW

    if (
        binary in _FILE_READERS
        and any(_is_secret_path(a) or _is_rc_secret_path(a) for a in args)
        and not _prints_no_content(binary, args)
    ):
        return _SECRET_DECISION

    cloud = _classify_cloud_secret(binary, args)
    if cloud is not None:
        return cloud

    if binary in _SHELL_INTERPRETERS and depth < 4:
        payload = _dash_c_payload(args)
        if payload is not None:
            return _classify_command(payload, depth + 1)
        # `bash script.sh` (a script file, not -c) -- running arbitrary code.
        # Allow when the script lives in a trusted root (your config / dev tree);
        # otherwise prompt, since the file's contents are opaque.
        script = next((a for a in args if not a.startswith("-")), None)
        if script is not None:
            return ALLOW if _is_trusted_script(script) else ASK
        return ALLOW

    if binary in ("eval", "sudo", "doas"):
        return ASK
    if binary == "mkfs" or binary.startswith("mkfs."):
        return DENY
    if binary == "dd":
        return DENY if any(_DD_DEVICE_RE.match(a) for a in args) else ASK
    if binary == "shred":
        return ASK
    if binary == "rm":
        if "--recursive" in args or any(
            a.startswith("-") and not a.startswith("--") and ("r" in a or "R" in a)
            for a in args
        ):
            return ASK
        return ALLOW
    if binary == "git":
        return _classify_git(args)
    if binary == "gh":
        return _classify_gh(args)
    return ALLOW


def _classify_command(command, depth=0):
    if _DISK_WRITE_RE.search(command):
        return DENY
    if _NET_SHELL_RE.search(command) or _SUBST_NET_RE.search(command):
        return ASK
    worst = ALLOW
    for seg in _split_segments(command):
        try:
            tokens = shlex.split(seg)
        except Exception:
            # Unparseable quoting -- the command-level regexes above already ran,
            # so default this segment to allow rather than prompt on every odd
            # quote. Rare, and keeps friction down.
            continue
        d = _classify_segment(tokens, depth)
        if _RANK[d] > _RANK[worst]:
            worst = d
        if worst == DENY:
            break
    return worst


# --------------------------------------------------------------------------- #
# Entry
# --------------------------------------------------------------------------- #
def _run():
    if os.environ.get("MT_GUARD", "1") == "0":
        _nothing()

    try:
        data = json.load(sys.stdin)
    except Exception:
        _nothing()

    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input") or {}

    if tool == "Bash":
        command = tool_input.get("command", "")
        if not command:
            _nothing()
        if _GUARD_OFF_PREFIX_RE.match(command):
            _nothing()  # explicit, visible opt-out for this one command
        decision = _classify_command(command)
        if decision == DENY:
            _emit(
                DENY,
                _DENY_REASON
                or (
                    "Blocked: raw-disk destruction or secret-file read. "
                    "Existence checks (`grep -q/-c`) and `sed -i` rewrites "
                    "still pass; to read a secret value anyway, prefix the "
                    "command with MT_GUARD=0."
                ),
            )
        if decision == ASK:
            _nothing()  # surface the normal prompt
        _emit(ALLOW, "allow-by-default ACL")

    if tool == "Grep":
        path = tool_input.get("path") or ""
        if _is_secret_path(path) or _is_rc_secret_path(path):
            # files_with_matches (the default) and count print no file content;
            # "content" prints matching lines, which is the whole exposure.
            if (tool_input.get("output_mode") or "files_with_matches") == "content":
                _emit(
                    DENY,
                    "Blocked by ACL: content grep of a secret file. Use "
                    "output_mode files_with_matches or count.",
                )
        _nothing()

    if tool in ("Read", "Edit", "Write", "NotebookEdit"):
        path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
        if _is_secret_path(path):
            if _SECRET_DECISION == DENY:
                _emit(DENY, "Blocked by ACL: secret file (.env / key material).")
            _nothing()  # ASK -> normal prompt on the secret file
        if tool == "Read" and _is_rc_secret_path(path):
            # A scoped read surfaces a slice, not the file -- that is the legit
            # access (an alias body, one export line), and it is what this
            # guard's own originating session needed. An unscoped Read pulls
            # every key and token in the file into context.
            if tool_input.get("offset") is None or tool_input.get("limit") is None:
                _emit(
                    DENY,
                    "Blocked by ACL: whole-file read of a shell rc / credential "
                    "file. Re-read it with offset+limit.",
                )
            _nothing()  # scoped -> hands off to native permissions
        if tool in ("Edit", "Write", "NotebookEdit") and _is_claude_config_path(path):
            _emit(ALLOW, "allow-by-default ACL: .claude config path")
        _nothing()  # non-secret file tool: hands off to native permissions

    _nothing()


def main():
    try:
        _run()
    except SystemExit:
        raise
    except Exception:
        # A hook bug must never block a tool: fail open to the normal prompt flow.
        sys.exit(0)


if __name__ == "__main__":
    main()
