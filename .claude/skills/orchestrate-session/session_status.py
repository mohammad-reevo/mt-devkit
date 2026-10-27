#!/usr/bin/env python3
"""Per-turn state of every slice in a orchestrate-session project, in one call.

    /usr/bin/python3 .claude/skills/orchestrate-session/session_status.py <project>

Reads the index (~/.claude/spec/<project>-project.md) and prints one row per slice: its
session's live state (from `claude agents --json`), its PR's live state (one GraphQL query per
PR: state, mergeability, review, checks rollup, unresolved threads, merge-queue position), and
which of its scope / plan / handoff files exist. Under the table, each blocked session's last
assistant message from its transcript — the question it is asking Mohammad. The orchestrator
builds its picture from this, not from the messages sessions happened to send.

Read-only. Runs under /usr/bin/python3 (macOS system Python 3.9): keep 3.9-compatible.
"""
import json
import os
import glob
import re
import subprocess
import sys

SPEC = os.path.expanduser("~/.claude/spec")
TMP = os.path.expanduser("~/.claude/tmp")
PROJECTS = os.path.expanduser("~/.claude/projects")
QUESTION_CHARS = 1500

PR_QUERY = """query($owner:String!,$repo:String!,$n:Int!){repository(owner:$owner,name:$repo){
pullRequest(number:$n){state mergeStateStatus reviewDecision isInMergeQueue
mergeQueueEntry{position}
commits(last:1){nodes{commit{statusCheckRollup{state}}}}
reviewThreads(first:100){nodes{isResolved}}}}}"""


def run(cmd):
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError("%s: %s" % (" ".join(cmd[:3]), out.stderr.strip()[:200]))
    return out.stdout


def read_index(project):
    path = os.path.join(SPEC, project + "-project.md")
    with open(path) as f:
        lines = f.read().splitlines()
    orchestrator = ""
    for line in lines:
        if line.startswith("> Orchestrator:"):
            quoted = re.search(r'"([^"]+)"', line)
            orchestrator = quoted.group(1) if quoted else line.split(":", 1)[1].split("(")[0].strip()
    table = [l for l in lines if l.startswith("|")]
    header = [c.strip().lower() for c in table[0].strip("|").split("|")]
    rows = []
    for line in table[2:]:
        cells = [c.strip() for c in line.strip("|").split("|")]
        rows.append(dict(zip(header, cells)))
    return orchestrator, rows


def session_of(cell):
    """'A · f249f765' -> ('A', 'f249f765'); 'B (fresh session …)' -> ('B', None)."""
    letter = re.match(r"\s*([A-Z])\b", cell or "")
    short_id = re.search(r"\b([0-9a-f]{8})\b", cell or "")
    return (letter.group(1) if letter else None, short_id.group(1) if short_id else None)


def agent_of(agents, orchestrator, letter, short_id):
    for a in agents:
        if (short_id and a.get("id") == short_id) or (
                letter and orchestrator and a.get("name") == "%s - %s" % (orchestrator, letter)):
            return a
    return None


def last_question(session_id):
    """The session's last assistant text, or its AskUserQuestion questions; None without a transcript."""
    # The transcript sits under the cwd the session started in, which a worktree switch doesn't move.
    paths = glob.glob(os.path.join(PROJECTS, "*", session_id + ".jsonl"))
    if not paths:
        return None
    with open(paths[0]) as f:
        lines = f.read().splitlines()
    for line in reversed(lines):
        entry = json.loads(line)
        if entry.get("type") != "assistant":
            continue
        content = entry["message"]["content"]
        asked = [q.get("question", "") for block in content
                 if block.get("type") == "tool_use" and block.get("name") == "AskUserQuestion"
                 for q in block.get("input", {}).get("questions", [])]
        if asked:
            return "(question UI) " + " / ".join(asked)
        texts = [block["text"] for block in content if block.get("type") == "text"]
        if texts:
            text = texts[-1].strip()
            # The question closes the message, so a long one keeps its end.
            return text if len(text) <= QUESTION_CHARS else "…" + text[-QUESTION_CHARS:]
    return None


def pr_state(url):
    m = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", url or "")
    if not m:
        return "—"
    data = json.loads(run(["gh", "api", "graphql", "-f", "query=" + PR_QUERY,
                           "-F", "owner=" + m.group(1), "-F", "repo=" + m.group(2),
                           "-F", "n=" + m.group(3)]))
    pr = data["data"]["repository"]["pullRequest"]
    rollup = (pr["commits"]["nodes"] or [{}])[0].get("commit", {}).get("statusCheckRollup") or {}
    open_threads = sum(1 for t in pr["reviewThreads"]["nodes"] if not t["isResolved"])
    parts = ["#%s %s" % (m.group(3), pr["state"].lower())]
    if pr["state"] == "OPEN":
        parts += [pr["mergeStateStatus"].lower(),
                  "checks " + (rollup.get("state") or "none").lower(),
                  "review " + (pr["reviewDecision"] or "none").lower(),
                  "%d open threads" % open_threads]
        if pr["isInMergeQueue"]:
            parts.append("queue #%s" % (pr["mergeQueueEntry"] or {}).get("position"))
    return ", ".join(parts)


def files_of(project, slug, letter):
    have = [name for name, path in (
        ("scope", os.path.join(SPEC, slug + "-scope.md")),
        ("plan", os.path.join(SPEC, slug + "-plan.md")),
        ("handoff", os.path.join(TMP, project, "%s-handoff.md" % letter)),
    ) if os.path.isfile(path)]
    return " ".join(have) or "—"


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: session_status.py <project>")
    project = sys.argv[1]
    orchestrator, rows = read_index(project)
    agents = json.loads(run(["claude", "agents", "--json"]))
    blocked = []
    print("| Session | Slice | Index status | Agent | PR | Files |")
    print("|---|---|---|---|---|---|")
    for row in rows:
        slug = re.sub(r"\s*\(.*\)$", "", row.get("slice", "")).strip()
        letter, short_id = session_of(row.get("session", ""))
        agent = agent_of(agents, orchestrator, letter, short_id) if letter else None
        if agent and agent.get("state") == "blocked":
            blocked.append((letter, agent.get("sessionId")))
        pr_url = re.search(r"\((https://github\.com/[^)]+)\)", row.get("pr", ""))
        try:
            pr = pr_state(pr_url.group(1) if pr_url else None)
        except RuntimeError as e:
            # Legit business flow: one unreachable PR must not hide every other session's
            # state — the error is printed in that row for the orchestrator to see.
            pr = "error: %s" % e
        print("| %s | %s | %s | %s | %s | %s |" % (
            letter or "—", slug, row.get("status", ""),
            "%s/%s" % (agent.get("status"), agent.get("state")) if agent
            else ("not running" if letter else "—"),
            pr, files_of(project, slug, letter)))
    for letter, session_id in blocked:
        print("\n**%s asks:**\n%s" % (letter, last_question(session_id) or "— no transcript found"))


if __name__ == "__main__":
    main()
