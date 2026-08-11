#!/usr/bin/env python3
"""Select the rule files that apply to a set of changed files.

    select_rules.py <repo-root> <changed-file>...
    git diff --name-only origin/main...HEAD | select_rules.py <repo-root>

Prints, one path per line, every rule under ``<repo-root>/.claude/rules/`` whose
``paths:`` frontmatter globs match at least one changed file. A rule with no
frontmatter, or with frontmatter that has no ``paths:`` key, is unscoped and is
always printed.

Why this exists: a reviewer subagent loads the mt-devkit house rules for free but
sees none of a sub-repo's own rules, and the sub-repos carry dozens each.
Path-scoping is what makes those usable without reading them all into context.

Why Python and not shell: shell ``case`` globbing cannot brace-expand, so
``src/**/*.{ts,tsx}`` — the dominant shape in frontend-monorepo — silently matched
nothing, and its ``**/`` required at least one intervening directory, so direct
children were missed. Both failures were silent, which is the worst property a
rule selector can have.

Unsupported glob syntax (character classes, unbalanced braces) is reported as a
malformed rule rather than quietly compiled into a pattern that matches nothing —
a rule that vanishes from a review without saying so is the failure this whole
selector exists to prevent.

Exit codes: 0 selected (possibly nothing), 2 bad usage/arguments, 3 selection
succeeded but some rule files are malformed. On 3 the selected rules are still
printed to stdout as normal — the code means "use these, and tell the user these
other rules could not be scoped", not "selection failed".
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_FRONTMATTER_DELIM = "---"
_MAX_BRACE_GROUPS = 10


class UsageError(Exception):
    """A caller mistake that must not be reported as 'nothing matched'."""


def _normalize_changed(paths: list[str], repo_root: Path) -> list[str]:
    """Make changed paths repo-relative.

    Every glob is ``^``-anchored, so an absolute or ``./``-prefixed path matches
    nothing and collapses the selection to just the unscoped rules — which looks
    exactly like "this diff touches nothing scoped".
    """
    root = repo_root.resolve()
    out: list[str] = []
    for raw in paths:
        value = raw.strip()
        if not value:
            continue
        candidate = Path(value)
        if candidate.is_absolute():
            try:
                value = str(candidate.resolve().relative_to(root))
            except ValueError:
                # Legit business flow: a caller passing a path from another repo
                # is a normal invocation mistake. Re-raised as the typed UsageError
                # so it exits 2 instead of quietly selecting nothing.
                raise UsageError(f"changed path is outside the repo root: {raw}") from None
        elif value.startswith("./"):
            value = value[2:]
        out.append(value)
    return out


def expand_braces(pattern: str) -> list[str]:
    """Expand ``{a,b}`` alternatives into a list of brace-free patterns.

    Capped: expansion is exponential in the number of groups, so a pathological
    glob would hang the selector instead of reporting anything.
    """
    start = pattern.find("{")
    if start == -1:
        return [pattern]

    if pattern.count("{") > _MAX_BRACE_GROUPS:
        raise MalformedRule(
            f"glob has {pattern.count('{')} brace groups (limit {_MAX_BRACE_GROUPS})"
        )

    depth = 0
    for i in range(start, len(pattern)):
        if pattern[i] == "{":
            depth += 1
        elif pattern[i] == "}":
            depth -= 1
            if depth == 0:
                head, body, tail = pattern[:start], pattern[start + 1 : i], pattern[i + 1 :]
                out = []
                for alt in _split_flow_items(body):
                    out.extend(expand_braces(head + alt + tail))
                return out

    # Treating an unbalanced brace as a literal produces a pattern that matches
    # nothing, so the rule silently vanishes from the review — the exact
    # substitute-and-carry-on this selector exists to avoid.
    raise MalformedRule(f"unbalanced brace in glob: {pattern}")


def _split_flow_items(body: str) -> list[str]:
    """Split an inline flow list on top-level commas only.

    A comma inside a brace group, a bracket group, or quotes belongs to the item.
    Splitting on every comma is what made `["src/**/*.{ts,tsx}"]` parse as two
    globs that matched nothing — silently, since the list was non-empty.
    """
    items, depth, quote, current = [], 0, None, ""
    for ch in body:
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch in "{[":
            depth += 1
        elif ch in "}]":
            depth -= 1
        elif ch == "," and depth == 0:
            items.append(current)
            current = ""
            continue
        current += ch
    items.append(current)
    return items


def glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Translate one brace-free glob to a regex with real ``**`` semantics.

    ``**/`` spans zero or more directories (so it matches direct children),
    ``**`` alone spans anything, ``*`` and ``?`` stop at a path separator.
    """
    # Collapse runs of `**/`. Adjacent groups each emit a `(?:[^/]+/)*`, and
    # nesting those quantifiers backtracks catastrophically on a long non-match
    # (12 adjacent groups measured at 54s). A run is semantically one group.
    pattern = re.sub(r"(?:\*\*/)+", "**/", pattern)

    # Escaping a character class to literal text would match nothing and drop the
    # rule silently. Refuse loudly instead — see the module docstring.
    if "[" in pattern:
        raise MalformedRule(
            f"glob uses an unsupported character class: {pattern} "
            "(rewrite it as brace alternatives, e.g. {a,b})"
        )

    out, i, n = ["^"], 0, len(pattern)
    while i < n:
        if pattern.startswith("**/", i):
            out.append("(?:[^/]+/)*")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    out.append("$")
    return re.compile("".join(out))


def _strip_comment(value: str) -> str:
    """Drop a trailing ``# comment`` from a glob, respecting quotes."""
    quote = None
    for i, ch in enumerate(value):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (i == 0 or value[i - 1].isspace()):
            return value[:i]
    return value


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


class MalformedRule(Exception):
    """A rule file whose frontmatter cannot be trusted to scope it."""


def parse_globs(text: str) -> list[str] | None:
    """Return a rule's globs, or None when the rule is unscoped.

    Raises MalformedRule when the frontmatter is unclosed, or when a ``paths:``
    key is present but yields no usable glob. Both cases must be loud: silently
    treating them as "unscoped" would print the rule for every changed file,
    which is indistinguishable from a genuinely global rule.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != _FRONTMATTER_DELIM:
        return None  # no frontmatter at all — unscoped

    try:
        end = next(
            i for i, line in enumerate(lines[1:], start=1) if line.strip() == _FRONTMATTER_DELIM
        )
    except StopIteration:
        # Legit business flow: a hand-written rule with unclosed frontmatter is a
        # normal authoring mistake, not a failure here. Re-raised as the typed
        # MalformedRule the caller already reports and exits 3 on.
        raise MalformedRule("frontmatter is never closed by '---'") from None

    frontmatter = lines[1:end]
    globs: list[str] = []
    in_paths = False
    saw_paths_key = False

    for line in frontmatter:
        if not in_paths:
            match = re.match(r"^paths:(.*)$", line)
            if not match:
                continue
            saw_paths_key = True
            inline = _strip_comment(match.group(1)).strip()
            if inline[:1] in (">", "|"):
                raise MalformedRule("'paths:' is a block scalar; write it as a list of globs")
            if inline.startswith("[") and inline.endswith("]"):
                globs.extend(
                    item
                    for item in (_unquote(p) for p in _split_flow_items(inline[1:-1]))
                    if item
                )
                continue
            if inline:
                globs.append(_unquote(inline))
                continue
            in_paths = True
            continue

        if re.match(r"^\s*#", line):
            continue  # a comment never ends the list, at any indentation
        if re.match(r"^\s*-\s*", line):
            item = _unquote(_strip_comment(re.sub(r"^\s*-\s*", "", line)))
            if item:
                globs.append(item)
        elif re.match(r"^\S[^:]*:", line):
            in_paths = False  # only a real top-level key ends the list

    if not saw_paths_key:
        return None  # frontmatter without a paths: key — unscoped
    if not globs:
        raise MalformedRule("'paths:' key present but no usable globs parsed")
    return globs


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: select_rules.py <repo-root> [changed-file...]", file=sys.stderr)
        return 2

    repo_root = Path(argv[1])
    if not repo_root.is_dir():
        print(f"select_rules.py: no such repo root: {repo_root}", file=sys.stderr)
        return 2

    if len(argv) > 2:
        raw_changed = argv[2:]
    elif sys.stdin.isatty():
        print("usage: select_rules.py <repo-root> [changed-file...]", file=sys.stderr)
        return 2
    else:
        raw_changed = list(sys.stdin)

    try:
        changed = _normalize_changed(raw_changed, repo_root)
    except UsageError as exc:
        # Legit business flow: a caller mistake is normal CLI usage, not a crash.
        # Surfaced on stderr with exit 2 — the caller's contract for "you passed
        # something wrong", distinct from exit 0's "nothing matched".
        print(f"select_rules.py: {exc}", file=sys.stderr)
        return 2

    if not changed:
        print("select_rules.py: no changed files given", file=sys.stderr)
        return 2

    rules_dir = repo_root / ".claude" / "rules"
    if not rules_dir.is_dir():
        # Legit business flow: a repo with no .claude/rules/ has no scoped rules,
        # and the repo root itself was validated above — so this is the complete
        # answer, not a swallowed bad-path error. Say so rather than exiting
        # silently, or it is indistinguishable from a root pointed at the wrong tree.
        print(f"select_rules.py: {repo_root} has no .claude/rules/", file=sys.stderr)
        return 0

    malformed: list[str] = []
    scoped_matches = 0
    for rule in sorted(rules_dir.rglob("*.md")):
        try:
            # utf-8-sig, not utf-8: a BOM left on the first line makes it read as
            # '﻿---', so the rule looks like it has no frontmatter and fails
            # open as "unscoped" — printed for every changed file.
            globs = parse_globs(rule.read_text(encoding="utf-8-sig"))
        except MalformedRule as exc:
            # Legit business flow: an unscopeable rule is a defect in that repo,
            # not an error here. It is collected into `malformed`, printed to
            # stderr, and drives exit 3 — the caller is told, not left guessing.
            malformed.append(f"{rule}: {exc}")
            continue

        if globs is None:
            print(rule)
            continue

        try:
            patterns = [glob_to_regex(p) for g in globs for p in expand_braces(g)]
        except MalformedRule as exc:
            # Legit business flow: same contract as above — an unsupported glob is
            # surfaced in `malformed` and exit 3, never silently skipped.
            malformed.append(f"{rule}: {exc}")
            continue

        if any(pattern.match(c) for pattern in patterns for c in changed):
            print(rule)
            scoped_matches += 1

    if scoped_matches == 0:
        print(
            "select_rules.py: no path-scoped rule matched any changed file. That is correct if "
            "the diff touches only unscoped areas — otherwise check the changed paths are "
            "repo-relative, as `git -C <repo> diff --name-only` prints them.",
            file=sys.stderr,
        )

    if malformed:
        print(
            f"select_rules.py: {len(malformed)} malformed rule file(s) — "
            "scoping cannot be trusted, report these rather than ignoring them:",
            file=sys.stderr,
        )
        for entry in malformed:
            print(f"  {entry}", file=sys.stderr)
        return 3

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
