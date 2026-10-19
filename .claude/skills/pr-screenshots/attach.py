#!/usr/bin/env python3
"""Attach images to a PR body by committing them to the repo's orphan `pr-media` branch.

GitHub has no API for PR image upload, but an image committed to the same repo renders in
the PR body for anyone with repo access. Each PR gets a `<pr>/` folder on `pr-media`; the
branch is built with plumbing (hash-object / mktree / commit-tree), so the caller's
checked-out branch and working tree are never touched.

  attach.py --repo-dir <clone> --pr <n> <file> [<file> ...] [--update-body] [--caption "<file>=<text>" ...]

Prints one markdown embed per file. --update-body also writes them into the live PR body:
in place of the frontend template placeholder, else under the Visual Verification heading,
else appended — editing the fetched live body, never a local draft.
"""

import argparse
import json
import os
import subprocess
import sys

BRANCH = "pr-media"
PLACEHOLDER = "[DRAG AND DROP SCREENSHOTS OR VIDEOS HERE]"
VISUAL_HEADING = "# Visual Verification & UI Demo"


def git(repo: str, *args: str, stdin: str | None = None) -> str:
    return subprocess.run(
        ["git", "-C", repo, *args], input=stdin, capture_output=True, text=True, check=True
    ).stdout.strip()


def remote_tip(repo: str) -> str | None:
    out = git(repo, "ls-remote", "origin", f"refs/heads/{BRANCH}")
    return out.split()[0] if out else None


def tree_entries(repo: str, treeish: str) -> list[str]:
    out = git(repo, "ls-tree", treeish)
    return out.splitlines() if out else []


def build_commit(*, repo: str, pr: str, files: list[str], parent: str | None) -> str:
    # Keep every other PR's folder, and any file already in this PR's folder not being replaced.
    names = {os.path.basename(f) for f in files}
    pr_entries: list[str] = []
    root_entries: list[str] = []
    if parent:
        git(repo, "fetch", "--quiet", "origin", f"refs/heads/{BRANCH}")
        for line in tree_entries(repo, parent):
            if line.endswith(f"\t{pr}"):
                pr_entries = [
                    e for e in tree_entries(repo, f"{parent}:{pr}") if e.split("\t")[1] not in names
                ]
            else:
                root_entries.append(line)
    for f in files:
        blob = git(repo, "hash-object", "-w", f)
        pr_entries.append(f"100644 blob {blob}\t{os.path.basename(f)}")
    pr_tree = git(repo, "mktree", stdin="\n".join(pr_entries) + "\n")
    root_entries.append(f"040000 tree {pr_tree}\t{pr}")
    root_tree = git(repo, "mktree", stdin="\n".join(root_entries) + "\n")
    args = ["commit-tree", root_tree, "-m", f"chore: PR verification media for #{pr} (never merged)"]
    if parent:
        args[2:2] = ["-p", parent]
    return git(repo, *args)


def push(*, repo: str, pr: str, files: list[str]) -> None:
    # A concurrent session may move pr-media between our read and push; rebuild on rejection.
    for _ in range(3):
        parent = remote_tip(repo)
        commit = build_commit(repo=repo, pr=pr, files=files, parent=parent)
        result = subprocess.run(
            ["git", "-C", repo, "push", "--quiet", "origin", f"{commit}:refs/heads/{BRANCH}"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return
        if "rejected" not in result.stderr and "non-fast-forward" not in result.stderr:
            sys.exit(f"push failed:\n{result.stderr}")
    sys.exit("push kept being rejected (pr-media moving under us); retry")


def update_body(*, repo: str, pr: str, block: str) -> None:
    body = subprocess.run(
        ["gh", "pr", "view", pr, "--json", "body", "-q", ".body"],
        cwd=repo, capture_output=True, text=True, check=True,
    ).stdout
    if PLACEHOLDER in body:
        body = body.replace(PLACEHOLDER, block)
    elif VISUAL_HEADING in body:
        head, _, tail = body.partition(VISUAL_HEADING)
        body = f"{head}{VISUAL_HEADING}\n\n{block}\n{tail}"
    else:
        body = f"{body.rstrip()}\n\n{block}\n"
    subprocess.run(
        ["gh", "pr", "edit", pr, "--body-file", "-"], cwd=repo, input=body, text=True, check=True,
        stdout=subprocess.DEVNULL,
    )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-dir", required=True)
    p.add_argument("--pr", required=True)
    p.add_argument("--update-body", action="store_true")
    p.add_argument("--caption", action="append", default=[], help="<file basename>=<caption>")
    p.add_argument("files", nargs="+")
    a = p.parse_args()

    missing = [f for f in a.files if not os.path.isfile(f)]
    if missing:
        sys.exit(f"not found: {missing}")
    repo = os.path.abspath(a.repo_dir)
    name_with_owner = json.loads(
        subprocess.run(
            ["gh", "repo", "view", "--json", "nameWithOwner"],
            cwd=repo, capture_output=True, text=True, check=True,
        ).stdout
    )["nameWithOwner"]
    captions = dict(c.split("=", 1) for c in a.caption)

    push(repo=repo, pr=a.pr, files=a.files)

    embeds = []
    for f in a.files:
        base = os.path.basename(f)
        cap = captions.get(base, os.path.splitext(base)[0])
        url = f"https://github.com/{name_with_owner}/raw/{BRANCH}/{a.pr}/{base}"
        embeds.append(f"**{cap}**\n\n![{cap}]({url})")
    block = "\n\n".join(embeds)
    if a.update_body:
        update_body(repo=repo, pr=a.pr, block=block)
    print(block)


if __name__ == "__main__":
    main()
