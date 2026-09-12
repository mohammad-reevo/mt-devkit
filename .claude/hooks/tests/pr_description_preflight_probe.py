#!/usr/bin/env python3
"""Probe for pr_description_preflight_hook.py -- run it, don't reason about it.

    /usr/bin/python3 .claude/hooks/tests/pr_description_preflight_probe.py

Builds a throwaway workspace that mirrors the real shape -- a worktree holding a
`salestech-be` that ships a validator and a `frontend-monorepo` that does not --
then feeds real PreToolUse payloads to the hook as a subprocess and asserts which
repo it routed to. Exits non-zero on the first mismatch.

Why this exists: the hook's whole job is picking a repo, and picking the wrong
one is silent in exactly the wrong direction. It does not fail open, it denies --
a correct frontend body checked against the backend template comes back as
"Missing or out-of-order required section '## Summary'", which reads like a body
problem and sends you rewriting a body that was already right. That is what
happened on frontend-monorepo#17656, and it cost three round-trips and a wrong
theory about `cd` to diagnose.

The stand-in validator reports the `CLAUDE_PROJECT_DIR` it was handed, so an
assertion can name the repo the hook chose rather than just "something denied".

Two outcomes:
  allow -- no decision emitted, so the PR call proceeds (the hook is fail-open)
  deny  -- the delegate for <repo> ran and its verdict was passed through
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir,
                    "pr_description_preflight_hook.py")
HOOK = os.path.normpath(HOOK)

# Stands in for salestech-be's scripts/hooks/extract_pr_description.py. Always
# denies, and names the repo root it was pointed at, so routing is observable.
STUB = '''#!/usr/bin/env python3
import json, os, sys
sys.stdin.read()
sys.stdout.write(json.dumps({"hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "DELEGATE " + os.path.basename(
        os.environ.get("CLAUDE_PROJECT_DIR", "?")),
}}))
'''

FAILURES = []


def build_workspace(root):
    """workspace/worktrees/wt/{salestech-be,frontend-monorepo} -- only the
    backend ships a validator, matching the real repos."""
    wt = os.path.join(root, "workspace", "worktrees", "wt")
    backend = os.path.join(wt, "salestech-be")
    frontend = os.path.join(wt, "frontend-monorepo")
    delegate = os.path.join(backend, "scripts", "hooks")
    os.makedirs(delegate)
    os.makedirs(os.path.join(frontend, "src"))
    with open(os.path.join(delegate, "extract_pr_description.py"), "w") as fh:
        fh.write(STUB)
    return wt, backend, frontend


def run(command, cwd):
    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": cwd,
    })
    p = subprocess.Popen([sys.executable, HOOK],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True)
    out, _ = p.communicate(payload, timeout=60)
    out = (out or "").strip()
    if not out:
        return "allow", ""
    parsed = json.loads(out)
    hook_output = parsed.get("hookSpecificOutput") or {}
    return (hook_output.get("permissionDecision") or "?",
            hook_output.get("permissionDecisionReason") or "")


def check(label, command, cwd, expect_decision, expect_repo=""):
    decision, reason = run(command, cwd)
    routed = reason.replace("DELEGATE ", "") if reason.startswith("DELEGATE ") else ""
    ok = decision == expect_decision and routed == expect_repo
    print("%-4s %s" % ("ok" if ok else "FAIL", label))
    if not ok:
        FAILURES.append("%s: expected %s/%s, got %s/%s"
                        % (label, expect_decision, expect_repo or "-",
                           decision, routed or "-"))


def main():
    root = tempfile.mkdtemp(prefix="pr-preflight-probe-")
    try:
        wt, backend, frontend = build_workspace(root)

        # The regression. Editing a frontend PR from inside the backend checkout
        # used to join the name onto the cwd, miss, walk up into salestech-be,
        # and validate a frontend body against the backend template.
        check("frontend PR from inside salestech-be -> no delegate",
              "gh pr edit 17656 --repo ReevoAI/frontend-monorepo --body-file b.md",
              backend, "allow")

        # The mirror: the backend really is the target, named from a sibling.
        check("backend PR from inside frontend-monorepo -> backend delegate",
              "gh pr edit 33134 --repo ReevoAI/salestech-be --body-file b.md",
              frontend, "deny", "salestech-be")

        # The shape that already worked, still working.
        check("backend PR with --repo from the worktree root",
              "gh pr create --repo ReevoAI/salestech-be --title t --body-file b.md",
              wt, "deny", "salestech-be")

        check("frontend PR with --repo from the worktree root -> no delegate",
              "gh pr create --repo ReevoAI/frontend-monorepo --title t --body-file b.md",
              wt, "allow")

        # No `--repo`: the cwd and `cd` clues are unchanged by the fix.
        check("plain gh pr create inside salestech-be",
              "gh pr create --title t --body-file b.md", backend, "deny", "salestech-be")

        check("cd salestech-be && gh pr create from the worktree root",
              "cd salestech-be && gh pr create --title t --body-file b.md",
              wt, "deny", "salestech-be")

        check("plain gh pr create inside frontend-monorepo -> no delegate",
              "gh pr create --title t --body-file b.md", frontend, "allow")

        # A repo that is not in this workspace never resolves to a sibling.
        check("--repo naming a repo outside the workspace -> no delegate",
              "gh pr create --repo ReevoAI/some-other-repo --title t --body-file b.md",
              backend, "allow")

        # Prefilter: an ordinary command must not pay for a subprocess.
        check("a command that is not a PR call",
              "gh issue list --limit 5", backend, "allow")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    if FAILURES:
        print("\n%d failure(s):" % len(FAILURES))
        for line in FAILURES:
            print("  " + line)
        sys.exit(1)
    print("\nall routing cases pass")


if __name__ == "__main__":
    main()
