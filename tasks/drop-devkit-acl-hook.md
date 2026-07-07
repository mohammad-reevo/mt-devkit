---
name: drop-devkit-acl-hook
title: Drop the devkit acl-hook dependency in favor of native Claude Code permissions
target: personal-claude
created: 2026-07-07
source: Wave 2b devkit hooks sweep (my-devkit-design.md)
---

## Problem
I currently run devkit's `acl-hook` plugin (a `PreToolUse:Bash|Monitor` gate that splits
compound commands part-by-part and checks each against an allow/ask/deny config), patched by my
personal `~/.claude/hooks/patch_acl_default.sh` (`SessionStart`) which flips the unknown-command
default from "ask" to "allow" so it stops prompting me constantly. That's a **live devkit
dependency** — one of the last two surfaced by the Wave 2b sweep (the other: the babysit-pr
plugin's nudge, already neutralized via `BABYSIT_PR_AUTONUDGE=0`).

## Why it matters
Moving off devkit means retiring this. Decision (2026-07-07): **drop rather than rebuild** —
Claude Code's native `settings.json` allow/deny/ask permissions are enough for a solo, trusted
personal harness, and dropping fits the "guidance over gates" philosophy. The only thing lost is
compound-command part-by-part vetting (native matches the whole command string), which I don't
need day-to-day. Can always rebuild a personal `mt-acl` hook later if I ever want that granularity.

## Fix ideas
- Stop loading devkit's `acl-hook` plugin for my sessions; remove/neutralize
  `~/.claude/hooks/patch_acl_default.sh` (it only exists to patch that plugin).
- Confirm native `~/.claude/settings.json` permissions cover the everyday command set so dropping
  the ACL gate doesn't reintroduce constant prompts — add allow-rules as needed.
- Verify nothing else references the acl-hook config.
- (Only if part-vetting is ever wanted) rebuild as a self-contained personal `mt-acl` hook.

## Links
- [[my-devkit-design]] Wave 2b sweep — acl hook.
- Hook: `~/.claude/hooks/patch_acl_default.sh`.
